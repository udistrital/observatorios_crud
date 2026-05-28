# Flujos funcionales y técnicos — observatorios_crud

## Flujo: CRUD de entidades de observatorios
### Objetivo
Gestionar creación, consulta, edición y desactivación de entidades del dominio.

### Actores involucrados
- `observatorios_cliente` (consumidor principal).
- API `observatorios_crud`.

### Flujo principal
1. Cliente invoca endpoint `api/v1/...`.
2. API valida request y permisos.
3. Ejecuta operación en Elasticsearch.
4. Devuelve respuesta estandarizada.

## Flujo: Sincronización de metadatos documentales
### Objetivo
Persistir referencia documental recibida vía `observatorios_mid`.

### Actores involucrados
- `observatorios_mid` (orquestador documental).
- `observatorios_crud`.

### Flujo principal
1. MID invoca endpoint de `datosArchivo`.
2. CRUD crea/actualiza documento de metadatos.
3. Se retorna identificador/estado para cierre del flujo en MID.

### Brechas
- Formalizar JSON contract de `datosArchivo` por versión.
- Definir catálogo común de errores funcionales y técnicos.
