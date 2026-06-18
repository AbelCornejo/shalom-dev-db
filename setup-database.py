#!/usr/bin/env python3
"""
SETUP DATABASE LOCAL - SHALOM DEV

Importa dumps .sql.gz generados desde phpMyAdmin:
- shalom_pro completo
- shalom_clientes_corp completo
- empresarial completo
- tarifas completo
- server12 schema + data seleccionada
- empresarial2 solo schema
"""

import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
import os
import sys

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"


class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    END = "\033[0m"
    BOLD = "\033[1m"


CONFIG = {
    "dump_folder": Path("./dumps"),
    "mysql_container": "mysql-dev-shalom",
    "mysql_user": "root",
    "mysql_password": "root",
    "app_user": "docker",
    "app_password": "4X+9zXs3k6%1e",
}

DATABASES = [
    "shalom_pro",
    "shalom_clientes_corp",
    "empresarial",
    "tarifas",
    "server12",
    "empresarial2",
]

IMPORT_PLAN = [
    {"db": "shalom_pro", "file": "shalom_pro.sql.gz", "description": "Shalom PRO completo"},
    {"db": "shalom_clientes_corp", "file": "shalom_clientes_corp.sql.gz", "description": "Clientes corp completo"},
    {"db": "empresarial", "file": "empresarial.sql.gz", "description": "Empresarial completo"},
    {"db": "tarifas", "file": "tarifas.sql.gz", "description": "Tarifas completo"},
    {"db": "server12", "file": "server12_schema.sql.gz", "description": "Server12 schema"},
    {"db": "server12", "file": "server12_data.sql.gz", "description": "Server12 data seleccionada"},
    {"db": "empresarial2", "file": "empresarial2_schema.sql.gz", "description": "Empresarial2 schema"},
]

VALIDATIONS = {
    "shalom_pro": ["users", "person", "service_order"],
    "shalom_clientes_corp": ["company", "person", "service_order"],
    "empresarial": ["emp_client_key_block"],
    "tarifas": ["tarifas", "agencias", "emp_tarifario_new"],
    "server12": ["emp_ciudad_ubigeo", "emp_terminal", "emp_ruta", "emp_ordenservicio", "emp_os_detalle", "emp_persona"],
    "empresarial2": [],
}


def setup_logging():
    log_file = f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = logging.getLogger("setup")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(handler)
    return logger, log_file


logger, log_file = setup_logging()


def print_header(title: str):
    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(80)}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 80}{Colors.END}\n")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")
    logger.info(f"✓ {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")
    logger.error(f"✗ {msg}")


def print_info(msg: str):
    print(f"{Colors.YELLOW}➜ {msg}{Colors.END}")
    logger.info(f"➜ {msg}")


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


