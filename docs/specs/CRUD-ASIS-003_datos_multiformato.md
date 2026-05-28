# CRUD-ASIS-003 — Gestión de datos por estructura con formatos FORM/CSV/JSON

## Historia de Usuario (AS-IS)
**Como** usuario funcional del observatorio
**Quiero** registrar y consultar datos en múltiples formatos
**Para** mantener la información actualizada sin depender de un único mecanismo de carga.

## Criterios de aceptación funcionales
- Dado un formato soportado (FORM/CSV/JSON), cuando envío datos, entonces el sistema los procesa según reglas definidas.
- Dado una consulta paginada, cuando la ejecuto, entonces recibo resultados consistentes y navegables.

## 1. Contexto
El módulo `datos` permite listar, crear, actualizar y desactivar registros en índices dinámicos de Elasticsearch.

## 2. Problema
El comportamiento multiformato y de validación está en código, sin contrato funcional explícito para consumidores.

## 3. Objetivo
Especificar flujo AS-IS de operaciones de datos por estructura.

## 4. Alcance
### Incluye
- Resolución dinámica de índice por `estructura_id`.
- Carga por `FORM`, `CSV` y `JSON`.
- Paginación y filtros de consulta.
### Excluye (Fuera de alcance)
- Diseño de mappings en Elasticsearch.

## 5. Actores
- `observatorios_cliente`.
- `DatosViewSet`.
- Elasticsearch.

## 6. Flujo principal
1. API recibe request con `estructura_id`.
2. Resuelve índice asociado desde `EstructuraCamposModelo`.
3. Según `formato`, procesa payload y persiste en Elasticsearch.
4. Retorna resultado de indexación/bulk.

## 7. Flujos alternos / excepciones
- A1: JSON inválido retorna `400`.
- A2: Errores de validación de columnas retornan error estructurado.
- A3: Borrado lógico por `_activo=false`.

## 8. Reglas de negocio
- RN-01: Listados excluyen registros inactivos o sin campo `_activo`.
- RN-02: Tamaño máximo de página configurable hasta 10000.

## 9. Contratos técnicos
- Endpoint: `datos/<estructura_id>/` (GET/POST/DELETE).
- Endpoint: `datos/<estructura_id>/<pk>/` (GET/PUT/DELETE).
- Formatos soportados en creación: `FORM`, `CSV`, `JSON`.

## 10. Criterios de aceptación verificables
- [ ] `create` procesa al menos tres formatos declarados.
- [ ] `list` retorna paginación.
- [ ] `destroy` aplica desactivación lógica.

## 11. Dependencias
- `apps.elasticsearch_utils`
- `apps.campos.models.EstructuraCamposModelo`

## 12. Riesgos
- Acoplamiento fuerte a disponibilidad de Elasticsearch.
- Operaciones bulk sin políticas explícitas de reintento.

## 13. Pendientes
- Especificar errores estandarizados por tipo de formato.

## 14. Evidencia
- `observatorios_crud/osiris/apps/datos/views.py`

## 15. Clasificación SDD
- Tipo: AS-IS
- Tamaño relativo: L
- Prioridad: Alta
