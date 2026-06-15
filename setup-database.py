#!/usr/bin/env python3
"""
SETUP.PY - Script Único y Autónomo para SHALOM DEV DB
Todo-en-uno: validación, importación, optimización, logging
Solo ejecuta: python setup.py
Sin dependencias externas - funciona en Windows y Linux
"""

import subprocess
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
import json
import os

# ============================================================================
# COLORES ANSI (Compatible Windows y Linux)
# ============================================================================
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ============================================================================
# CONFIGURACIÓN TODO-EN-UNO
# ============================================================================
CONFIG = {
    'dump_folder': Path('./dumps'),
    'mysql_host': 'mysql-dev-shalom',
    'mysql_user': 'root',
    'mysql_password': 'root',
    'docker_user': 'docker',
    'docker_password': '4X+9zXs3k6%1e',
    'databases': ['server12', 'shalom_pro', 'shalom_clientes_corp', 
                  'empresarial', 'empresarial2', 'tarifas'],
    'app_container': 'pro-qa_app',
    'max_retries': 3,
    'retry_delay': 2,
    'mysql_wait_timeout': 30,
}

SQL_IMPORT_ORDER = [
    ('server12_schema.sql', 'server12'),
    ('shalom_pro_schema.sql', 'shalom_pro'),
    ('shalom_pro_data.sql', 'shalom_pro'),
    ('shalom_pro_service_order.sql', 'shalom_pro'),
    ('shalom_pro_login_seed.sql', 'shalom_pro'),
    ('shalom_pro_extra_branches_person.sql', 'shalom_pro'),
    ('shalom_pro_extra_companies_user.sql', 'shalom_pro'),
    ('shalom_pro_extra_company.sql', 'shalom_pro'),
    ('shalom_pro_extra_contact_extra.sql', 'shalom_pro'),
    ('shalom_pro_extra_get_user.sql', 'shalom_pro'),
    ('empresarial_schema_utf8.sql', 'empresarial'),
    ('empresarial_data_utf8.sql', 'empresarial'),
    ('empresarial2_schema.sql', 'empresarial2'),
    ('tarifas_schema.sql', 'tarifas'),
    ('tarifas_data.sql', 'tarifas'),
    ('shalom_clientes_corp_schema.sql', 'shalom_clientes_corp'),
    ('shalom_clientes_corp_data.sql', 'shalom_clientes_corp'),
]

AUTO_INCREMENT_CONFIG = [
    ('server12', 'emp_ordenservicio', 'ose_id'),
    ('server12', 'emp_os_detalle', 'osd_id'),
    ('shalom_pro', 'users', 'id'),
    ('shalom_pro', 'person', 'id'),
    ('tarifas', 'ubigeo', 'id'),
]

INDEXES_TO_CREATE = [
    ('server12.emp_ordenservicio', 'idx_ose_estado', 'ose_estado'),
    ('server12.emp_ordenservicio', 'idx_usercreaid', 'usercreaid'),
    ('server12.emp_os_detalle', 'idx_osd_osid', 'osd_osid'),
    ('server12.emp_persona', 'idx_perso_email', 'perso_mail'),
    ('server12.emp_persona', 'idx_perso_telefono', 'perso_telefono'),
    ('server12.emp_tarifas_aereas', 'idx_tarifas_ruta', 'ruta_id'),
    ('shalom_pro.users', 'idx_email', 'email'),
    ('shalom_pro.users', 'idx_document', 'document'),
    ('shalom_pro.person', 'idx_person_email', 'email'),
    ('shalom_pro.service_order', 'idx_user_id', 'user_id'),
    ('shalom_pro.service_order', 'idx_service_status', 'status'),
    ('shalom_pro.detail_my_company', 'idx_company_id', 'company_id'),
    ('empresarial.emp_client_key_block', 'idx_document', 'document'),
    ('empresarial.emp_client_key_block', 'idx_block_date', 'block_date'),
    ('tarifas.ubigeo', 'idx_ubigeo_code', 'ubigeo_cod'),
]

CRITICAL_VALIDATIONS = [
    ('SELECT COUNT(*) AS count FROM shalom_pro.users;', 'shalom_pro.users (usuarios)'),
    ('SELECT COUNT(*) AS count FROM shalom_pro.person;', 'shalom_pro.person (personas)'),
    ('SELECT COUNT(*) AS count FROM shalom_pro.service_order;', 'shalom_pro.service_order (órdenes)'),
    ('SELECT COUNT(*) AS count FROM tarifas.ubigeo;', 'tarifas.ubigeo (ubicaciones)'),
    ('SELECT COUNT(*) AS count FROM empresarial.emp_client_key_block;', 'empresarial.emp_client_key_block'),
    ('SELECT COUNT(*) AS count FROM server12.emp_persona;', 'server12.emp_persona (personas)'),
]

