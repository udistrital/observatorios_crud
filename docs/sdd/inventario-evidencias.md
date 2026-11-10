# Inventario de evidencias AS-IS

## Identidad de la inspección

| Campo | Valor |
|---|---|
| Repositorio | `observatorios_crud` |
| Rama local | `feature/campo_orden` |
| Commit | `3de996b166430ca180ab372fbabf69f4c12b419c` |
| Fecha | 2026-11-10 |
| Método | Revisión estática del checkout local; sin peticiones externas ni escrituras en Elasticsearch |

Las etiquetas `[VERIFICADO]`, `[INFERIDO]`, `[NO VERIFICADO]`, `[PROPUESTA]` y
`[NO APLICA]` expresan el nivel de evidencia. El commit identifica el código; los
cambios documentales sin commit se describen en el informe de entrega.

## Cobertura

- [VERIFICADO] 33 plantillas de ruta de dominio y 90 combinaciones
  `método + ruta` explícitas bajo `/api/{version}/`.
- [VERIFICADO] 1 operación de salud y 4 rutas de documentación Swagger/ReDoc.
- [VERIFICADO] El segmento `{version}` acepta cualquier cadena; no existe una lista
  de versiones admitidas (`osiris/osiris/urls.py: urlpatterns`).
- [VERIFICADO] El inventario operación por operación está en
  [`../api/openapi.yaml`](../api/openapi.yaml).
- [NO VERIFICADO] No se ejecutaron las operaciones contra una instancia real de
  Elasticsearch; "detectado" no equivale a "operativo".

## Inventario por capacidad

| ID | Capacidad | Rutas | Operaciones | Implementación y evidencia | Consumidor observado | Estado |
|---|---|---:|---:|---|---|---|
| CRUD-MOD-001 | Observatorios e imágenes | 2 | 5 | `osiris/apps/observatorios/{urls.py,views.py,serializers.py,models.py}` | Administración del cliente | [VERIFICADO] |
| CRUD-MOD-002 | Procesos | 2 | 6 | `osiris/apps/procesos/{urls.py,views.py,serializers.py}` | `procesos.service.js`, `Espacios.vue` | [VERIFICADO] |
| CRUD-MOD-003 | Factores | 2 | 6 | `osiris/apps/factores/{urls.py,views.py,serializers.py}` | `factores.service.js`, `ProcesoFactores.vue` | [VERIFICADO] |
| CRUD-MOD-004 | Características | 2 | 6 | `osiris/apps/caracteristicas/{urls.py,views.py,serializers.py}` | `caracteristicas.service.js` | [VERIFICADO] |
| CRUD-MOD-005 | Aspectos | 2 | 6 | `osiris/apps/aspectos/{urls.py,views.py,serializers.py}` | `aspectos.service.js`, `AspectosSection.vue` | [VERIFICADO] |
| CRUD-MOD-006 | Estructuras de evidencia | 2 | 6 | `osiris/apps/estructuras/{urls.py,views.py,serializers.py}` | `estructuras-evidencias.service.js` | [VERIFICADO] |
| CRUD-MOD-007 | Campos, registros, alias de archivos y vista previa | 8 | 28 | `osiris/apps/campos/{urls.py,views.py,serializers.py,utils.py}` | `campos.service.js`, `Tablero.vue`, `DocumentoVisor.vue` | [VERIFICADO] con anomalías descritas abajo |
| CRUD-MOD-008 | Datos multiformato y `datosArchivo` heredados | 4 | 12 | `osiris/apps/datos/{urls.py,views.py}` | MID y componentes `archivos/` legados | [INFERIDO] no operativo |
| CRUD-MOD-009 | Dashboards y gráficos persistidos | 5 | 11 | `osiris/apps/dashboards/{urls.py,views.py}` | Componentes `panel/` | [VERIFICADO] salvo construcción de gráfico |
| CRUD-MOD-010 | Constructor de gráficos | 4 | 4 | `osiris/apps/graficos/{urls.py,views.py}` | Componentes `panel/graficas/` | [VERIFICADO] rutas; [INFERIDO] ejecución parcial rota |

## Hallazgos de contrato

