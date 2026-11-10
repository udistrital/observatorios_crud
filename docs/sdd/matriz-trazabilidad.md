# Matriz de trazabilidad AS-IS

## Convención

La matriz relaciona comportamiento observado, no requisitos institucionales
aprobados. Los `REQ-ASIS-*`, `BR-ASIS-*` y `AC-ASIS-*` son identificadores
documentales estables para localizar evidencia y pruebas.

| REQ-ID | Caso de uso | Regla y AC observable | Endpoint/capacidad | Fuente | Prueba existente | Estado y riesgo |
|---|---|---|---|---|---|---|
| REQ-ASIS-CRUD-001 | Gestionar procesos | BR-001 ordena por `orden,nombre`; AC-001 listar retorna arreglo | `/procesos/`, `/procesos/{id}/` | `apps/procesos/views.py` | No identificada | [VERIFICADO], sin cobertura |
| REQ-ASIS-CRUD-002 | Asociar factores a proceso | BR-002 actualiza hijo y referencia del padre; AC-002 proceso inexistente no crea relación válida | `/factores/*` | `apps/factores/views.py` | No identificada | [VERIFICADO], no transaccional |
| REQ-ASIS-CRUD-003 | Gestionar características | BR-003 exige factor; AC-003 filtra por `factor_id` | `/caracteristicas/*` | `apps/caracteristicas/views.py` | No identificada | [VERIFICADO] |
| REQ-ASIS-CRUD-004 | Gestionar aspectos | BR-004 admite referencias de estructura `Documental` o `Tabla`; AC-004 filtra por característica | `/aspectos/*` | `apps/aspectos/views.py` | No identificada | [VERIFICADO] |
| REQ-ASIS-CRUD-005 | Crear estructura | BR-005 crea índice dinámico y referencia; AC-005 éxito devuelve estructura y referencias | `/estructuras-evidencias/*` | `apps/estructuras/views.py` | No identificada | [VERIFICADO], compensación parcial |
| REQ-ASIS-CRUD-006 | Definir campos | BR-006 campo usa ID, orden, nombre y tipo; AC-006 GET recupera documento de estructura | `/campos/estructuras/*` | `apps/campos/views.py`, `utils.py` | No identificada | [VERIFICADO] |
| REQ-ASIS-CRUD-007 | Capturar registros | BR-007 registro se embebe y su ID es posición; AC-007 POST retorna 201 | `/campos/datos/*` | `apps/campos/views.py: DatosEstructuraDocumentoView` | No identificada | [VERIFICADO], ID inestable |
| REQ-ASIS-CRUD-008 | Convertir Office a vista previa | BR-008 acepta Word/Excel validado y retorna PDF; AC-008 temporales se eliminan | `/campos/archivos/vista-previa/` | `apps/campos/views.py: VistaPreviaDocumentoView` | `apps/campos/tests.py` | [VERIFICADO], Bearer no autenticado |
| REQ-ASIS-CRUD-009 | Gestionar observatorios | BR-009 DELETE desactiva; AC-009 crear imagen retorna 201 | `/observatorios/*` | `apps/observatorios/views.py` | `apps/observatorios/tests/` | [VERIFICADO] |
| REQ-ASIS-CRUD-010 | Gestionar dashboards | BR-010 dashboard deriva índice de gráficos; AC-010 filtra por observatorio | `/dashboards/*` | `apps/dashboards/views.py` | No identificada | [VERIFICADO] |
| REQ-ASIS-CRUD-011 | Configurar y construir gráficos | BR-011 configuración depende de tipo; AC-011 catálogo expone tipos | `/graficos/*`, `/constructor_graficos/*` | `apps/dashboards/views.py`, `apps/graficos/views.py` | No identificada | [INFERIDO] ejecución parcial rota |
| REQ-ASIS-CRUD-012 | Cargar datos heredados | BR-012 pretende `FORM`, CSV o JSON; AC-012 no reproducido | `/datos/*`, `/datosArchivo/*` | `apps/datos/views.py` | No identificada | [INFERIDO] no operativo |

## Trazabilidad cruzada

| Integración | Requisito relacionado | Consumidor | Evidencia |
|---|---|---|---|
| Cliente a CRUD | REQ-001 a REQ-011 | Servicios y componentes Vue | [`matriz_interacciones.md`](matriz_interacciones.md) |
| Cliente a Gestor y luego CRUD | REQ-007 | `Tablero.vue` | Repositorio cliente, `src/service/gestorDocumentalService.js` |
| MID a `datosArchivo` | REQ-012 | `observatorios_mid` | `services/observatorios_service.py`; estado legado |

## Vacíos

- [VERIFICADO] Solo REQ-008 y parte de REQ-009 tienen pruebas identificadas.
- [NO VERIFICADO] No hay cobertura, rendimiento, disponibilidad o límites
  institucionales medidos.
- [PROPUESTA] Una evolución debe crear IDs TO-BE nuevos, enlazar AC con pruebas y
  registrar convergencia; no debe cambiar el significado de estos IDs AS-IS.
