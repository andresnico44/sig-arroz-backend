# 🌾 SIG-ARROZ — Backend API Service

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.17-A30000?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JWT](https://img.shields.io/badge/Auth-SimpleJWT-black?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)

Servicio backend de alto rendimiento para el **Sistema de Información Georreferenciada para el Cultivo de Arroz (SIG-ARROZ)**. Expone una arquitectura RESTful robusta y segura para la administración territorial de fincas y lotes, trazabilidad agronómica estacional, manejo hídrico, sanidad vegetal, monitoreo de labores y cálculo de rentabilidad financiera con aritmética de alta precisión.

---

## 1. Arquitectura del Sistema

El backend está construido sobre **Django 6.0** y **Django REST Framework (DRF)**, diseñado bajo un patrón de capas desacopladas con soporte multi-base de datos (PostgreSQL para producción y SQLite3 para desarrollo local ágil):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Cliente Web / Frontend React                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / JSON (JWT Bearer)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Django REST Framework (DRF)                     │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   Seguridad y CORS      │  │      Autenticación & Permisos       │  │
│  │ CorsMiddleware, X-Frame │  │ JWT (SimpleJWT) + RBAC (Perfiles)   │  │
│  └────────────┬────────────┘  └──────────────────┬──────────────────┘  │
│               ▼                                  ▼                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │             Controladores de Dominio (ViewSets & APIViews)        │  │
│  │ Fincas, Lotes, Ciclos, Labores, Fenología, Riegos, Costos, etc.  │  │
│  └───────────────────────────────────┬──────────────────────────────┘  │
│                                      ▼                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                Serializadores y Validaciones de Negocio          │  │
│  │      Validación cruzada RF12, umbrales %, precisión Decimal      │  │
│  └───────────────────────────────────┬──────────────────────────────┘  │
│                                      ▼                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  Modelos ORM & Transacciones Atómicas            │  │
│  │      Transiciones automáticas de estado y sincronización contable│  │
│  └───────────────────────────────────┬──────────────────────────────┘  │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Capa de Persistencia de Datos                     │
│   Producción: PostgreSQL (Neon / Railway) | Desarrollo: SQLite3 local  │
└────────────────────────────────────────────────────────────────────────┘
```

### Características Técnicas Clave
- **Control de Acceso Basado en Roles (RBAC):** Roles diferenciados (`ADMIN`, `PRODUCTOR`, `TECNICO`) con matrices de permisos multi-inquilino.
- **Transacciones Atómicas (`transaction.atomic`):** Garantía ACID en el registro de siembra, preparación, fertilización, aplicaciones y riegos con sincronización automática en la billetera de costos (`RegistroCosto`).
- **Aritmética Monetaria de Precisión (Mitigación INSSA-25):** Empleo estricto de `Decimal` para evitar imprecisiones de redondeo en rentabilidad y liquidación del molino.
- **Normalización de Requisitos (CR-001):** Cobertura exhaustiva de los módulos de manejo agronómico, hídrico y fitosanitario (RF-21 a RF-33).

---

## 2. Requisitos Previos

- **Python:** Versión `3.12` o superior (`3.12.x` / `3.13.x` / `3.14.x`).
- **Gestor de Paquetes:** `pip` actualizado.
- **Motor de Base de Datos:**
  - *Desarrollo Local:* SQLite3 (incluido por defecto en Python, sin dependencias externas).
  - *Producción / Staging:* PostgreSQL `15+` o `16+` (ej. Neon Database, Supabase o Railway Postgres).
- **Git:** Para clonación y control de versiones.

---

## 3. Puesta en Marcha en Entorno Local

Siga los siguientes pasos para clonar, configurar y ejecutar el servidor en su máquina local:

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/andresnico44/sig-arroz-backend.git
cd sig-arroz-backend
```

### Paso 2: Crear y Activar el Entorno Virtual

- **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(Si PowerShell restringe la ejecución de scripts, ejecute previamente: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **En Windows (CMD):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

- **En Linux / macOS (Bash / Zsh):**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Paso 3: Instalar Dependencias del Proyecto
Con el entorno virtual activado, instale las bibliotecas especificadas en `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno
Copie la plantilla de variables de entorno y configure los parámetros deseados:

- **En Windows:**
  ```powershell
  Copy-Item .env.example .env
  ```
- **En Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

> [!NOTE]
> Para desarrollo local rápido, no es obligatorio configurar PostgreSQL. Si deja comentadas `DATABASE_URL` y `DB_HOST` en su archivo `.env`, Django usará automáticamente SQLite3 local (`db.sqlite3`).

### Paso 5: Aplicar Migraciones de Base de Datos
Ejecute las migraciones de Django para construir la estructura de tablas:
```bash
python manage.py migrate
```

### Paso 6: Crear Cuenta de Superusuario (Administrador)
Cree el usuario administrador para acceder al panel Django Admin y a la gestión del sistema:
```bash
python manage.py createsuperuser
```
*Siga las instrucciones en consola ingresando nombre de usuario, correo electrónico y contraseña.*

### Paso 7: Carga Opcional de Datos Iniciales / Fixtures
Si dispone de datos semilla o fixtures para pruebas, puede cargarlos mediante:
```bash
# Carga de datos de prueba si existe fixture
python manage.py loaddata initial_data.json
```

### Paso 8: Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver 0.0.0.0:8000
```
El servidor quedará disponible en: `http://localhost:8000/`

---

## 4. Ejecución de Pruebas Automatizadas

El proyecto cuenta con suites de pruebas unitarias y de integración que verifican transiciones de estado, validaciones de liquidación molinera, cálculos de rentabilidad y controles de seguridad:

```bash
# Ejecutar todas las pruebas de la app 'arroz'
python manage.py test arroz

# Ejecutar con nivel de detalle (verbose)
python manage.py test arroz -v 2

# Ejecutar una prueba específica
python manage.py test arroz.tests.LiquidacionModelAndTrazabilidadTestCase
```

---

## 5. Catálogo de Endpoints de la API REST

Todos los endpoints están prefijados por `/api/`. A excepción del login y registro, todos exigen cabecera de autenticación:
`Authorization: Bearer <access_token>`

| Módulo | Método | Endpoint | Descripción | Permisos |
| :--- | :---: | :--- | :--- | :--- |
| **Autenticación** | `POST` | `/api/token/` | Inicio de sesión, retorna JWT (Access + Refresh). | `Público` |
| | `POST` | `/api/token/refresh/` | Renovación de token de acceso caducado. | `Público` |
| | `POST` | `/api/users/register/` | Autoregistro público de usuarios (con rol). | `Público` |
| | `POST` | `/api/password_reset/` | Solicitud de restablecimiento de contraseña. | `Público` |
| **Administración** | `GET` | `/api/admin/metrics/` | KPIs globales del sistema (usuarios, fincas, ciclos). | `ADMIN` |
| | `GET/POST`| `/api/users-gestion/` | CRUD y gestión RBAC de usuarios. | `ADMIN` |
| | `GET` | `/api/productores/` | Listado exclusivo de productores para asignar predios. | `ADMIN` |
| **Gestión Territorial**| `GET/POST`| `/api/fincas/` | Listado y registro de fincas (`?productor_id=`). | `Autenticado` (RBAC) |
| | `GET/POST`| `/api/lotes/` | Listado y registro de lotes (`?finca_id=`). | `Autenticado` (RBAC) |
| | `GET/POST`| `/api/analisis-suelos/` | Registro de análisis edafológicos (`?lote_id=`). | `Autenticado` (RBAC) |
| **Ciclos Productivos** | `GET/POST`| `/api/ciclos/` | Planificación y control de ciclos (`?lote_id=`). | `Autenticado` (RBAC) |
| | `GET` | `/api/ciclos/{id}/trazabilidad/` | **Trazabilidad Integral y Resumen Financiero**. | `Autenticado` |
| **Labores Agronómicas**| `GET/POST`| `/api/preparacion/` | Preparación de maquinaria (`?ciclo_id=`, `?lote_id=`).| `Autenticado` |
| | `GET/POST`| `/api/siembra/` | Siembra y germinación (`?ciclo_id=`). | `Autenticado` |
| | `GET/POST`| `/api/fenologia/` | Seguimiento fenológico y vigor (`?ciclo_id=`). | `Autenticado` |
| **Sanidad & Nutrición**| `GET/POST`| `/api/monitoreos/` | Monitoreo de plagas, enfermedades y malezas. | `Autenticado` |
| | `GET/POST`| `/api/aplicaciones-agroquimicos/` | Aspersión de plaguicidas y periodos de carencia. | `Autenticado` |
| | `GET/POST`| `/api/fertilizaciones/` | Aplicación de fertilizantes edáficos / foliares. | `Autenticado` |
| **Manejo Hídrico** | `GET/POST`| `/api/riegos/` | Eventos de riego, lámina en cm y estado de drenaje.| `Autenticado` |
| **Economía & Cierre** | `GET/POST`| `/api/costos/` | Billetera centralizada de costos del ciclo. | `Autenticado` |
| | `GET/POST`| `/api/cosechas/` | Registro de recolección en verde y rendimiento (t/ha). | `Autenticado` |
| | `GET/POST`| `/api/liquidaciones/` | Liquidación económica de trilla con el molino. | `Autenticado` |

---

## 6. Despliegue en Producción (Railway / PaaS)

El backend incluye configuraciones listas para despliegue automatizado en **Railway**:
- **Archivo `railway.json`:** Define comandos de build y puesta en marcha con Gunicorn y WhiteNoise.
- **Variables requeridas en el dashboard de la nube:**
  - `SECRET_KEY`: Cadena segura aleatoria.
  - `DEBUG`: `False`.
  - `DATABASE_URL`: Cadena de conexión PostgreSQL provista por Neon o Railway.
  - `CORS_ALLOWED_ORIGINS`: URL del frontend desplegado en Vercel (ej. `https://sig-arroz-frontend.vercel.app`).
  - `ALLOWED_HOSTS`: `.railway.app,localhost`.

Comando de arranque ejecutado por el PaaS:
```bash
python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 7. Licencia y Créditos
Desarrollado para el proyecto **SIG-ARROZ**. Documentación y gestión bajo la norma **IEEE 828:2022**.

