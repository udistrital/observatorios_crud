# PROY-TOBE-007 Tipo de campo Enlace

## Identidad

| Campo | Valor |
|---|---|
| Sistema dueño | `observatorios_crud` |
| Estado | aprobado para implementación |
| Referencia | `feature/documentacion_spec_driven@1ad6ef3`, 2026-11-11 |
| Reemplaza | `[NO APLICA]` |

## Contexto y objetivo

**Como** administrador de una estructura tipo Tabla, **quiero** definir campos
de tipo Enlace, **para** registrar direcciones web que el cliente pueda presentar
como vínculos navegables seguros.

El contrato vigente solo admite tipos nativos de Elasticsearch. La evolución
agrega el tipo semántico `link`, respaldado por un mapping `keyword`.

## Alcance

### Incluye

- Catálogo y validación del tipo `link`.
- Conversión de valores vacíos a `null` y validación de URL absoluta HTTP(S).
- Mapping Elasticsearch `keyword` para valores de enlace.
- Compatibilidad con alta, actualización, consulta, ordenamiento y filtros de
  registros existentes.

### Excluye

- Detección o conversión automática de columnas `text` que contengan URLs.
- Protocolos distintos de `http` y `https`.
- Solicitudes automáticas a la URL almacenada.

## Requisitos funcionales

| ID | Requisito verificable | Fuente/prioridad |
|---|---|---|
| REQ-LINK-001 | `GET /campos/tipos` incluye `{ "label": "Enlace", "value": "link" }`. | Alta |
| REQ-LINK-002 | La definición de campos acepta `tipo_campo: "link"`. | Alta |
| REQ-LINK-003 | POST/PUT de registros aceptan enlaces HTTP(S) absolutos y valores vacíos. | Alta |
| REQ-LINK-004 | POST/PUT rechazan sin esquema, URL inválida, protocolo no permitido o longitud mayor a 2048. | Alta |
| REQ-LINK-005 | Elasticsearch recibe mapping `keyword` para un campo `link`. | Alta |

## Reglas de negocio

| ID | Regla | Fuente |
|---|---|---|
| BR-LINK-001 | El valor persistido es una cadena URL sin espacios exteriores. | Decisión de esta entrega |
| BR-LINK-002 | Solo se permiten esquemas explícitos `http://` y `https://`. | Seguridad |
| BR-LINK-003 | Un valor vacío es opcional y se persiste como `null`. | Compatibilidad actual |
| BR-LINK-004 | Cambiar manualmente un tipo usa la migración vigente; no se inspeccionan columnas para inferir enlaces. | Alcance solicitado |

## Escenarios

- Un administrador crea un campo `link` y registra `https://example.org/ruta`;
  el valor se conserva y se consulta con el resto del registro.
- Un registro omite el enlace; la API guarda `null`.
- Un consumidor envía `javascript:alert(1)`, `www.example.org` o una URL
  malformada; la API responde 400 con el detalle asociado al campo.

## Criterios de aceptación

- **AC-LINK-001**: Dado un campo `link`, cuando se guarda una URL HTTP(S)
  absoluta, entonces el registro se crea o actualiza sin alterar la dirección.
- **AC-LINK-002**: Dado un protocolo no permitido o una URL sin esquema,
  cuando se guarda el registro, entonces la API responde 400.
- **AC-LINK-003**: Dado un campo `link`, cuando se actualiza su mapping,
  entonces Elasticsearch recibe `type: keyword` y no `type: link`.
- **AC-LINK-004**: Dadas estructuras y columnas existentes, cuando se despliega
  el cambio, entonces no se convierten automáticamente campos `text`.

## Contratos e integraciones

No se crean rutas ni se modifican formas de respuesta. Se amplía el valor
admitido de `tipo_campo` y el catálogo de `GET /api/{version}/campos/tipos`.
Los errores de valor conservan HTTP 400 y la forma
`{ "detalle": { "<campo>": "<mensaje>" } }`. El consumidor coordinado es
`observatorios_cliente` mediante `/campos/estructuras/` y `/campos/datos/`.

## Requisitos no funcionales

- Validación obligatoria en servidor; la validación del cliente no es frontera
  de seguridad.
- No resolver, descargar ni previsualizar la URL.
- Mantener paginación, búsqueda y ordenamiento manual existentes.

## Pruebas y evidencia

- Pruebas unitarias propuestas en `osiris/apps/campos/tests.py` para catálogo,
  mapping, valores válidos, vacío y rechazos.
- Verificación prevista: `python manage.py test apps.campos` y
  `python manage.py check`.

## Riesgos, dudas y decisiones

- La migración vigente convierte valores inválidos a `null`; solo se ejecuta
  ante un cambio manual de tipo que envíe `migrar_data: true`.
- No hay migración SQL ni barrido de documentos existentes.

## Convergencia

Implementado el 2026-11-11 junto con cliente `PROY-TOBE-008`. Se actualizaron
OpenAPI, modelo de índices, AS-IS, matrices y pruebas. Evidencia:

- `python manage.py test apps.campos`: 16 pruebas aprobadas en entorno virtual
  temporal con `osiris/requirements.txt`.
- `python manage.py check`: sin problemas.
- `docs/api/openapi.yaml`: parseo YAML correcto.

[NO VERIFICADO] No se ejecutó una prueba de mapping contra una instancia
Elasticsearch real; el mapping unitario esperado es `{ "type": "keyword" }`.