def run_command(cmd: str, timeout: int = 1800):
    logger.debug(f"CMD: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)


def mysql_exec(sql: str, timeout: int = 300):
    # Usar stdin es más seguro en Windows para evitar problemas con comillas
    cmd = (
        f'docker exec -i {CONFIG["mysql_container"]} mysql '
        f'--user={CONFIG["mysql_user"]} '
        f'--password={CONFIG["mysql_password"]} '
        f'--max_allowed_packet=1G'
    )
    logger.debug(f"CMD: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            input=sql,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)


def validate_environment():
    print_header("VALIDACIÓN DE ENTORNO")
    ok, _, stderr = run_command("docker ps", timeout=10)
    if not ok:
        print_error("Docker no está corriendo")
        if stderr:
            print_error(stderr)
        return False
    if not CONFIG["dump_folder"].exists():
        print_error("La carpeta dumps no existe")
        return False
    missing = []
    for item in IMPORT_PLAN:
        file_path = CONFIG["dump_folder"] / item["file"]
        if not file_path.exists():
            missing.append(item["file"])
    if missing:
        print_error("Faltan dumps requeridos:")
        for f in missing:
            print_error(f" - {f}")
        return False
    print_info("Esperando MySQL local...")
    for _ in range(60):
        ok, _, _ = mysql_exec("SELECT 1;", timeout=5)
        if ok:
            print_success("MySQL local está listo")
            return True
        time.sleep(1)
    print_error("MySQL no respondió")
    return False


def validate_gzip_files():
    print_header("VALIDANDO ARCHIVOS GZIP")
    for item in IMPORT_PLAN:
        filename = item["file"]
        print_info(f"Validando {filename}...")
        cmd = f'docker exec {CONFIG["mysql_container"]} sh -c "gzip -t /dumps/{filename}"'
        ok, _, stderr = run_command(cmd, timeout=1800)
        if not ok:
            print_error(f"{filename} está corrupto o incompleto")
            if stderr:
                print_error(stderr)
            return False
        print_success(f"{filename} OK")
    return True


def create_databases():
    print_header("CREANDO BASES DE DATOS")
    for db in DATABASES:
        print_info(f"Recreando {db}...")
        sql = f"""
DROP DATABASE IF EXISTS {db};
CREATE DATABASE {db} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"""
        ok, _, stderr = mysql_exec(sql, timeout=120)
        if not ok:
            print_error(f"No se pudo crear {db}")
            if stderr:
                print_error(stderr)
            sys.exit(1)
        print_success(f"{db} creada")


def build_import_command(db: str, filename: str) -> str:
    source_cmd = (
        f"(printf '%s\n' 'SET FOREIGN_KEY_CHECKS=0;'; "
        f"gunzip -c /dumps/{filename}; "
        f"printf '%s\n' 'SET FOREIGN_KEY_CHECKS=1;')"
    )
    mysql_cmd = (
        f"MYSQL_PWD={CONFIG['mysql_password']} mysql --force "
        f"--user={CONFIG['mysql_user']} "
        f"--max_allowed_packet=1G "
        f"{db}"
    )
    return f'docker exec {CONFIG["mysql_container"]} sh -c "set -o pipefail; {source_cmd} | {mysql_cmd}"'


def import_dumps():
    print_header("IMPORTANDO DUMPS")
    total = len(IMPORT_PLAN)
    for i, item in enumerate(IMPORT_PLAN, start=1):
        db = item["db"]
        filename = item["file"]
        description = item["description"]
        file_path = CONFIG["dump_folder"] / filename
        size_mb = file_path.stat().st_size / 1024 / 1024
        if size_mb > 2000:
            timeout = 14400
        elif size_mb > 1000:
            timeout = 10800
        elif size_mb > 500:
            timeout = 7200
        elif size_mb > 100:
            timeout = 3600
        else:
            timeout = 1800
        print_info(f"[{i}/{total}] {filename} ({size_mb:.1f} MB) → {db} | {description}")
        start = time.time()
        cmd = build_import_command(db, filename)
        ok, stdout, stderr = run_command(cmd, timeout=timeout)
        elapsed = format_time(time.time() - start)
        if not ok:
            print_error(f"Error importando {filename} en {db}")
            if stdout:
                print_error(stdout[-2000:])
            if stderr:
                print_error(stderr[-4000:])
            sys.exit(1)
        print_success(f"{filename} importado en {elapsed}")


def create_app_user():
    print_header("CREANDO USUARIO LOCAL DE APP")
    u = CONFIG["app_user"]
    p = CONFIG["app_password"]
    sql = f"""
CREATE USER IF NOT EXISTS '{u}'@'%' IDENTIFIED BY '{p}';
ALTER USER '{u}'@'%' IDENTIFIED BY '{p}';
GRANT ALL PRIVILEGES ON *.* TO '{u}'@'%';
FLUSH PRIVILEGES;
"""
    ok, _, stderr = mysql_exec(sql, timeout=60)
    if not ok:
        print_error("No se pudo crear/asignar permisos al usuario de app")
        if stderr:
            print_error(stderr)
        sys.exit(1)
    print_success(f"Usuario {u} listo")


def validate_tables():
    print_header("VALIDACIÓN DE TABLAS")
    for db, tables in VALIDATIONS.items():
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}{db}{Colors.END}\n")
        if not tables:
            ok, out, err = mysql_exec(
                f"SELECT COUNT(*) AS tables_count FROM information_schema.tables WHERE table_schema='{db}';",
                timeout=30
            )
            if ok and out:
                lines = out.strip().splitlines()
                count = lines[1].strip() if len(lines) >= 2 else "0"
                print_success(f"{db}: {count} tablas creadas")
            else:
                print_error(f"No se pudo validar {db}")
                if err:
                    print_error(err)
            continue
        for t in tables:
            ok, out, _ = mysql_exec(
                f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='{db}' AND table_name='{t}';",
                timeout=30,
            )
            exists = ok and out.strip().splitlines()[-1].strip() == "1"
            if not exists:
                print_error(f"{t:<45} No existe")
                continue
            ok, out, err = mysql_exec(f"SELECT COUNT(*) FROM {db}.{t};", timeout=120)
            if ok and out:
                count = out.strip().splitlines()[-1].strip()
                print(f"{Colors.GREEN}✓ {t:<45} {count:>15}{Colors.END}")
            else:
                print_error(f"{t:<45} Error contando")
                if err:
                    print_error(err)


def main():
    try:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'SETUP DATABASE LOCAL - SHALOM DEV'.center(80)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'DUMPS SQL.GZ DESDE PHPMYADMIN'.center(80)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.END}\n")
        if not validate_environment():
            sys.exit(1)
        if not validate_gzip_files():
            sys.exit(1)
        create_databases()
        import_dumps()
        create_app_user()
        validate_tables()
        print_header("SETUP COMPLETADO")
        print_success("Base local lista para usar")
        print(f"\nLogs: {log_file}\n")
    except KeyboardInterrupt:
        print_error("\nCancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        logger.exception("Error inesperado")
        sys.exit(1)


if __name__ == "__main__":
    main()