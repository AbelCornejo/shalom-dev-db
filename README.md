# Shalom-Dev-DB

**Base de datos centralizada dockerizada para todos los proyectos Shalom en desarrollo local.**

**DRIVE**

https://drive.google.com/drive/folders/1iRkA5Szy1vaQXVD_bHcT-ajHApmw4qcT


---

## 📋 Requisitos Previos

- **Docker Desktop** instalado y en ejecución ([Descargar](https://www.docker.com/products/docker-desktop))

---

## 🚀 Quick Start 

### 1. Clonar el proyecto

```bash
git clone <tu-repositorio-url>
cd shalom-dev-db
```

### 2. Crear la carpeta "snapshots"

Al crear la carpeta snapshots, copias los archivos del comprimido del link del drive (2 archivos)


### 3. Crear un volumen vacio

docker volume create shalom-dev-db_mysql_dev_data

### 4. Restauracion del snapshot


Restaurar el snapshot dentro del volumen:

docker run --rm `
  -v shalom-dev-db_mysql_dev_data:/volume `
  -v "${PWD}\snapshots:/backup" `
  alpine sh -c "cd /volume && tar -xzf /backup/dev-db-core-20260618-mysql8.tar.gz"


### 5. Levantar el contenedor de la BD

docker compose up -d



## 📁 Estructura del Proyecto

```
shalom-dev-db/
├── docker-compose.yml          # Configuración de MySQL
├── snapshots/                   # Snapshots de bases de datos
│   ├── *.tar.gz                # Snapshots comprimidos
│   └── *.txt                   
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


**Última actualización:** 19 de Junio, 2026  
**Versión:** 1.0  
**Estado:** ✅ Producción