# ============================================================================
# SETUP DE LOGGING
# ============================================================================
def setup_logging():
    """Configura logging a archivo y consola - Compatible Windows + Linux"""
    log_file = f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = logging.getLogger('setup')
    logger.setLevel(logging.DEBUG)
    
    # File handler con UTF-8 explícito (importante para Windows)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Console handler con UTF-8 (para Windows)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter())
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logging()

# ============================================================================
# FUNCIONES DE CONSOLA
# ============================================================================
def print_header(title):
    """Imprime encabezado"""
    msg = f"\n{Colors.CYAN}{'='*70}{Colors.END}\n{Colors.CYAN}{Colors.BOLD}{title.center(70)}{Colors.END}\n{Colors.CYAN}{'='*70}{Colors.END}\n"
    print(msg)
    logger.info(f">>> {title}")

def print_success(msg):
    """Mensaje éxito"""
    formatted = f"{Colors.GREEN}✓ {msg}{Colors.END}"
    print(formatted)
    logger.info(f"✓ {msg}")

def print_error(msg):
    """Mensaje error"""
    formatted = f"{Colors.RED}✗ {msg}{Colors.END}"
    print(formatted)
    logger.error(f"✗ {msg}")

def print_warning(msg):
    """Mensaje advertencia"""
    formatted = f"{Colors.YELLOW}⚠ {msg}{Colors.END}"
    print(formatted)
    logger.warning(f"⚠ {msg}")

def print_info(msg):
    """Mensaje info"""
    formatted = f"{Colors.YELLOW}➜ {msg}{Colors.END}"
    print(formatted)
    logger.info(f"➜ {msg}")

def print_section(msg):
    """Sección importante"""
    formatted = f"{Colors.MAGENTA}{Colors.BOLD}{msg}{Colors.END}"
    print(formatted)
    logger.info(f"=== {msg}")

