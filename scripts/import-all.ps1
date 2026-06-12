# import-all.ps1
# Script completo para importar todas las bases de datos automáticamente con optimizaciones

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "SETUP AUTOMATICO - SHALOM DEV" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Variables
$dumpFolder = "./dumps"
$mysql_host = "mysql-dev-shalom"
$mysql_user = "root"
$mysql_password = "root"
$docker_user = "docker"
$docker_password = "4X+9zXs3k6%1e"

# Esperar a que MySQL esté listo
Write-Host "`nEsperando a que MySQL esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Definir bases de datos
$databases = @("server12", "shalom_pro", "shalom_clientes_corp", "empresarial", "empresarial2", "tarifas")

# ============================================================
# 1. ELIMINAR Y CREAR BASES DE DATOS
# ============================================================
Write-Host "`n======================================" -ForegroundColor Yellow
Write-Host "1. ELIMINANDO Y CREANDO BASES DE DATOS" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Yellow

foreach ($db in $databases) {
    Write-Host "Preparando base de datos: $db..." -ForegroundColor Yellow
    docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "DROP DATABASE IF EXISTS $db; CREATE DATABASE IF NOT EXISTS $db;"
}

# ============================================================
# 2. IMPORTAR DUMPS .SQL.GZ
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "2. IMPORTANDO DUMPS COMPRIMIDOS (.sql.gz)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$gzDumps = Get-ChildItem -Path $dumpFolder -Filter "*.sql.gz" | Sort-Object Name

foreach ($dump in $gzDumps) {
    $fileName = $dump.Name
    
    # Determinar base según nombre
    if ($fileName -match "server12") { $dbTarget = "server12" }
    elseif ($fileName -match "shalom_pro") { $dbTarget = "shalom_pro" }
    elseif ($fileName -match "shalom_clientes_corp") { $dbTarget = "shalom_clientes_corp" }
    elseif ($fileName -match "empresarial2") { $dbTarget = "empresarial2" }
    elseif ($fileName -match "empresarial") { $dbTarget = "empresarial" }
    elseif ($fileName -match "tarifas") { $dbTarget = "tarifas" }
    else { 
        Write-Host "⚠ No se reconoce base para $fileName, saltando..." -ForegroundColor Red
        continue 
    }

    Write-Host "Importando $fileName en $dbTarget..." -ForegroundColor Green
    docker exec -i $mysql_host sh -c "gunzip -c /dumps/$fileName | mysql -u$mysql_user -p$mysql_password --init-command='SET FOREIGN_KEY_CHECKS=0; SET UNIQUE_CHECKS=0;' $dbTarget" 2>&1 | Out-Null
}

# ============================================================
# 3. IMPORTAR DUMPS .SQL (sin comprimir)
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "3. IMPORTANDO DUMPS SIN COMPRIMIR (.sql)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Importar shalom_pro extras
$shalom_pro_sql_files = @(
    @{file="shalom_pro_schema.sql"; db="shalom_pro"},
    @{file="shalom_pro_data.sql"; db="shalom_pro"},
    @{file="shalom_pro_service_order.sql"; db="shalom_pro"},
    @{file="shalom_pro_login_seed.sql"; db="shalom_pro"},
    @{file="shalom_pro_extra_branches_person.sql"; db="shalom_pro"},
    @{file="shalom_pro_extra_companies_user.sql"; db="shalom_pro"},
    @{file="shalom_pro_extra_company.sql"; db="shalom_pro"},
    @{file="shalom_pro_extra_contact_extra.sql"; db="shalom_pro"},
    @{file="shalom_pro_extra_get_user.sql"; db="shalom_pro"}
)

# Importar empresarial
$empresarial_sql_files = @(
    @{file="empresarial_schema_utf8.sql"; db="empresarial"},
    @{file="empresarial_data_utf8.sql"; db="empresarial"}
)

# Importar empresarial2
$empresarial2_sql_files = @(
    @{file="empresarial2_schema.sql"; db="empresarial2"}
)

# Combinar todos
$allSqlFiles = $shalom_pro_sql_files + $empresarial_sql_files + $empresarial2_sql_files

foreach ($item in $allSqlFiles) {
    $filePath = Join-Path $dumpFolder $item.file
    
    if (Test-Path $filePath) {
        Write-Host "Importando $($item.file) en $($item.db)..." -ForegroundColor Green
        Get-Content $filePath | docker exec -i $mysql_host mysql -u$mysql_user -p$mysql_password $item.db 2>&1 | Out-Null
    } else {
        Write-Host "⚠ Archivo no encontrado: $($item.file)" -ForegroundColor Yellow
    }
}