| ID | Hallazgo | Evidencia | Consecuencia |
|---|---|---|---|
| CRUD-EV-001 | La API funcional usa Elasticsearch directamente; no hay modelos Django de dominio. | `osiris/apps/elasticsearch_utils/models.py: ModeloElasticSearch`; `osiris/apps/*/models.py` | Las migraciones SQL no describen el dominio. |
| CRUD-EV-002 | No se configuran autenticación ni permisos globales DRF y las vistas de dominio no declaran permisos. | `osiris/osiris/settings.py: REST_FRAMEWORK`; `osiris/apps/*/views.py` | [INFERIDO] se aplican defaults DRF y las rutas quedan `AllowAny`; debe comprobarse también el gateway. |
| CRUD-EV-003 | La vista previa solo comprueba que `Authorization` empiece por `Bearer ` y contenga texto. | `osiris/apps/campos/views.py: VistaPreviaDocumentoView` | No prueba identidad, firma, expiración ni rol. |
| CRUD-EV-004 | `datos` y `datosArchivo` llaman miembros que el modelo actual no define. | `osiris/apps/datos/views.py: DatosViewSet.initial, DatosArchivoViewSet.initial`; `osiris/apps/campos/models.py: EstructuraCamposModelo` | [INFERIDO] fallan antes del handler útil. |
| CRUD-EV-005 | Parte del constructor de gráficos usa la misma API antigua. | `osiris/apps/dashboards/views.py: GraficoViewSet.construir`; `osiris/apps/graficos/views.py` | [INFERIDO] `campos_sugeridos`, `probar_configuracion` y `construir` no completan una entrada válida. |
| CRUD-EV-006 | Los IDs de registros embebidos son posiciones del arreglo `data`. | `osiris/apps/campos/views.py: DatosEstructuraDocumentoView` | Eliminar una posición renumera los registros posteriores. |
| CRUD-EV-007 | Las relaciones padre-hijo se actualizan en operaciones Elasticsearch separadas. | `views.py` de factores, características, aspectos y estructuras | Puede quedar estado parcial; no hay transacción distribuida. |
| CRUD-EV-008 | Los errores no tienen una única forma. | `osiris/apps/utils/views.py: custom_exception_handler`; respuestas manuales en `apps/*/views.py` | El cliente debe tratar `detail`, `error`, `detalle`, `message` y fallos sin cuerpo uniforme. |

## Pruebas encontradas

| Área | Evidencia | Casos | Estado |
|---|---|---:|---|
| Vista previa Office | `osiris/apps/campos/tests.py` | 9 métodos | [VERIFICADO] existen; [NO VERIFICADO] ejecución en esta inspección |
| Observatorios | `osiris/apps/observatorios/tests/test_views.py` | 2 métodos | [VERIFICADO] existen; requieren Elasticsearch |
| Otras aplicaciones | `osiris/apps/*/tests.py` | Archivos vacíos o ausentes | [VERIFICADO] sin cobertura ejecutable identificada |

## Documentación previa y vigencia

| Artefacto | Estado |
|---|---|
| `swagger/swagger.yml` y `swagger/swagger.json` | [VERIFICADO] Swagger 2 histórico y divergente; no es fuente canónica AS-IS. |
| `docs/specs/CRUD-ASIS-*` | [VERIFICADO] conservado por trazabilidad; algunos documentos describen rutas heredadas como operativas. |
| `docs/sdd/matriz_interacciones.md` | [VERIFICADO] matriz canónica de integraciones, actualizada para distinguir activo y legado. |
| `docs/api/openapi.yaml` | [VERIFICADO] inventario contractual AS-IS generado por inspección; su validación se registra en diferencias de contrato. |

## Pendientes de verificación dinámica

- [NO VERIFICADO] Mappings e índices existentes en cada ambiente.
- [NO VERIFICADO] Controles de autenticación o autorización aplicados por gateway,
  ingress o WAF.
- [NO VERIFICADO] Compatibilidad real de los índices creados con Elasticsearch
  desplegado.
- [NO VERIFICADO] Recuperación, backup, retención y capacidad operativa.
- [NO VERIFICADO] Respuestas generadas por drf-yasg en un servidor iniciado.
