# Historia de Usuario
Como equipo de desarrollo de `observatorios_crud`,
quiero un conjunto de reglas operativas para agentes de IA,
para generar codigo nuevo consistente con las convenciones del repositorio y reducir retrabajos funcionales y tecnicos.

## Criterios de aceptación funcionales
1. Debe existir una guia unica con reglas de desarrollo para agentes de IA orientada a Django/DRF del proyecto.
2. La guia debe priorizar valor funcional (actor, resultado esperado, impacto) antes de detalles de implementacion.
3. Toda propuesta de codigo generada por agentes debe respetar estructura `apps/*`, versionamiento de rutas y la convención de entorno basada en `PARAMETER_STORE`.
4. La guia debe incluir validaciones minimas de seguridad y despliegue para `test/prod`.
5. Debe incluir evidencia de convenciones del repositorio y soporte en documentacion oficial (Context7).

---

## Problema funcional
Existen lineamientos tecnicos historicos de API Django, pero no estaban integrados de forma operativa en una unica guia para **agentes de IA** con reglas accionables para crear codigo nuevo sin romper convenciones locales del CRUD.

## Objetivo del usuario
Estandarizar la salida de agentes de IA para que cualquier cambio nuevo:
- sea coherente con la arquitectura actual,
- minimice contradicciones entre codigo y documentacion,
- y facilite pruebas/local-run y despliegue.

## Impacto institucional
- Menos retrabajo en PR y revisiones.
- Menor riesgo de cambios inseguros en `test/prod`.
- Mejor trazabilidad entre requerimiento funcional y entrega tecnica.

---

## Reglas de desarrollo para agentes de IA (AS-IS vigente)

### 1) Regla de entrada funcional (obligatoria)
Antes de escribir codigo, el agente debe declarar:
1. Actor funcional afectado.
2. Resultado esperado del endpoint/flujo.
3. Evidencia de contrato impactado (ruta, payload, codigos HTTP).

Si no hay evidencia suficiente, marcar como **INFERENCIA**.

### 2) Estructura de proyecto (Django apps)
- Mantener organizacion por dominio dentro de `osiris/apps/`.
- Ubicar cambios en archivos esperados por app: `models.py`, `views.py`, `serializers.py`, `urls.py`, `tests.py`.
- Registrar app en `INSTALLED_APPS` solo si es nueva.

Subreglas obligatorias por app (integradas desde lineamientos internos):
- `models.py`: definir modelo y metadatos de persistencia.
- `serializers.py`: mapear entrada/salida y validaciones de campos/objeto.
- `views.py`: preferir `ViewSet` para CRUD y `@action` para casos no estandar.
- `urls.py`: exponer rutas con router o `path()` manteniendo versionamiento global.
- `tests.py`: incluir pruebas minimas de flujo feliz y validaciones.
- `migrations/`: generar y versionar migraciones cuando cambia el modelo.
- `permissions.py`, `filters.py`, `signals.py`: solo cuando el caso lo requiera, evitando complejidad innecesaria.

**Evidencia local:** lineamientos historicos de API Django del repositorio.

### 3) Convenciones de API y rutas
- Respetar versionamiento actual bajo `/api/<str:version>/...`.
- Mantener endpoints documentables por Swagger (`drf_yasg`).
- En DRF, preferir `ViewSet` + serializer explicito y respuestas consistentes.
- Cuando aplique enrutamiento CRUD, usar router de DRF para reducir errores de wiring.
- Si el endpoint requiere logica de negocio adicional, ubicarla en capa de servicio/utilidad y no incrustarla completamente en el serializer.

**Evidencia local:** `osiris/osiris/urls.py` y apps `*/urls.py`.

### 4) Regla de configuracion por entorno
- Usar un solo `osiris/.env` y `PARAMETER_STORE` para distinguir local vs entornos con secretos en SSM.
- Local (sin `PARAMETER_STORE`): credenciales ES desde variables de entorno (`ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`).
- Remoto (con `PARAMETER_STORE`): credenciales ES vía AWS SSM.
- No hardcodear secretos ni hostnames de produccion.

### 5) Regla de seguridad minima
Para cambios en configuracion:
- `DEBUG=False` en `test/prod`.
- `ALLOWED_HOSTS` no vacio en `test/prod`.
- Cookies seguras y redireccion SSL en `test/prod` segun politica del repo.
- Ejecutar validacion de despliegue Django.
- Gestionar `SECRET_KEY` solo por entorno (sin hardcode en codigo fuente).

