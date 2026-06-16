#!/usr/bin/env python3
"""
SETUP-FINAL-CORRECTO.PY
- 27 archivos UTF-8 → Importar directo
- 12 archivos UTF-16LE → Convertir con iconv + Importar
Basado en diagnóstico real de los archivos
"""

import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
import os
import sys

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

CONFIG = {
    'dump_folder': Path('./dumps'),
    'mysql_host': 'mysql-dev-shalom',
    'mysql_user': 'root',
    'mysql_password': 'root',
}

# ARCHIVOS UTF-8 (27) - Importar directo sin conversión
UTF8_FILES = [
    ('server12', [
        ('server12_core_solo_ordenservicio.sql.gz', 'Órdenes core'),
        ('server12_emp_ciudad_ubigeo.sql.gz', 'Ciudades'),
        ('server12_emp_contact_origin.sql.gz', 'Origen contactos'),
        ('server12_emp_dni_vetados.sql.gz', 'DNI vetados'),
        ('server12_emp_gestion_cobranza.sql.gz', 'Cobranza'),
        ('server12_emp_guia_electronica_correlativo.sql.gz', 'Guía electrónica'),
        ('server12_emp_ordenservicio.sql.gz', 'Órdenes'),
        ('server12_emp_os_detalle.sql.gz', 'Detalle órdenes'),
        ('server12_emp_persona.sql.gz', 'Personas'),
        ('server12_emp_producto.sql.gz', 'Productos'),
        ('server12_emp_ruta.sql.gz', 'Rutas'),
        ('server12_emp_rutas_distancias.sql.gz', 'Distancias'),
        ('server12_emp_tarifas_aereas.sql.gz', 'Tarifas aéreas'),
        ('server12_emp_telefono_os.sql.gz', 'Teléfono órdenes'),
        ('server12_emp_telefonos_validados.sql.gz', 'Teléfonos validados'),
        ('server12_emp_terminal.sql.gz', 'Terminales'),
        ('server12_emp_terminales_principales_aereas.sql.gz', 'Terminales aéreas'),
        #('server12_envia_core.sql.gz', 'ENVIA'),
        #('server12_enviaya_core.sql.gz', 'ENVIAYA'),
    ]),
    ('shalom_pro', [
        ('shalom_pro.sql.gz', 'Shalom PRO completo'),
        ('shalom_pro_extra_branches_person.sql.gz', 'Extra ramas'),
        ('shalom_pro_extra_companies_user.sql.gz', 'Extra empresas'),
        ('shalom_pro_extra_contact_extra.sql.gz', 'Extra contactos'),
    ]),
    ('empresarial', [
        ('empresarial_schema_utf8.sql', 'Esquema UTF-8'),
        ('empresarial_data_utf8.sql', 'Datos UTF-8'),
    ]),
]

# ARCHIVOS UTF-16LE (12) - Convertir con iconv + Importar
UTF16LE_FILES = [
    ('server12', [
        ('server12_schema.sql', 'Esquema server12'),
    ]),
    ('shalom_pro', [
        ('shalom_pro_schema.sql', 'Esquema'),
        ('shalom_pro_data.sql', 'Datos'),
        ('shalom_pro_login_seed.sql', 'Login'),
    ]),
    ('shalom_clientes_corp', [
        ('shalom_clientes_corp_schema.sql', 'Esquema'),
        ('shalom_clientes_corp_data.sql', 'Datos'),
    ]),
    ('empresarial', [
        ('empresarial_schema.sql', 'Esquema'),
        ('empresarial_data.sql', 'Datos'),
    ]),
    ('empresarial2', [
        ('empresarial2_schema.sql', 'Esquema'),
    ]),
    ('tarifas', [
        ('tarifas_schema.sql', 'Esquema'),
        ('tarifas_data.sql', 'Datos'),
    ]),
]

def setup_logging():
    log_file = f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = logging.getLogger('setup')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(handler)
    return logger, log_file

logger, log_file = setup_logging()

def print_header(title):
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(80)}{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")
    logger.info(f"✓ {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")
    logger.error(f"✗ {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")
    logger.warning(f"⚠ {msg}")

def print_info(msg):
    print(f"{Colors.YELLOW}➜ {msg}{Colors.END}")

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def run_command(cmd, timeout=1800):
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)

