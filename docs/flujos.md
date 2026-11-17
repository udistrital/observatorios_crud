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

## Flujo activo: visualización documental validada

1. El tablero envía proceso, factor, estructura y documento a
   `/campos/documentos/referencias/` con Bearer.
2. CRUD valida la cadena activa y una única coincidencia `hash`, y retorna una
   referencia Fernet `v1_` efímera.
3. El visor abre `/documentos/{referencia}` y consulta
   `/campos/documentos/{referencia}/`.
4. CRUD descifra con TTL, revalida Elasticsearch y consulta el GET fijo del Gestor
   con el Bearer reenviado.
5. CRUD completa el spool temporal, resuelve errores y solo entonces retorna 200.

El Bearer se comprueba solo sintácticamente; no hay JWT ni ACL por proceso. La
referencia es transferible durante el TTL y el Gestor decide los permisos efectivos
del Bearer. El MID y los componentes legados no participan en este flujo.
