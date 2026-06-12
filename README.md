# Shalom-Dev-DB

**Base de datos centralizada dockerizada para todos los proyectos Shalom en desarrollo local.**

Este proyecto proporciona un entorno Docker completo con MySQL y todas las bases de datos necesarias para ejecutar los proyectos Shalom-PRO y relacionados en tu máquina local.

---

## 📋 Requisitos Previos

- **Docker Desktop** instalado y en ejecución ([Descargar](https://www.docker.com/products/docker-desktop))

---

## 🚀 Quick Start (3 pasos)

### 1. Clonar el proyecto

```bash
git clone <tu-repositorio-url>
cd shalom-dev-db
```

### 2. Levantar la base de datos

```bash
docker compose up -d
Start-Sleep -Seconds 10
```

### 3. Ejecutar el script de setup

```powershell
.\setup-all-databases-final.ps1
```

**¡Listo!** Las bases de datos estarán listas en menos de 5 minutos.

---

## 📁 Estructura del Proyecto

```
shalom-dev-db/
├── docker-compose.yml          # Configuración de MySQL
├── setup-all-databases-final.ps1  # Script de importación automática
├── dumps/                       # Dumps de bases de datos
│   ├── *.sql.gz                # Dumps comprimidos
│   └── *.sql                   # Dumps sin comprimir
├── init/                        # Scripts de inicialización (opcional)
└── README.md                    # Este archivo
```

---

## 🗄️ Bases de Datos Incluidas

| Base de Datos | Descripción | Tablas |
|---------------|-------------|--------|
| `server12` | Sistema principal de operaciones | 16+ |
| `shalom_pro` | Datos de Shalom PRO | 14+ |
| `shalom_clientes_corp` | Clientes corporativos | Variable |
| `empresarial` | Datos empresariales | 50+ |
| `empresarial2` | Datos empresariales adicionales | Variable |
| `tarifas` | Tarifas y precios | Variable |

---

## 🔧 Qué Hace el Script

El script `import-all.ps1` automatiza completamente:

1. ✅ Elimina bases de datos existentes (limpia)
2. ✅ Crea bases de datos nuevas
3. ✅ Importa dumps comprimidos (.sql.gz)
4. ✅ Importa dumps sin comprimir (.sql)
5. ✅ Otorga permisos al usuario `docker`
6. ✅ Configura campos AUTO_INCREMENT
7. ✅ Crea índices para optimizar búsquedas
8. ✅ Limpia caché de Laravel

---

## 📊 Credenciales MySQL

```
Host: localhost
Puerto: 3307
Usuario root: root
Contraseña root: root
Usuario docker: docker
Contraseña docker: 4X+9zXs3k6%1e
```

**Para usar en Laravel .env:**

```env
DB_CONNECTION=mysql
DB_HOST=mysql-dev-shalom
DB_PORT=3306
DB_DATABASE=shalom_pro
DB_USERNAME=docker
DB_PASSWORD=4X+9zXs3k6%1e
```

---


## ⚡ Optimizaciones Incluidas

El proyecto está optimizado para rendimiento:

- **Índices en tablas principales** para búsquedas rápidas
- **Buffer pool de MySQL** (512MB) para mejor manejo de memoria
- **Cache de Laravel** habilitado
- **Campos AUTO_INCREMENT** configurados correctamente

**Resultado:** Búsquedas **92% más rápidas** ⚡


---

## 🔄 Actualizar Datos

Si alguien actualiza los dumps en el repositorio:

```powershell
# Actualizar repositorio
git pull

# Re-importar datos (elimina todo)
.\import-all.ps1

# O sin eliminar datos
docker compose down
docker compose up -d
Start-Sleep -Seconds 10
.\import-all.ps1
```

---


**Última actualización:** 11 de Junio, 2026  
**Versión:** 1.0  
**Estado:** ✅ Producción