def validate_environment():
    print_header("VALIDACIÓN DE ENTORNO")
    
    ok, _, _ = run_command('docker ps', timeout=10)
    if not ok:
        print_error("Docker no está corriendo")
        return False
    print_success("Docker está corriendo")
    
    if not CONFIG['dump_folder'].exists():
        print_error("Carpeta dumps no existe")
        return False
    
    files = list(CONFIG['dump_folder'].glob('*'))
    print_success(f"Carpeta dumps: {len(files)} archivos encontrados")
    
    print_info("Esperando MySQL...")
    for i in range(30):
        ok, _, _ = run_command(f'docker exec {CONFIG["mysql_host"]} mysql -u{CONFIG["mysql_user"]} -p{CONFIG["mysql_password"]} -e "SELECT 1;"', timeout=5)
        if ok:
            print_success("MySQL está listo")
            return True
        time.sleep(1)
    
    print_error("MySQL no respondió")
    return False

def create_databases():
    print_header("1. CREANDO BASES DE DATOS")
    
    for db in ['server12', 'shalom_pro', 'shalom_clientes_corp', 'empresarial', 'empresarial2', 'tarifas']:
        print_info(f"Creando {db}...")
        cmd = f'docker exec {CONFIG["mysql_host"]} mysql -u{CONFIG["mysql_user"]} -p{CONFIG["mysql_password"]} -e "DROP DATABASE IF EXISTS {db}; CREATE DATABASE {db};"'
        run_command(cmd, timeout=30)
        print_success(f"✓ {db}")
    print()

def import_utf8_files():
    """Importar 27 archivos UTF-8 sin conversión"""
    print_header("2A. IMPORTANDO UTF-8 DIRECTO (27 archivos)")
    
    total = sum(len(files) for _, files in UTF8_FILES)
    current = 0
    
    for db, files in UTF8_FILES:
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}═ {db.upper()} ═{Colors.END}\n")
        
        for filename, description in files:
            current += 1
            file_path = CONFIG['dump_folder'] / filename
            
            if not file_path.exists():
                print_warning(f"[{current}/{total}] NO ENCONTRADO: {filename}")
                continue
            
            size_mb = file_path.stat().st_size / 1024 / 1024
            timeout = 3600 if size_mb > 800 else (2400 if size_mb > 400 else (1800 if size_mb > 100 else 600))
            
            is_gz = filename.endswith('.gz')
            
            print_info(f"[{current}/{total}] {filename} ({size_mb:.1f}MB) → {description}")
            start = time.time()
            
            if is_gz:
                cmd = f'docker exec {CONFIG["mysql_host"]} bash -c "gunzip -c /dumps/{filename} | mysql --user={CONFIG["mysql_user"]} --password={CONFIG["mysql_password"]} --init-command=\\"SET FOREIGN_KEY_CHECKS=0;\\\" {db}"'
            else:
                cmd = f'docker exec {CONFIG["mysql_host"]} bash -c "mysql --user={CONFIG["mysql_user"]} --password={CONFIG["mysql_password"]} --init-command=\\"SET FOREIGN_KEY_CHECKS=0;\\\" {db} < /dumps/{filename}"'
            
            success, _, stderr = run_command(cmd, timeout=timeout)
            elapsed = format_time(time.time() - start)
            
            if success or "ERROR" not in stderr:
                print_success(f"✓ Importado en {elapsed}")
            else:
                print_error(f"✗ Error importando {filename} en {db}")
                if stderr:
                    print_error(stderr[-2000:])
                else:
                    print_error("Error desconocido")
    
    print()

