# Flujos funcionales y técnicos — observatorios_crud

> Estado: resumen. Las secuencias verificadas y limitaciones están en
> [`sdd/arquitectura-as-is.md`](sdd/arquitectura-as-is.md).

## Flujo: CRUD de entidades de observatorios
### Objetivo
Gestionar creación, consulta, edición y desactivación de entidades del dominio.

### Actores involucrados
- `observatorios_cliente` (consumidor principal).
- API `observatorios_crud`.

### Flujo principal
1. Cliente invoca endpoint `api/v1/...`.
2. API valida request; [VERIFICADO] no hay permisos de dominio globales.
3. Ejecuta operación en Elasticsearch.
4. Devuelve una respuesta cuya forma depende del handler; no existe un formato único de error.

## Flujo activo: metadatos documentales
### Objetivo
Persistir metadatos y hash enviados directamente por `observatorios_cliente`.

### Actores involucrados
- `observatorios_cliente` (orquesta Gestor Documental y CRUD).
- `observatorios_crud`.

### Flujo principal
1. El cliente carga el binario al Gestor Documental.
2. El cliente invoca `/campos/datos/{estructura}/` con metadatos y hash.
3. CRUD actualiza `data` de la estructura y responde al cliente.

### Brechas
- `datosArchivo` permanece como ruta heredada y [INFERIDO] no operativa.
- El contrato de errores sigue siendo heterogéneo.
