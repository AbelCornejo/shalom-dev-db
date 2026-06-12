#!/usr/bin/env python3
"""
Script para validar la importación de dumps
Muestra qué tablas se importaron, cuáles están vacías, y cuáles faltan
"""

import subprocess
import sys
from pathlib import Path
from collections import defaultdict

# Colores ANSI
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

CONFIG = {
    'mysql_host': 'mysql-dev-shalom',
    'mysql_user': 'root',
    'mysql_password': 'root',
    'databases': ['server12', 'shalom_pro', 'shalom_clientes_corp', 'empresarial', 'empresarial2', 'tarifas'],
}

def print_header(title):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def run_mysql_query(database, query):
    """Ejecuta una query MySQL y retorna el resultado"""
    try:
        cmd = [
            'docker', 'exec', CONFIG['mysql_host'], 'mysql',
            f"-u{CONFIG['mysql_user']}", f"-p{CONFIG['mysql_password']}",
            '-N', '-e',  # -N: sin headers, -e: execute
            query
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def get_tables_in_database(database):
    """Obtiene todas las tablas de una BD"""
    query = f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{database}';"
    success, output = run_mysql_query(database, query)
    if success and output:
        return [line.strip() for line in output.split('\n') if line.strip()]
    return []

def get_table_row_count(database, table):
    """Cuenta las filas en una tabla"""
    query = f"SELECT COUNT(*) FROM {database}.{table};"
    success, output = run_mysql_query(database, query)
    if success:
        try:
            return int(output.strip())
        except:
            return -1
    return -1

def validate_database(database):
    """Valida una base de datos completa"""
    print_header(f"VALIDANDO BASE DE DATOS: {database.upper()}")
    
    tables = get_tables_in_database(database)
    
    if not tables:
        print_error(f"No hay tablas en {database}")
        return {'total': 0, 'empty': 0, 'with_data': 0, 'tables': []}
    
    print(f"{Colors.CYAN}Total de tablas: {len(tables)}{Colors.END}\n")
    
    stats = {
        'total': len(tables),
        'empty': 0,
        'with_data': 0,
        'tables': []
    }
    
    # Tablas con datos
    print(f"{Colors.BOLD}TABLAS CON DATOS:{Colors.END}")
    with_data = []
    
    for table in sorted(tables):
        count = get_table_row_count(database, table)
        if count > 0:
            with_data.append((table, count))
            stats['with_data'] += 1
    
    if with_data:
        for table, count in with_data:
            print(f"  {Colors.GREEN}✓{Colors.END} {table:<40} {count:>10,} filas")
    else:
        print(f"  {Colors.YELLOW}(ninguna){Colors.END}")
    
    # Tablas vacías
    print(f"\n{Colors.BOLD}TABLAS VACÍAS:{Colors.END}")
    empty = []
    
    for table in sorted(tables):
        count = get_table_row_count(database, table)
        if count == 0:
            empty.append(table)
            stats['empty'] += 1
    
    if empty:
        for table in empty:
            print(f"  {Colors.YELLOW}⚠{Colors.END} {table:<40} 0 filas")
    else:
        print(f"  {Colors.GREEN}(ninguna){Colors.END}")
    
    # Resumen
    print(f"\n{Colors.BOLD}RESUMEN:{Colors.END}")
    print(f"  Tablas totales:  {stats['total']}")
    print(f"  Con datos:       {stats['with_data']} ({(stats['with_data']/stats['total']*100):.1f}%)")
    print(f"  Vacías:          {stats['empty']} ({(stats['empty']/stats['total']*100):.1f}%)")
    
    stats['tables'] = [(t, get_table_row_count(database, t)) for t in tables]
    
    return stats

def check_critical_tables():
    """Verifica tablas críticas para el login"""
    print_header("VALIDANDO TABLAS CRÍTICAS")
    
    critical = {
        'shalom_pro': ['users', 'person', 'service_order', 'detail_my_company'],
        'server12': ['emp_persona', 'emp_ordenservicio', 'emp_os_detalle'],
        'empresarial': ['emp_client_key_block'],
    }
    
    for db, tables in critical.items():
        print(f"{Colors.BOLD}{db}:{Colors.END}")
        for table in tables:
            count = get_table_row_count(db, table)
            if count > 0:
                print(f"  {Colors.GREEN}✓{Colors.END} {table:<30} {count:>10,} filas")
            elif count == 0:
                print(f"  {Colors.RED}✗{Colors.END} {table:<30} {'VACÍA':>10}")
            else:
                print(f"  {Colors.RED}✗{Colors.END} {table:<30} {'NO EXISTE':>10}")

def main():
    try:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}VALIDACION DE IMPORTACION DE DUMPS{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        # Verificar Docker
        try:
            subprocess.run(['docker', 'ps'], capture_output=True, check=True)
        except:
            print_error("Docker no está corriendo")
            sys.exit(1)
        
        # Validar cada BD
        all_stats = {}
        for db in CONFIG['databases']:
            stats = validate_database(db)
            all_stats[db] = stats
        
        # Validar tablas críticas
        check_critical_tables()
        
        # Resumen general
        print_header("RESUMEN GENERAL")
        
        total_tables = sum(s['total'] for s in all_stats.values())
        total_with_data = sum(s['with_data'] for s in all_stats.values())
        total_empty = sum(s['empty'] for s in all_stats.values())
        
        print(f"{Colors.BOLD}Across all databases:{Colors.END}")
        print(f"  Tablas totales:  {total_tables}")
        print(f"  Con datos:       {total_with_data} ({(total_with_data/total_tables*100):.1f}%)")
        print(f"  Vacías:          {total_empty} ({(total_empty/total_tables*100):.1f}%)")
        
        print(f"\n{Colors.BOLD}Por base de datos:{Colors.END}")
        for db in CONFIG['databases']:
            stats = all_stats[db]
            if stats['total'] > 0:
                pct = (stats['with_data']/stats['total']*100)
                status = Colors.GREEN + "✓" + Colors.END if pct == 100 else Colors.YELLOW + "⚠" + Colors.END
                print(f"  {status} {db:<20} {stats['with_data']:>3}/{stats['total']:<3} tablas ({pct:>5.1f}%)")
            else:
                print(f"  {Colors.RED}✗{Colors.END} {db:<20} {'SIN TABLAS':>15}")
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}\n")
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()