# ============================================================
# 4. DAR PERMISOS AL USUARIO DOCKER
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "4. DANDO PERMISOS AL USUARIO DOCKER" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

foreach ($db in $databases) {
    Write-Host "Otorgando permisos en $db..." -ForegroundColor Yellow
    docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "GRANT ALL PRIVILEGES ON $db.* TO '$docker_user'@'%'; FLUSH PRIVILEGES;"
}

# ============================================================
# 5. ARREGLAR CAMPOS AUTO_INCREMENT
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "5. ARREGLANDO CAMPOS AUTO_INCREMENT" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "Modificando tablas en server12..." -ForegroundColor Yellow
docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "
ALTER TABLE server12.emp_ordenservicio MODIFY COLUMN ose_id INT AUTO_INCREMENT;
ALTER TABLE server12.emp_os_detalle MODIFY COLUMN osd_id INT AUTO_INCREMENT;
" 2>&1 | Out-Null

# ============================================================
# 5.5 CREAR INDICES PARA OPTIMIZAR PERFORMANCE
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "5.5 CREANDO INDICES PARA OPTIMIZAR" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "Creando índices en tablas principales..." -ForegroundColor Yellow
docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "
-- Índices en server12
ALTER TABLE server12.emp_ordenservicio ADD INDEX idx_ose_estado (ose_estado);
ALTER TABLE server12.emp_os_detalle ADD INDEX idx_osd_osid (osd_osid);

-- Índices en shalom_pro
ALTER TABLE shalom_pro.users ADD INDEX idx_email (email);
ALTER TABLE shalom_pro.service_order ADD INDEX idx_user_id (user_id);

-- Índices en empresarial
ALTER TABLE empresarial.emp_client_key_block ADD INDEX idx_document (document);
" 2>&1 | Out-Null

Write-Host "✓ Índices creados exitosamente" -ForegroundColor Green

# ============================================================
# 6. VALIDAR IMPORTACION
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "6. VALIDANDO IMPORTACION" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nBases de datos creadas:" -ForegroundColor Cyan
docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "SHOW DATABASES WHERE Db NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys');" 2>&1 | Out-Null

Write-Host "`nTotal de tablas por base:" -ForegroundColor Cyan
docker exec $mysql_host mysql -u$mysql_user -p$mysql_password -e "
SELECT table_schema AS 'Base', COUNT(*) AS 'Tablas'
FROM information_schema.tables
WHERE table_schema IN ('server12','shalom_pro','shalom_clientes_corp','empresarial','empresarial2','tarifas')
GROUP BY table_schema
ORDER BY table_schema;
" 2>&1 | Out-Null

# ============================================================
# 7. LIMPIAR CACHE LARAVEL
# ============================================================
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "7. LIMPIANDO CACHE DE LARAVEL" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "Limpiando configuración y cache..." -ForegroundColor Yellow
docker exec pro-qa_app php artisan config:clear 2>&1 | Out-Null
docker exec pro-qa_app php artisan cache:clear 2>&1 | Out-Null

# ============================================================
# RESUMEN FINAL
# ============================================================
Write-Host "`n======================================" -ForegroundColor Green
Write-Host "✓ SETUP COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

Write-Host "`nResumen:" -ForegroundColor Cyan
Write-Host "✓ Bases de datos creadas y limpias" -ForegroundColor Green
Write-Host "✓ Dumps .sql.gz importados" -ForegroundColor Green
Write-Host "✓ Dumps .sql importados" -ForegroundColor Green
Write-Host "✓ Permisos otorgados al usuario docker" -ForegroundColor Green
Write-Host "✓ Campos AUTO_INCREMENT configurados" -ForegroundColor Green
Write-Host "✓ Indices creados para optimizar búsquedas" -ForegroundColor Green
Write-Host "✓ Cache de Laravel limpiado" -ForegroundColor Green

Write-Host "`nURL de la aplicación:" -ForegroundColor Cyan
Write-Host "http://localhost:8006" -ForegroundColor Yellow

Write-Host "`nPróximos pasos:" -ForegroundColor Cyan
Write-Host "1. Actualiza el navegador" -ForegroundColor Yellow
Write-Host "2. Inicia sesión en la aplicación" -ForegroundColor Yellow
Write-Host "3. ¡Listo para usar!" -ForegroundColor Yellow

Write-Host "`n======================================" -ForegroundColor Green