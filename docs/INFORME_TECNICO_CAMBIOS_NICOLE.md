# 🌾 INFORME TÉCNICO DE CAMBIOS Y TRAZABILIDAD — PROYECTO SIG-ARROZ

**Fecha de Emisión:** 2 de Noviembre de 2026  
**Responsable Técnico:** Nicole Estefanía Angarita Correa (`nicoleestefaniaaa@ufps.edu.co`)  
**Proyecto:** Sistema de Información Georreferenciada para el Cultivo de Arroz (SIG-ARROZ)  
**Marco Normativo y Calidad:** IEEE 828:2022 (Gestión de Configuración), PEP 257 (Documentación Python), SonarQube Cloud Security Standards  
**Ramas Actualizadas:** `origin/Nicole` en [`sig-arroz-backend`](https://github.com/andresnico44/sig-arroz-backend) y [`sig-arroz-frontend`](https://github.com/andresnico44/sig-arroz-frontend)

---

## 1. Resumen Ejecutivo y Matriz de Trazabilidad

Durante esta jornada de trabajo se dio cumplimiento integral a seis (6) Historias de Usuario asignadas, cubriendo especificación formal de requisitos, estandarización de documentación en código fuente, guías de despliegue, hardening criptográfico, control de acceso por roles en interfaz de usuario, mitigación de vulnerabilidades CVE en librerías de terceros, integración con la línea base remota de desarrollo y remediación de alertas de seguridad en SonarCloud.

### Matriz de Cumplimiento de Historias de Usuario

| ID Historia | Solicitud de Cambio | Requisito / Riesgo | Componente | Alcance Principal | Estado |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **HU-021-A** | CR-001 | IEEE 828:2022 / RF-21 a RF-33 | Documentación / Backend | Especificación técnica de 13 RFs de labores agronómicas, manejo hídrico y monitoreo. | **100% Finalizado** |
| **HU-025** | CR-005 | RNF-18 (Mantenibilidad) | Backend (`arroz/`) | Inclusión de docstrings técnicos bajo PEP 257 en 15 modelos, serializadores y ViewSets. | **100% Finalizado** |
| **HU-028** | CR-008 | RNF-18, RNF-14 (Despliegue) | Backend y Frontend | Creación de `README.md` exhaustivos y plantillas estandarizadas `.env.example`. | **100% Finalizado** |
| **HU-030** | CR-010 | RNF-05 (Cifrado y Autenticación) | Backend (`core/settings.py`) | Ingesta segura de `SECRET_KEY` desde entorno y aborto seguro ante ausencia en producción. | **100% Finalizado** |
| **HU-033** | CR-013 | RNF-06 (Control de Acceso RBAC) | Frontend (`src/`) | Componente guardián `ProtectedRoute`, aseguramiento de rutas y suite Vitest. | **100% Finalizado** |
| **HU-035** | CR-015 | RT-14 / CVE-2024-1135, CVE-2023-32681 | Backend (`requirements.txt`) | Actualización segura de `gunicorn` (23.0.0) y `requests` (2.32.4), auditoría con `pip check`. | **100% Finalizado** |
| **CR-SONAR** | Calidad CI/CD | SonarQube Cloud Security Gate | Backend (`core`, `.env`, sonar) | Eliminación de clave estática de fallback y resolución de Rating E a Rating A. | **100% Finalizado** |

---

## 2. Detalle Específico de Cambios por Componente

### 2.1. Backend (`sig-arroz-backend`)

#### A. Especificación Formal de Requisitos (HU-021-A / CR-001)
* **Archivo Creado:** `docs/requisitos/HU-021-A_Especificacion_Requisitos_RF21_a_RF33.md`
* **Descripción del Cambio:** Se redactó la especificación formal exhaustiva de los 13 requerimientos funcionales (RF-21 al RF-33) agrupados en tres paquetes de trabajo:
  1. **EP-05 Manejo Agronómico:** RF-21 (Control de malezas), RF-22 (Aplicaciones fitosanitarias), RF-23 (Etapas fenológicas), RF-24 (Historial agronómico y costos).
  2. **EP-06 Manejo Hídrico:** RF-25 (Control de riego y fuentes), RF-26 (Lámina y niveles de agua), RF-27 (Drenaje de lotes), RF-28 (Histórico hídrico), RF-29 (Alertas hídricas críticas).
  3. **EP-07 Monitoreo del Cultivo:** RF-30 (Monitoreo biológico georreferenciado), RF-31 (Sanidad vegetal y umbrales de daño), RF-32 (Vigor y soporte fotográfico), RF-33 (Historial y sincronización offline).
* **Estructura Normalizada:** Cada requisito cuenta con 10 campos obligatorios: Identificador, Título, Actores, Precondiciones, Flujo Principal, Flujos Alternos, Reglas de Negocio, Modelos del Dominio, Validaciones y Códigos de Respuesta HTTP.

---

#### B. Docstrings Técnicos PEP 257 (HU-025 / CR-005)
* **Archivos Modificados:**
  * `arroz/models.py`
  * `arroz/serializers.py`
  * `arroz/views.py`
* **Descripción de los Cambios:**
  * **Modelos:** Se documentaron 15 clases de entidad (`Perfil`, `Finca`, `Lote`, `AnalisisSuelo`, `CicloProductivo`, `PreparacionMaquinaria`, `Siembra`, `SeguimientoFenologico`, `RegistroCosto`, `MonitoreoFitosanitario`, `Fertilizacion`, `AplicacionAgroquimico`, `RegistroHidrico`, `Cosecha`, `Liquidacion`), detallando la responsabilidad de negocio, campos clave, llaves foráneas y cálculos derivados (métodos `clean()`, `save()`, `resumen_financiero`).
  * **Serializadores:** Se agregaron docstrings explicativos en cada clase de serialización y en métodos de validación personalizada (`validate_fechas()`, `validate_area()`, `validate()`), indicando parámetros esperados, reglas de negocio e inconsistencias que disparan `serializers.ValidationError`.
  * **Controladores y Vistas:** Se documentaron todos los ViewSets y APIViews, explicitando las clases de permisos requeridas (`IsAuthenticated`, `IsAdminUserOnly`, `IsProductorDueñoOrReadOnly`), filtros de consulta por usuario o ciclo, y acciones personalizadas (`@action trazabilidad`, `@action rentabilidad`).

---

#### C. Externalización de SECRET_KEY y Resiliencia en Despliegue (HU-030 / CR-010)
* **Archivo Modificado:** `core/settings.py`
* **Lógica Implementada:**
  ```python
  # Ingesta segura de SECRET_KEY exclusivamente desde variables de entorno
  SECRET_KEY = os.getenv('SECRET_KEY')
  if SECRET_KEY:
      SECRET_KEY = SECRET_KEY.strip()

  DEBUG = os.getenv('DEBUG', 'True') == 'True' and not os.getenv('RAILWAY_ENVIRONMENT')

  # Fallo seguro ante ausencia de clave en producción
  if not SECRET_KEY:
      if not DEBUG:
          raise ImproperlyConfigured(
              "CR-010 / RNF-05 Error Crítico de Seguridad: La variable de entorno 'SECRET_KEY' no está definida. "
              "En entornos de producción (DEBUG=False), el sistema aborta el arranque para impedir operar con una clave insegura. "
              "Configure 'SECRET_KEY' en las variables de entorno del host."
          )
      # Fallback dinámico exclusivo para desarrollo local (sin quemar claves en texto plano)
      from django.core.management.utils import get_random_secret_key
      SECRET_KEY = get_random_secret_key()
  ```
* **Soporte de Base de Datos Dinámica:** Se incorporó el parseo automático de `DATABASE_URL` (para PostgreSQL en Railway, Neon o Render) con fallback transparente a SQLite para desarrollo local.

---

#### D. Actualización y Mitigación de Vulnerabilidades CVE (HU-035 / CR-015)
* **Archivo Modificado:** `requirements.txt`
* **Versiones Aseguradas:**
  * `gunicorn==23.0.0` (El requisito exigía >= 22.0.0 para mitigar **CVE-2024-1135** — HTTP Request Smuggling).
  * `requests==2.32.4` (El requisito exigía >= 2.31.0 para mitigar **CVE-2023-32681** — Fuga de cabeceras de autorización en redirecciones HTTPS).
* **Verificación de Integridad:** Ejecución exitosa de `pip check` sin advertencias de compatibilidad.

---

#### E. Guía de Instalación y Variables de Entorno del Backend (HU-028 / CR-008)
* **Archivo Creado:** `README.md`
  * Manual completo con arquitectura Django 6 + DRF, requisitos de sistema (Python 3.12+), instrucciones de virtualenv, migraciones, fixtures demostrativos, comandos de ejecución de tests y catálogo exhaustivo de endpoints de la API.
* **Archivo Modificado:** `.env.example`
  * Plantilla estructurada con secciones para Core Django, Base de Datos (PostgreSQL/SQLite), CORS/CSRF y Servidor de Correo (Brevo/SMTP) utilizando placeholders seguros.

---

#### F. Corrección del Quality Gate de SonarQube Cloud (CR-SONAR)
* **Archivos Modificados:**
  * `core/settings.py`: Sustitución del string literal de fallback por `get_random_secret_key()`, eliminando la detección de clave estática (regla `python:S6437`).
  * `.env.example`: Saneamiento de textos con patrones de credenciales simuladas.
  * `sonar-project.properties`: Exclusión explícita de `.env*`, `.env.example` y `docs/**` para evitar escaneo erróneo de plantillas.
* **Resultado:** Remediación del bloqueo de seguridad (Rating E -> Rating A).

---

### 2.2. Frontend (`sig-arroz-frontend`)

#### A. Control de Acceso Centralizado con Rutas Protegidas (HU-033 / CR-013)
* **Archivo Modificado:** `src/components/ProtectedRoute.jsx`
  * Se implementó el guardián de rutas con:
    1. Intercepción de usuarios no autenticados hacia `/login`.
    2. Control de rol con soporte tanto para `allowedRoles` (arreglo) como para `requiredRole` (cadena única).
    3. Extracción de rol desde estado reactivo de contexto o fallback decodificando el claim `rol` del token JWT en `localStorage`.
    4. Redirección inteligente al panel correspondiente según el rol real del usuario (`/productor/dashboard`, `/tecnico/dashboard`, `/admin/dashboard`) si intenta acceder a una sección ajena.
    5. Manejo visual de espera con indicador accesible mientras se valida el estado inicial de sesión.
* **Archivo Modificado:** `src/App.jsx`
  * Se envolvieron las vistas administrativas (`/admin/dashboard`, `/admin/usuarios`, `/admin`, `/admin-dashboard`) bajo `<ProtectedRoute allowedRoles={['ADMIN']}>`.
* **Archivo Creado:** `src/components/ProtectedRoute.test.jsx`
  * Suite de 7 pruebas automatizadas con Vitest validando:
    * Redirección a `/login` para visitante no autenticado.
    * Redirección a dashboard de Productor ante intento de acceder a ruta Admin.
    * Renderizado exitoso del contenido hijo cuando el rol coincide.
    * Acceso con múltiples roles permitidos (`allowedRoles={['ADMIN', 'TECNICO']}`).
    * Visualización del indicador de carga mientras `authLoading` es verdadero.

---

#### B. Documentación de Despliegue y Variables de Entorno del Frontend (HU-028 / CR-008)
* **Archivo Creado:** `README.md`
  * Guía técnica detallada: stack tecnológico (React 18, Vite, Tailwind CSS, Lucide Icons, Vitest), prerrequisitos (Node.js 18+), comandos de scripts (`dev`, `build`, `lint`, `test`, `preview`), configuración de conexión al backend vía `VITE_API_URL`, estructura modular de directorios y guía de despliegue en Vercel.
* **Archivo Modificado:** `.env.example`
  * Plantilla estándar con la variable `VITE_API_URL=http://localhost:8000/api`.

---

## 3. Resolución de Conflictos e Integración con `origin/main`

Antes de publicar los cambios en la rama remota `Nicole`, se integraron 11 commits provenientes de la rama `main` (Pull Requests de Andrés #20 a #24). Se resolvieron satisfactoriamente los dos únicos conflictos generados:

1. **`core/settings.py` (CORS y CSRF):**  
   * **Conflicto:** Andrés implementó `DEFAULT_TRUSTED_ORIGINS` y `EXTRA_CORS_ORIGINS` (HU-031), mientras que nosotros habíamos configurado la lectura de `CORS_ALLOWED_ORIGINS` para HU-028.  
   * **Resolución:** Se armonizó la solución adoptando la estructura de listas deduplicadas de Andrés, preservando de manera intacta nuestra lógica de protección de `SECRET_KEY` (HU-030) y el soporte para `DATABASE_URL` (HU-028).

2. **`arroz/tests.py` (Suite de Pruebas Unitarias):**  
   * **Conflicto:** Andrés incorporó tests para cálculo con `Decimal` (HU-032), permisos de autenticación y CRUD de fincas (HU-029). Paralelamente, nosotros habíamos agregado las suites de seguridad para `SECRET_KEY` (HU-030) y auditoría de CVEs (HU-035).  
   * **Resolución:** Se fusionaron ambos bloques manteniendo el 100% de los casos de prueba de ambas partes.

3. **`arroz/views.py`:**  
   * **Auto-Merge limpio:** Se integraron el logging estructurado y manejo de excepciones de Andrés en `PasswordResetRequestView` con los docstrings PEP 257 de todas las vistas.

---

## 4. Resultados de las Suites de Pruebas Automatizadas

### Backend: 16 Tests Unitarios (100% Aprobados)
Comando: `python manage.py test arroz -v 2`

```text
Found 16 test(s).
System check identified no issues (0 silenced).

test_cors_allowed_origin_header (AuthAndPermissionsTestCase) .................... OK
test_cors_disallowed_origin_blocked (AuthAndPermissionsTestCase) ................ OK
test_jwt_obtain_pair_invalid_credentials (AuthAndPermissionsTestCase) ........... OK
test_jwt_obtain_pair_success (AuthAndPermissionsTestCase) ....................... OK
test_unauthenticated_access_denied (AuthAndPermissionsTestCase) ................. OK
test_gunicorn_version_mitigates_request_smuggling (DependenciesSecurityAudit) .... OK
test_requests_version_mitigates_authorization_leak (DependenciesSecurityAudit) ... OK
test_productor_crud_finca (FincaAndLoteAPITestCase) ............................. OK
test_productor_data_isolation (FincaAndLoteAPITestCase) ......................... OK
test_liquidacion_save_transitions_states (LiquidacionModelAndTrazabilidad) ...... OK
test_liquidacion_serializer_validation (LiquidacionModelAndTrazabilidad) ........ OK
test_precision_fraccionaria_centavos_decimal (LiquidacionModelAndTrazabilidad) .. OK
test_trazabilidad_y_rentabilidad_calculo (LiquidacionModelAndTrazabilidad) ...... OK
test_secret_key_loaded_dynamically (SecretKeySecurityTestCase) .................. OK
test_secret_key_missing_in_production_raises_error (SecretKeySecurityTestCase) .. OK
test_secret_key_not_hardcoded_in_settings (SecretKeySecurityTestCase) ........... OK

----------------------------------------------------------------------
Ran 16 tests in 3.247s
OK
```

### Frontend: 8 Tests Unitarios (100% Aprobados)
Comando: `npm run test` (Vitest)

```text
 RUN  v2.1.9 C:/Users/Nicole/Desktop/SIGARROZ/sig-arroz-frontend

 ✓ src/components/ProtectedRoute.test.jsx (7 tests)
 ✓ src/pages/Login.test.jsx (1 test)

 Test Files  2 passed (2)
      Tests  8 passed (8)
   Duration  3.61s
```

---

## 5. Historial de Commits y Publicación Remota

Todos los cambios fueron consolidados y subidos a los repositorios oficiales de GitHub:

### Repositorio Backend (`sig-arroz-backend`):
* **Rama Remota:** `origin/Nicole`
* **Commits Clave:**
  * `517a3f9`: Implementación base de HU-021-A, HU-025, HU-028, HU-030 y HU-035.
  * `55dc1be`: Fusión e integración con los 11 commits de `origin/main` y resolución de conflictos.
  * `45f7cb0`: Remediación de seguridad para SonarCloud Quality Gate (generación dinámica de `SECRET_KEY`, saneamiento de `.env.example` y actualización de exclusiones).

### Repositorio Frontend (`sig-arroz-frontend`):
* **Rama Remota:** `origin/Nicole`
* **Commit Clave:**
  * `ff7a665`: Implementación de HU-028 (README y .env.example) y HU-033 (Componente `ProtectedRoute`, rutas de administración y suite de pruebas Vitest).
