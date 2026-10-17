# ESPECIFICACIÓN DETALLADA DE REQUERIMIENTOS FUNCIONALES (RF-34 A RF-51)
## Proyecto SIG-ARROZ — Universidad Francisco de Paula Santander (UFPS)
**Documento Técnico de Trazabilidad y Control de Cambios (CR-001 / HU-021-B)**  
**Línea Base IEEE 828:2022 / Semestre 2026-2**  
**Responsable:** Ramiro Andrés Niño Correa (Desarrollador)  
**Aprobó:** Royner Daniel Omaña Macualo (Product Owner)

---

# ÍNDICE DE REQUERIMIENTOS ABARCADOS
1. **Épica EP-08: Cosecha y Producción** (RF-34 a RF-38)
2. **Épica EP-09: Trazabilidad del Ciclo Productivo** (RF-39 a RF-42)
3. **Épica EP-10: Reportes e Indicadores** (RF-43 a RF-47)
4. **Épica EP-11: Gestión de Usuarios y Seguridad** (RF-48 a RF-51)

---

# 1. ÉPICA EP-08: COSECHA Y PRODUCCIÓN

### Ficha Técnica: RF-34 — Registrar cosecha por lote
* **Actor Principal:** Productor Agrícola / Técnico Agrónomo.
* **Modelos involucrados:** `Cosecha`, `CicloProductivo`, `Lote`.
* **Endpoint:** `POST /api/cosechas/`
* **Precondición:** El lote debe tener un `CicloProductivo` activo en estado `EJECUCION` y contar con registro previo de siembra (`Siembra`).
* **Flujo Principal:**
  1. El usuario selecciona el ciclo productivo y digita la fecha de corte/cosecha.
  2. Registra la producción bruta obtenida en kilogramos (`produccion_obtenida_kg`).
  3. Registra porcentajes de humedad del grano (`humedad_grano_porcentaje`) e impurezas (`impurezas_porcentaje`).
  4. El sistema valida que la fecha no sea anterior a la siembra ni superior a la fecha actual.
  5. El sistema persiste el registro de `Cosecha`.
  6. Se dispara la transición automática de estados: el ciclo pasa a estado `COSECHADO` y el lote pasa a estado `COSECHADO`.
* **Flujos Alternos:**
  - *Ciclo sin siembra:* El sistema rechaza la operación con código HTTP 400 y mensaje: *"No se puede registrar cosecha sin un registro previo de siembra en el ciclo"*.
* **Poscondición:** Registro de cosecha vinculado al ciclo; lote y ciclo en estado `COSECHADO`.

---

### Ficha Técnica: RF-35 — Registrar producción obtenida
* **Actor Principal:** Productor / Técnico.
* **Modelos involucrados:** `Cosecha`.
* **Precondición:** Cosecha en proceso de registro.
* **Regla de Negocio:** La producción debe ser un valor numérico positivo mayor a 0 kg.
* **Validación:** `produccion_obtenida_kg > 0`. Error 400 si el valor es nulo o negativo.

---

### Ficha Técnica: RF-36 — Calcular rendimiento por hectárea
* **Actor Principal:** Sistema SIG-ARROZ (Cálculo automático).
* **Modelos involucrados:** `Cosecha`, `Lote`, `CicloProductivo`.
* **Fórmula de Negocio:**
  $$\text{Rendimiento (Ton/Ha)} = \frac{\text{produccion\_obtenida\_kg} / 1000}{\text{lote.area\_hectareas}}$$
* **Garantía Técnica:** Operación aritmética de alta precisión utilizando el tipo `Decimal` con redondeo a dos cifras decimales.

---

### Ficha Técnica: RF-37 — Registrar condiciones de cosecha
* **Actor Principal:** Técnico Agrícola.
* **Modelos involucrados:** `Cosecha`.
* **Campos:** Método de recolección (mecanizada/manual), porcentaje de humedad inicial y porcentaje de grano verde/vano.
* **Validaciones:** Humedad e impurezas restringidas al rango numérico `[0.0, 100.0]`.

---

### Ficha Técnica: RF-38 — Consultar historial de producción
* **Actor Principal:** Productor / Técnico / Administrador.
* **Endpoint:** `GET /api/cosechas/?ciclo_id=&finca_id=&lote_id=`
* **Aislamiento de Seguridad:** El productor únicamente recibe cosechas pertenecientes a sus fincas; administradores y técnicos tienen visibilidad global.

---

# 2. ÉPICA EP-09: TRAZABILIDAD DEL CICLO PRODUCTIVO

### Ficha Técnica: RF-39 — Registrar historial completo del ciclo productivo
* **Actor Principal:** Sistema SIG-ARROZ.
* **Modelos involucrados:** `CicloProductivo`, `HistorialCiclo`.
* **Regla de Negocio:** Cada cambio de estado (`PLANIFICADO` $\rightarrow$ `EJECUCION` $\rightarrow$ `COSECHADO` $\rightarrow$ `FINALIZADO` / `CANCELADO`) debe generar automáticamente una traza auditable con `estado_anterior`, `estado_nuevo`, fecha/hora y usuario responsable.

---

### Ficha Técnica: RF-40 — Asociar producción con lote de origen
* **Actor Principal:** Sistema SIG-ARROZ.
* **Modelos involucrados:** `Cosecha` $\rightarrow$ `CicloProductivo` $\rightarrow$ `Lote` $\rightarrow$ `Finca`.
* **Regla de Integridad:** Se asegura la clave foránea no nula hacia el ciclo; se impide desvincular un lote con cosecha consolidada.

---