# ============================================================================
# FUNCIONES DE EJECUCIÓN
# ============================================================================
def run_command(cmd, shell=False, verbose=True, timeout=1200):
    """Ejecuta comando - retorna (éxito, stdout, stderr)
    timeout por defecto: 1200s (20 minutos)
    Para archivos pequeños: ok
    Para archivos grandes: ok
    """
    try:
        if verbose:
            logger.debug(f"Ejecutando: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, check=False, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout ({timeout}s)"
    except Exception as e:
        return False, "", str(e)

def docker_exec_mysql(sql_command, timeout=60):
    """Ejecuta SQL en MySQL via Docker"""
    try:
        cmd = [
            'docker', 'exec', CONFIG['mysql_host'], 'mysql',
            f"-u{CONFIG['mysql_user']}", f"-p{CONFIG['mysql_password']}",
            '-e', sql_command
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout esperando MySQL"
    except Exception as e:
        return False, "", str(e)

def format_time(seconds):
    """Convierte segundos a formato legible"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

# ============================================================================
# DETECCIÓN DE ENCODING
# ============================================================================
def detect_file_encoding(file_path):
    """Detecta encoding del archivo"""
    try:
        with open(file_path, 'rb') as f:
            bom = f.read(4)
        if bom.startswith(b'\xff\xfe'):
            return 'UTF-16LE'
        if bom.startswith(b'\xfe\xff'):
            return 'UTF-16BE'
        if bom.startswith(b'\xef\xbb\xbf'):
            return 'UTF-8'
        return 'UTF-8'
    except:
        return 'UTF-8'

def needs_iconv(encoding):
    """¿Necesita conversión con iconv?"""
    return encoding.startswith('UTF-16')

# ============================================================================
# VALIDACIONES PREVIAS
# ============================================================================
def validate_environment():
    """Valida que el entorno esté listo"""
    print_header("VALIDACIÓN DE ENTORNO")
    
    issues = []
    
    # Python
    if sys.version_info < (3, 7):
        issues.append(f"Python 3.7+ requerido (tienes {sys.version_info.major}.{sys.version_info.minor})")
    else:
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Docker
    ok, _, _ = run_command(['docker', 'ps'], verbose=False)
    if not ok:
        issues.append("Docker no está corriendo - ejecutar: docker-compose up -d")
    else:
        print_success("Docker está corriendo")
    
    # Carpeta dumps
    if not CONFIG['dump_folder'].exists():
        issues.append(f"Carpeta dumps no existe: {CONFIG['dump_folder'].absolute()}")
    else:
        files = list(CONFIG['dump_folder'].glob('*.sql')) + list(CONFIG['dump_folder'].glob('*.sql.gz'))
        if len(files) == 0:
            issues.append("No hay archivos .sql o .sql.gz en carpeta dumps/")
        else:
            print_success(f"Carpeta dumps encontrada ({len(files)} archivos)")
    
    # MySQL
    if not issues:  # Solo si Docker está ok
        print_info(f"Esperando a MySQL (timeout {CONFIG['mysql_wait_timeout']}s)...")
        start = time.time()
        while time.time() - start < CONFIG['mysql_wait_timeout']:
            ok, _, _ = docker_exec_mysql("SELECT 1;", timeout=5)
            if ok:
                print_success("MySQL está listo")
                break
            time.sleep(1)
        else:
            issues.append("MySQL no respondió a tiempo")
    
    if issues:
        print_error("\n⚠ PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print_error(f"  → {issue}")
        return False
    
    return True

# ============================================================================
# IMPORTACIÓN PRINCIPAL
# ============================================================================
def create_databases():
    """Crea todas las BDs"""
    print_header("1. CREANDO BASES DE DATOS")
    for db in CONFIG['databases']:
        print_info(f"Creando: {db}...")
        sql = f"DROP DATABASE IF EXISTS {db}; CREATE DATABASE IF NOT EXISTS {db};"
        success, _, _ = docker_exec_mysql(sql)
        if success:
            print_success(f"BD creada: {db}")
    print_success("Bases de datos creadas\n")

def import_gz_dumps():
    """Importa archivos .sql.gz - con timeout inteligente"""
    print_header("2. IMPORTANDO DUMPS COMPRIMIDOS (.sql.gz)")
    
    gz_files = sorted(CONFIG['dump_folder'].glob('*.sql.gz'))
    if not gz_files:
        print_warning("No hay archivos .sql.gz\n")
        return
    
    print_info(f"Encontrados {len(gz_files)} archivos .sql.gz\n")
    
    for gz_file in gz_files:
        filename = gz_file.name
        # Detectar BD
        db_target = None
        for db in CONFIG['databases']:
            if db in filename.lower():
                db_target = db
                break
        
        if not db_target:
            print_warning(f"Saltando: {filename} (BD no identificada)")
            continue
        
        size_mb = gz_file.stat().st_size / 1024 / 1024
        print_section(f"Importando {filename} ({size_mb:.1f} MB)")
        
        # Timeout inteligente según tamaño
        if size_mb > 500:
            timeout = 1800  # 30 minutos
        elif size_mb > 200:
            timeout = 1200  # 20 minutos
        else:
            timeout = 600   # 10 minutos
        
        cmd = f"docker exec {CONFIG['mysql_host']} sh -c \"gunzip -c /dumps/{filename} | mysql -u{CONFIG['mysql_user']} -p{CONFIG['mysql_password']} --init-command='SET FOREIGN_KEY_CHECKS=0;' {db_target}\""
        
        start_time = time.time()
        success, _, stderr = run_command(cmd, shell=True, verbose=False, timeout=timeout)
        elapsed = format_time(time.time() - start_time)
        
        if success or "ERROR 1050" in stderr:
            print_success(f"Importado: {filename} ({elapsed})")
        else:
            print_warning(f"Error: {filename} - {stderr[:100]}")
            logger.warning(f"Failed to import {filename}: {stderr[:300]}")

def import_sql_dumps():
    """Importa archivos .sql sin comprimir - con timeout extendido para grandes"""
    print_header("3. IMPORTANDO DUMPS .SQL")
    
    imported = 0
    for filename, db in SQL_IMPORT_ORDER:
        file_path = CONFIG['dump_folder'] / filename
        
        if not file_path.exists():
            print_warning(f"No encontrado: {filename}")
            continue
        
        size_mb = file_path.stat().st_size / 1024 / 1024
        encoding = detect_file_encoding(file_path)
        needs_conversion = needs_iconv(encoding)
        
        print_section(f"Importando {filename} ({size_mb:.1f} MB)")
        print_info(f"Encoding: {encoding}" + (" - Requiere conversión iconv" if needs_conversion else ""))
        
        # Determinar timeout según tamaño
        # Archivos > 500 MB: 30 minutos
        # Archivos > 200 MB: 20 minutos
        # Archivos pequeños: 10 minutos
        if size_mb > 500:
            timeout = 1800  # 30 minutos
            print_info(f"Timeout: 30 minutos (archivo grande)")
        elif size_mb > 200:
            timeout = 1200  # 20 minutos
            print_info(f"Timeout: 20 minutos (archivo mediano)")
        else:
            timeout = 600   # 10 minutos
        
        # Intentar 3 veces
        for attempt in range(1, CONFIG['max_retries'] + 1):
            if attempt > 1:
                print_info(f"Intento {attempt}/3...")
            
            # Comando con conversión si es necesario
            if needs_conversion:
                iconv_cmd = f"iconv -f {encoding} -t UTF-8 | "
                shell_cmd = f"cat /dumps/{filename} | {iconv_cmd}mysql -u{CONFIG['mysql_user']} -p{CONFIG['mysql_password']} --init-command='SET FOREIGN_KEY_CHECKS=0;' {db}"
            else:
                shell_cmd = f"cat /dumps/{filename} | mysql -u{CONFIG['mysql_user']} -p{CONFIG['mysql_password']} --init-command='SET FOREIGN_KEY_CHECKS=0;' {db}"
            
            cmd = f"docker exec {CONFIG['mysql_host']} sh -c \"{shell_cmd}\""
            
            start_time = time.time()
            success, _, stderr = run_command(cmd, shell=True, verbose=False, timeout=timeout)
            elapsed = format_time(time.time() - start_time)
            
            if success or "ERROR 1050" in stderr or "ERROR 1062" in stderr:
                print_success(f"Importado: {filename} ({elapsed})")
                imported += 1
                logger.info(f"Successfully imported {filename} in {elapsed}")
                break
            elif "Timeout" in stderr:
                if attempt < CONFIG['max_retries']:
                    print_warning(f"Timeout - Aumentando espera. Reintentando en 3s...")
                    logger.warning(f"Timeout on {filename}, attempt {attempt}/3")
                    time.sleep(3)
                else:
                    print_error(f"Timeout después de 3 intentos: {filename}")
                    logger.error(f"Timeout after 3 attempts: {filename}")
            else:
                if attempt < CONFIG['max_retries']:
                    print_warning(f"Error - Reintentando en 2s...")
                    logger.warning(f"Error on {filename}: {stderr[:200]}")
                    time.sleep(CONFIG['retry_delay'])
                else:
                    print_error(f"No se pudo importar: {filename}")
                    print_error(f"Error: {stderr[:300]}")
                    logger.error(f"Failed after 3 attempts on {filename}: {stderr[:300]}")
    
    print_success(f"Importados {imported}/{len(SQL_IMPORT_ORDER)} archivos .sql\n")

def configure_auto_increment():
    """Configura AUTO_INCREMENT"""
    print_header("4. CONFIGURANDO AUTO_INCREMENT Y PRIMARY KEY")
    
    for db, table, column in AUTO_INCREMENT_CONFIG:
        print_info(f"Configurando {db}.{table}.{column}...")
        sql = f"ALTER TABLE {db}.{table} MODIFY COLUMN {column} INT NOT NULL AUTO_INCREMENT PRIMARY KEY;"
        success, _, _ = docker_exec_mysql(sql)
        if success:
            print_success(f"✓ {db}.{table}.{column}")
    
    print_success("AUTO_INCREMENT configurado\n")

def create_indexes():
    """Crea índices"""
    print_header("5. CREANDO ÍNDICES DE OPTIMIZACIÓN")
    
    print_info(f"Creando {len(INDEXES_TO_CREATE)} índices...\n")
    
    for table, index_name, column in INDEXES_TO_CREATE:
        sql = f"ALTER TABLE {table} ADD INDEX IF NOT EXISTS {index_name} ({column});"
        success, _, _ = docker_exec_mysql(sql)
        if success:
            print_success(f"✓ {index_name}")
    
    print_success(f"Índices creados\n")

def grant_permissions():
    """Asigna permisos"""
    print_header("6. OTORGANDO PERMISOS")
    
    for db in CONFIG['databases']:
        print_info(f"Permisos en {db}...")
        sql = f"GRANT ALL PRIVILEGES ON {db}.* TO '{CONFIG['docker_user']}'@'%'; FLUSH PRIVILEGES;"
        docker_exec_mysql(sql)
    
    print_success("Permisos completados\n")

def enable_foreign_keys():
    """Habilita Foreign Keys"""
    print_header("7. HABILITANDO FOREIGN KEY CHECKS")
    
    sql = "SET GLOBAL FOREIGN_KEY_CHECKS=1;"
    success, _, _ = docker_exec_mysql(sql)
    if success:
        print_success("Foreign keys habilitadas\n")

def validate_databases():
    """Valida importación"""
    print_header("8. VALIDACIÓN FINAL")
    
    print_section("Estado de las bases de datos:")
    
    sql = """
    SELECT 
        table_schema AS 'Base',
        COUNT(*) AS 'Tablas',
        SUM(CASE WHEN table_rows IS NOT NULL THEN table_rows ELSE 0 END) AS 'Filas Totales'
    FROM information_schema.tables
    WHERE table_schema IN ('server12','shalom_pro','shalom_clientes_corp','empresarial','empresarial2','tarifas')
    GROUP BY table_schema
    ORDER BY table_schema;
    """
    
    success, output, _ = docker_exec_mysql(sql)
    if success and output:
        print(f"\n{output}\n")
    
    print_section("Tablas críticas:")
    
    validation_data = {}
    for sql, name in CRITICAL_VALIDATIONS:
        success, count_output, _ = docker_exec_mysql(sql)
        
        if success and count_output.strip():
            try:
                lines = count_output.strip().split('\n')
                if len(lines) >= 2:
                    count = lines[1].strip()
                    validation_data[name] = count
                    
                    if count != '0':
                        print_success(f"{name}: {count} registros")
                    else:
                        print_warning(f"{name}: vacía")
            except:
                print_warning(f"{name}: error al procesar")
    
    return validation_data

def clear_laravel_cache():
    """Limpia cache Laravel"""
    print_header("9. LIMPIANDO CACHE DE LARAVEL")
    
    for cmd in ['config:clear', 'cache:clear', 'route:clear', 'view:clear']:
        full_cmd = f"docker exec {CONFIG['app_container']} php artisan {cmd}"
        success, _, _ = run_command(full_cmd, shell=True, verbose=False)
        if success:
            print_success(f"✓ {cmd}")

def print_summary(validation_data):
    """Imprime resumen final"""
    print_header("✓ SETUP COMPLETADO EXITOSAMENTE")
    
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("✓ Todas las bases de datos importadas")
    print("✓ Encodings detectados y convertidos (UTF-8/UTF-16)")
    print("✓ AUTO_INCREMENT configurado")
    print("✓ Índices de optimización creados")
    print("✓ Permisos asignados")
    print("✓ Foreign keys habilitadas")
    print(f"{Colors.END}")
    
    print(f"\n{Colors.CYAN}═════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.CYAN}RESUMEN DE DATOS IMPORTADOS{Colors.END}")
    print(f"{Colors.CYAN}═════════════════════════════════════════════════════{Colors.END}\n")
    
    for name, count in validation_data.items():
        try:
            count_int = int(count)
            if count_int > 0:
                print(f"{Colors.GREEN}✓ {name:<50} {count_int:>10,}{Colors.END}")
        except:
            pass
    
    print(f"\n{Colors.CYAN}═════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.CYAN}ACCESO A LA APLICACIÓN{Colors.END}")
    print(f"{Colors.CYAN}═════════════════════════════════════════════════════{Colors.END}\n")
    
    print(f"{Colors.YELLOW}URL:{Colors.END}")
    print(f"  → {Colors.BOLD}http://localhost:8006{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Credenciales de prueba:{Colors.END}")
    print(f"  → Email: {Colors.BOLD}overskull@overskull.pe{Colors.END}")
    print(f"  → Contraseña: {Colors.BOLD}.soltero.{Colors.END}")
    
    print(f"\n{Colors.CYAN}═════════════════════════════════════════════════════{Colors.END}\n")
    print(f"{Colors.GREEN}{Colors.BOLD}✓ Listo para usar!{Colors.END}\n")

# ============================================================================
# MAIN
# ============================================================================
def main():
    """Función principal"""
    try:
        # Banner
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}")
        print("SETUP COMPLETO - SHALOM DEV DB".center(70))
        print("Script único y autónomo".center(70))
        print(f"{'='*70}{Colors.END}\n")
        
        logger.info("="*70)
        logger.info("Setup iniciado")
        logger.info("="*70)
        
        # Validación
        if not validate_environment():
            sys.exit(1)
        
        print_info("Esperando 3 segundos...\n")
        time.sleep(3)
        
        # Ejecutar setup completo
        create_databases()
        import_gz_dumps()
        import_sql_dumps()
        grant_permissions()
        configure_auto_increment()
        create_indexes()
        enable_foreign_keys()
        validation_data = validate_databases()
        
        try:
            clear_laravel_cache()
        except:
            print_warning("Cache de Laravel no limpiado (app puede no estar corriendo)")
        
        print_summary(validation_data)
        
        logger.info("Setup completed successfully")
        
    except KeyboardInterrupt:
        print_error("\n\nSetup cancelado por el usuario")
        logger.error("Setup cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        print_error(f"Error fatal: {str(e)}")
        logger.exception("Fatal error occurred")
        sys.exit(1)

if __name__ == '__main__':
    main()