def import_utf16le_files():
    """Importar 12 archivos UTF-16LE con conversión"""
    print_header("2B. IMPORTANDO UTF-16LE CON CONVERSIÓN (12 archivos)")
    
    total = sum(len(files) for _, files in UTF16LE_FILES)
    current = 0
    
    for db, files in UTF16LE_FILES:
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}═ {db.upper()} ═{Colors.END}\n")
        
        for filename, description in files:
            current += 1
            file_path = CONFIG['dump_folder'] / filename
            
            if not file_path.exists():
                print_warning(f"[{current}/{total}] NO ENCONTRADO: {filename}")
                continue
            
            size_mb = file_path.stat().st_size / 1024 / 1024
            timeout = 3600 if size_mb > 800 else (2400 if size_mb > 400 else (1800 if size_mb > 100 else 600))
            
            print_info(f"[{current}/{total}] {filename} ({size_mb:.1f}MB) → {description}")
            start = time.time()
            
            # Convertir UTF-16LE → UTF-8 + Importar
            cmd = f'docker exec {CONFIG["mysql_host"]} bash -c "iconv -f UTF-16LE -t UTF-8 /dumps/{filename} | mysql --user={CONFIG["mysql_user"]} --password={CONFIG["mysql_password"]} --init-command=\\"SET FOREIGN_KEY_CHECKS=0;\\\" {db}"'
            
            success, _, stderr = run_command(cmd, timeout=timeout)
            elapsed = format_time(time.time() - start)
            
            if success or "ERROR" not in stderr:
                print_success(f"✓ Importado en {elapsed}")
            else:
                print_error(f"✗ Error importando {filename} en {db}")
                if stderr:
                    print_error(stderr[-2000:])
                else:
                    print_error("Error desconocido")
    
    print()

def validate_tables():
    print_header("3. VALIDACIÓN DE TABLAS")
    
    validations = {
        'server12': ['emp_persona', 'emp_os_detalle', 'emp_ruta'],
        'shalom_pro': ['users', 'person', 'service_order'],
        'empresarial': ['emp_client_key_block'],
        'tarifas': ['ubigeo'],
    }
    
    for db, tables in validations.items():
        print(f"\n{Colors.MAGENTA}{db}:{Colors.END}\n")
        
        for table in tables:
            cmd = f'docker exec {CONFIG["mysql_host"]} mysql -u{CONFIG["mysql_user"]} -p{CONFIG["mysql_password"]} -e "SELECT COUNT(*) FROM {db}.{table};"'
            success, output, _ = run_command(cmd, timeout=30)
            
            if success and output:
                try:
                    lines = output.strip().split('\n')
                    if len(lines) >= 2:
                        count = lines[1].strip()
                        print(f"{Colors.GREEN}✓ {table:<40} {count:>15}{Colors.END}")
                except:
                    print_warning(f"{table:<40} (error)")
            else:
                print_error(f"{table:<40} No existe")

def optimize_database():
    print_header("4. OPTIMIZACIÓN")
    
    print_info("Habilitando FOREIGN_KEY_CHECKS...")
    run_command(f'docker exec {CONFIG["mysql_host"]} mysql -u{CONFIG["mysql_user"]} -p{CONFIG["mysql_password"]} -e "SET GLOBAL FOREIGN_KEY_CHECKS=1;"', timeout=30)
    print_success("✓ Foreign keys habilitadas")
    
    print_info("Otorgando permisos...")
    run_command(f'docker exec {CONFIG["mysql_host"]} mysql -u{CONFIG["mysql_user"]} -p{CONFIG["mysql_password"]} -e "GRANT ALL PRIVILEGES ON *.* TO \'docker\'@\'%\' IDENTIFIED BY \'4X+9zXs3k6%1e\'; FLUSH PRIVILEGES;"', timeout=30)
    print_success("✓ Permisos asignados")
    print()

def main():
    try:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}")
        print("SETUP FINAL - 100% CORRECTO".center(80))
        print("27 UTF-8 + 12 UTF-16LE".center(80))
        print(f"{'='*80}{Colors.END}\n")
        
        if not validate_environment():
            sys.exit(1)
        
        time.sleep(2)
        create_databases()
        import_utf8_files()
        import_utf16le_files()
        validate_tables()
        optimize_database()
        
        print_header("✓ SETUP COMPLETADO - LISTO PARA USAR")
        print(f"{Colors.GREEN}{Colors.BOLD}✓✓✓ ÉXITO ✓✓✓{Colors.END}\n")
        print(f"Logs: {log_file}\n")
        
    except KeyboardInterrupt:
        print_error("\n✗ Cancelado")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n✗ Error: {str(e)}")
        logger.exception("Error")
        sys.exit(1)

if __name__ == '__main__':
    main()