### Ficha Técnica: RF-41 — Consultar trazabilidad completa del cultivo
* **Actor Principal:** Productor / Técnico / Auditor.
* **Endpoint:** `GET /api/ciclos/{id}/trazabilidad/`
* **Contenido Retornado (Payload Consolidado):**
  1. Ficha del Lote y Finca (área, coordenadas, tipo de suelo).
  2. Análisis de Suelos (pH, materia orgánica, recomendaciones).
  3. Labores de Preparación y Maquinaria (arado, rastra, caballoneo).
  4. Datos de Siembra (variedad FEDEARROZ, densidad kg/ha, método).
  5. Seguimiento Fenológico (vegetativa, reproductiva, maduración).
  6. Monitoreo Fitosanitario (plagas, enfermedades, malezas).
  7. Aplicaciones de Agroquímicos y Fertilizaciones.
  8. Registros Hídricos (riegos y lámina de agua).
  9. Costos Operativos y Liquidación Económica del Molino.
  10. Resumen Financiero con Aritmética `Decimal` (Total egresos, ingreso neto, balance neto y balance/ha).

---

### Ficha Técnica: RF-42 — Generar historial del proceso productivo por ciclo
* **Actor Principal:** Productor / Administrador.
* **Precondición:** Ciclo cerrado con liquidación económica registrada.
* **Resultado:** Visualización cronológica ordenada de todas las intervenciones técnicas del cultivo desde la preparación hasta la liquidación final.

---

# 3. ÉPICA EP-10: REPORTES E INDICADORES

### Ficha Técnica: RF-43 — Generar reportes de productividad por lote
* **Actor:** Productor / Administrador.
* **Modelos:** `Lote`, `CicloProductivo`, `Cosecha`.
* **Indicadores:** Rendimiento histórico promedio (Ton/Ha) por lote a lo largo de múltiples semestres agrícolas.

---

### Ficha Técnica: RF-44 — Generar indicadores por ciclo productivo
* **Actor:** Técnico / Productor.
* **Endpoint:** `GET /api/ciclos/{id}/trazabilidad/` (bloque `resumen_financiero`).
* **Métricas Obligatorias:**
  - `total_egresos` (COP)
  - `ingreso_neto` (COP)
  - `balance_neto` (COP)
  - `costo_por_hectarea` (COP/Ha)
  - `ingreso_por_hectarea` (COP/Ha)
  - `balance_por_hectarea` (COP/Ha)
  - `rentable` (Booleano: `balance > 0`)

---

### Ficha Técnica: RF-45 — Generar reportes técnicos (uso de agua, fertilización)
* **Actor:** Técnico Agrícola.
* **Modelos:** `RegistroHidrico`, `Fertilizacion`, `AplicacionAgroquimico`.
* **Contenido:** Resumen de volumen de agua suministrado (m³ o días de riego) y balance de unidades nutricionales (Nitrógeno, Fósforo, Potasio - NPK) aplicadas por hectárea.

---

### Ficha Técnica: RF-46 — Visualizar indicadores de rendimiento
* **Actor:** Administrador / Productor.
* **Endpoint:** `GET /api/admin/metrics/`
* **Métricas Globales:** Total de fincas, lotes registrados, ciclos totales, ciclos en ejecución y distribución de roles del sistema.

---

### Ficha Técnica: RF-47 — Exportar reportes (PDF/Excel)
* **Actor:** Productor / Auditor.
* **Funcionalidad:** Descarga de reportes de trazabilidad consolidada y balances de liquidación en formatos portables estándar para presentación ante gremios arroceros (FEDEARROZ / Molinos).

---

# 4. ÉPICA EP-11: GESTIÓN DE USUARIOS Y SEGURIDAD

### Ficha Técnica: RF-48 — Registrar usuarios del sistema
* **Actor:** Usuario nuevo (Auto-registro) / Administrador.
* **Endpoint:** `POST /api/users/register/`
* **Campos:** `nombre_completo`, `email`, `password`, `rol` (`PRODUCTOR`, `TECNICO`, `ADMIN`).
* **Validaciones:**
  - Correo electrónico único en la base de datos (rechazo de duplicados HTTP 400).
  - Contraseña robusta (validadores de longitud mínima y similitud de Django).
  - Creación transaccional del modelo `User` junto con su `Perfil`.

---

### Ficha Técnica: RF-49 — Asignar roles (Productor, Técnico, Administrador)
* **Actor:** Administrador del sistema.
* **Modelos:** `User`, `Perfil`.
* **Regla de Negocio:** Cada perfil tiene un rol exclusivo:
  - `PRODUCTOR`: Administra sus propias fincas, lotes y ciclos.
  - `TECNICO`: Supervisa labores agronómicas, fitosanitarias e hídricas.
  - `ADMIN`: Gestión total de usuarios, métricas globales del sistema y auditoría.

---

### Ficha Técnica: RF-50 — Gestionar permisos de acceso
* **Actor:** Sistema SIG-ARROZ / Clases de Permisos DRF.
* **Clases Técnicas:** `IsAuthenticated`, `IsProductorOrTecnicoOrAdmin`, `IsAdminUserOnly`.
* **Mecanismo:** Validación del token JWT en cada solicitud HTTP vía cabecera `Authorization: Bearer <token>`.

---

### Ficha Técnica: RF-51 — Controlar acceso a la información según rol
* **Actor:** Sistema SIG-ARROZ.
* **Regla de Aislamiento:**
  - El productor `A` tiene estrictamente prohibido consultar o modificar fincas, lotes, ciclos o liquidaciones pertenecientes al productor `B` (filtro automático en `get_queryset` y excepción `PermissionDenied` en `perform_create`).
  - Los endpoints de administración (`/api/users-gestion/`, `/api/admin/metrics/`) son inaccesibles para productores y técnicos (código HTTP 403 Forbidden).
