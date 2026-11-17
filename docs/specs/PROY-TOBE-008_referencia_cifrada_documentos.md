# PROY-TOBE-008 Referencia cifrada y validación documental

## Identidad

| Campo | Valor |
|---|---|
| Sistema dueño | `observatorios_crud` |
| Estado | implementado; cobertura unitaria y checks ejecutados |
| Referencia | `develop@f51497c` + cambios locales, 2026-11-11 |
| Reemplaza | Consulta directa Cliente → Gestor solo para visualización |

## Contexto y objetivo

**Como** usuario autenticado de ATLAS, **quiero** que el CRUD valide la
pertenencia de un documento antes de recuperarlo, **para** impedir que un UUID
manipulado permita consultar archivos ajenos a la estructura seleccionada.

El flujo anterior usaba el UUID del Gestor en `/documentos/:hash` y consultaba al
Gestor desde el navegador. La implementación mantiene el visor, usa el parámetro
`:referencia` y reemplaza el hash visible por una referencia cifrada emitida y
consumida por el CRUD.

## Alcance

### Incluye

- `POST /api/{version}/campos/documentos/referencias/`.
- `GET /api/{version}/campos/documentos/{referencia}/`.
- Validación repetida de proceso, factor, característica, aspecto, estructura
  Documental activa y valor exacto del campo `hash` en un registro activo.
- Cifrado autenticado URL-safe, versionado y con vencimiento.
- Passthrough del JSON original del Gestor para conservar nombre, MIME y base64;
  primero completa un spool temporal y luego sirve el 200.

### Excluye

- Cambios de carga, reemplazo o eliminación de archivos.
- Cifrado del valor `hash` persistido o eliminación del hash en respuestas de datos.
- Cambios en Nuxeo, Gestor Documental, mappings o migraciones SQL.

## Requisitos funcionales

| ID | Requisito verificable | Prioridad |
|---|---|---|
| REQ-DOC-001 | Emitir referencia solo si el archivo pertenece al contexto proceso/factor/estructura. | Alta |
| REQ-DOC-002 | Cifrar proceso, factor, estructura y documento con integridad autenticada. | Alta |
| REQ-DOC-003 | Repetir toda la validación Elasticsearch al solicitar contenido. | Alta |
| REQ-DOC-004 | No invocar al Gestor si token, jerarquía o asociación fallan. | Alta |
| REQ-DOC-005 | Reenviar el Bearer y transmitir la respuesta compatible con el visor. | Alta |

## Reglas de negocio

| ID | Regla |
|---|---|
| BR-DOC-001 | La estructura debe coincidir con `atlas_estructura_documental_<uuid>` y estar activa. |
| BR-DOC-002 | La cadena hija `estructura.aspecto_id → caracteristica_id → factor_id → proceso_id` debe coincidir exactamente con los IDs solicitados. |
| BR-DOC-003 | Debe existir un único campo activo `hash` y exactamente un registro activo con el documento solicitado. |
| BR-DOC-004 | La referencia usa una clave Fernet aleatoria, prefijo `v1_`, sin padding visible y TTL de 604800 segundos (7 días). |
| BR-DOC-005 | Ambas operaciones requieren la sintaxis exacta `Authorization: Bearer <token-sin-espacios>`; no validan JWT, identidad, expiración, rol ni ACL por proceso. |
| BR-DOC-006 | El GET solo consulta `GESTOR_DOCUMENTAL/document/{documento_id}`, reenvía el Bearer y deja la autorización efectiva al Gestor. |
| BR-DOC-007 | `documento_id` debe ser un UUID canónico; segmentos de ruta y otros identificadores se rechazan antes de consultar Elasticsearch o Gestor. |

## Criterios de aceptación

- **AC-DOC-001**: Dado un documento asociado, cuando se solicita una referencia,
  entonces el CRUD responde un token opaco que no contiene el UUID legible.
- **AC-DOC-002**: Dado un token válido, cuando el documento continúa asociado,
  entonces el CRUD consulta al Gestor y transmite su respuesta.
- **AC-DOC-003**: Dado otro proceso, factor o estructura, cuando se solicita o usa
  la referencia, entonces responde 404 y no consulta al Gestor.
- **AC-DOC-004**: Dado un token manipulado o vencido, entonces responde 403 y no
  consulta al Gestor.
- **AC-DOC-005**: Dado que el registro fue eliminado o desactivado después de
  emitir la referencia, entonces la recuperación responde 404.

## Contratos e integraciones

Solicitud de referencia:

```json
{
  "proceso_id": "ID_PROCESO",
  "factor_id": "ID_FACTOR",
  "estructura_id": "ID_ESTRUCTURA",
  "documento_id": "ID_ARCHIVO"
}
```

Respuesta 200: `{ "referencia": "v1_<cifrado>" }`.

El POST responde 200, 400, 401, 404, 429 o 503. El GET transmite el JSON del
Gestor que contiene `file`, `file:content.name`, `file:content.mime-type` y/o
`dc:title`; responde 200, 401, 403 por referencia inválida/vencida o rechazo
upstream, 404, 413, 429, 502, 503 o 504.

## Requisitos no funcionales

- Clave Fernet real en `DOCUMENT_REFERENCE_KEY`; nunca se retorna ni se registra,
  no tiene valor predeterminado y una cadena vacía o inválida se rechaza.
- URL del Gestor fija en `GESTOR_DOCUMENTAL`; el cliente no controla el destino.
- HTTPS obligatorio en producción, TLS verificado, redirects deshabilitados,
  timeout de lectura y plazo upstream total, concurrencia acotada hasta cerrar la
  respuesta y límite de bytes con spool temporal en disco.
- El GET 200 incluye `Cache-Control: private, no-store`, `Pragma: no-cache` y
  `X-Content-Type-Options: nosniff`.
- Producción usa Gunicorn `gthread`, 2 workers por 4 threads y timeout 240 s. La
  concurrencia predeterminada del proxy es 2 por proceso.

## Riesgos y decisiones

- [VERIFICADO] El CRUD actual no valida criptográficamente el Bearer ni define ACL
  por proceso. Esta entrega exige su presencia y lo reenvía al Gestor/gateway,
  conservando los permisos existentes, pero no crea una política institucional.
- La referencia es transferible entre sesiones autenticadas mientras no venza;
  cifrar los IDs no la convierte en autorización.
- El hash continúa en la respuesta del registro porque edición y eliminación
  existentes aún lo consumen; no aparece en la ruta del visor.
- El Gestor puede seguir siendo consultado directamente por una credencial con
  alcance excesivo. Se registra como riesgo residual y no se modifica en esta tarea.

## Pruebas y convergencia

`ReferenciaDocumentoTests` cubre cifrado, expiración, token manipulado, UUID,
jerarquía cruzada, asociaciones ambiguas/inactivas, Bearer, upstream, límites,
plazo total, ciclo del cupo y garantía API de no invocar al Gestor en rechazos.
`apps.campos` ejecutó 47 casos y `manage.py check` no reportó problemas. La suite
global conserva dos fallos ajenos porque el usuario Elasticsearch local no puede
crear `test_observatorios`. No se verificó el flujo end-to-end contra servicios
reales.