### 6) Regla de datos y Elasticsearch
- Usar `ELASTICSEARCH_MAIN_INDEX` como prefijo canonico.
- Evitar indices hardcodeados por app.
- Validar compatibilidad de cambios con utilidades de `apps/elasticsearch_utils`.

### 7) Regla de pruebas y verificacion
Todo cambio de agente debe proponer minimo:
1. prueba funcional del endpoint afectado,
2. verificacion de arranque local (`./run_crud.sh`),
3. validacion Django (`manage.py check`).
4. para cambios de despliegue/seguridad: `manage.py check --deploy` en contexto de `test/prod`.

Para pruebas API en DRF:
- Preferir `APIClient` para pruebas end-to-end del endpoint.
- Usar validaciones de serializer (`validate_<field>()` y `validate()`) para reglas de negocio de datos.

### 8) Regla de no regresion documental
Si cambia:
- contrato de endpoint,
- variable de entorno,
- o flujo de ejecucion,
el agente debe actualizar `README.md` y/o `docs/specs/*` en el mismo cambio.

### 9) Regla obligatoria de ciclo SDD (AS-IS / TO-BE)
Para estandarizar requerimientos nuevos, todo agente de IA debe seguir este flujo:
1. Registrar el requerimiento en `docs/specs/backlog_specs.md` con ID `CRUD-TOBE-XXX`.
2. Crear o actualizar la especificacion objetivo en `docs/specs/CRUD-TOBE-XXX_nombre.md`.
3. Implementar el cambio en codigo.
4. Actualizar la especificacion de estado actual afectada en `docs/specs/CRUD-ASIS-XXX_nombre.md`.
5. Si cambia operacion local o contratos, actualizar tambien `README.md` y referencias en `docs/`.

Criterio de uso:
- **TO-BE**: requerimiento nuevo o cambio objetivo.
- **AS-IS**: comportamiento implementado y vigente.

---

## Soporte técnico (Context7 + evidencia)

### A. Django (Context7)
Documentacion consultada via Context7 `/django/django/4.2.21`:
- Uso de `manage.py check --deploy` para validaciones de despliegue.
- Recomendacion de `DEBUG=False` en despliegue.
- `ALLOWED_HOSTS` obligatorio y no vacio en produccion.
- Manejo de `SECRET_KEY` desde entorno.
- Configuracion de `STATIC_ROOT/STATIC_URL` y `MEDIA_ROOT/MEDIA_URL` para despliegue.
- Recomendacion de `collectstatic` para publicacion de estaticos.

### B. DRF (Context7)
Documentacion consultada via Context7 `/encode/django-rest-framework`:
- Patron de `ViewSet` + serializer.
- Enrutamiento con `DefaultRouter`/routers por app.
- Uso de `@action` para operaciones no CRUD estandar.
- Permisos personalizados con `BasePermission`.
- Validaciones de serializer a nivel de campo y objeto.
- Pruebas de API con `APIClient`/`APIRequestFactory` cuando aplique.

### C. Evidencia en repositorio
- `osiris/osiris/settings.py` (PARAMETER_STORE/USE_SSM, seguridad, ES).
- `run_crud.sh` (arranque API local).
- `infraestructura/run_infra.sh` (stack local opcional).

---

## Dependencias y compatibilidad
- Framework principal: Django 4.2.x.
- API framework: Django REST Framework.
- Documentacion OpenAPI: drf-yasg.
- Infra local opcional: Docker Compose (Elastic/Kibana/Nginx).

---

## Riesgos y controles
1. **Riesgo:** generar codigo con supuestos de entorno incorrectos.
   - **Control:** validar `PARAMETER_STORE` y variables requeridas antes de proponer cambios.
2. **Riesgo:** romper contratos API existentes.
   - **Control:** declarar endpoint impactado y pruebas de no regresion.
3. **Riesgo:** introducir configuraciones inseguras en `test/prod`.
   - **Control:** checklist de seguridad Django y `check --deploy`.

---

## Contradicciones y brechas identificadas
- **INFERENCIA:** En varios componentes se importa `ELASTICSEARCH_MAIN_INDEX` directamente desde `osiris.settings`; una futura refactorizacion de settings debe preservar este contrato interno para evitar roturas transversales.
- Persisten advertencias de Docker Compose por atributo `version` obsoleto; no bloquea ejecucion, pero conviene normalizar.
