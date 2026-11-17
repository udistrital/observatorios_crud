# PROY-ASIS-003 Campos, registros y documentos

## Identidad

| Campo | Valor |
|---|---|
| Sistema/estado | `observatorios_crud` / AS-IS |
| Referencia | `f51497c` + `PROY-TOBE-007/008`, 2026-11-11 |
| Evidencia | `osiris/apps/campos/`; `osiris/apps/datos/` |

## Objetivo y alcance

**Como** consumidor, **quiero** definir campos y registrar valores en una
estructura, **para** capturar datos tabulares o metadatos documentales.

Incluye catálogo de tipos, estructura, datos embebidos, alias `archivos`, vista
previa y visualización mediante referencia cifrada. Las rutas antiguas
`datos`/`datosArchivo` se documentan como legado, no como operativas.

## Requisitos y reglas

| ID | Requisito | Regla AS-IS |
|---|---|---|
| REQ-CAM-001 | Exponer tipos de campo. | BR-CAM-001: catálogo estático de 30 tipos. |
| REQ-CAM-002 | Consultar/actualizar definición. | BR-CAM-002: POST de colección responde 405; la estructura nace en otro recurso. |
| REQ-CAM-003 | Crear/listar registros. | BR-CAM-003: valores se almacenan en `data[]` por `campo_id`. |
| REQ-CAM-004 | Actualizar/desactivar/eliminar registro. | BR-CAM-004: ID externo es posición; PATCH solo cambia `activo`. |
| REQ-CAM-005 | Convertir Word/Excel a PDF temporal. | BR-CAM-005: multipart `archivo`, header Bearer sintáctico y validación de formato/límites. |
| REQ-CAM-006 | Conservar alias `archivos`. | BR-CAM-006: hereda el mismo JSON de datos; no carga bytes. |
| REQ-CAM-007 | Exponer rutas heredadas. | BR-CAM-007: [INFERIDO] fallan por API antigua de `EstructuraCamposModelo`. |
| REQ-CAM-008 | Admitir enlaces web. | BR-CAM-008: `link` usa mapping `keyword`; solo acepta URL HTTP(S) absoluta de máximo 2048 caracteres o `null`. |
| REQ-CAM-009 | Emitir referencia documental. | BR-CAM-009: POST exige cuatro IDs, Bearer sintáctico, cadena ES activa, un campo `hash` activo y una coincidencia activa exacta. |
| REQ-CAM-010 | Recuperar documento por referencia. | BR-CAM-010: GET descifra Fernet `v1_` con TTL de 604800 s, revalida ES y consulta el Gestor fijo con el Bearer reenviado. |

## Criterios

- **AC-CAM-001**: Dado un registro válido, cuando se hace POST, entonces retorna
  201 y aparece en `results`.
- **AC-CAM-002**: Dado un borrado por posición, cuando termina, entonces el arreglo
  pierde ese elemento y posiciones posteriores cambian.
- **AC-CAM-003**: Dado Word/Excel válido y capacidad disponible, cuando se solicita
  vista previa, entonces retorna PDF `inline` sin conservar temporales.
- **AC-CAM-004**: Dado un Bearer ausente, cuando se solicita vista previa, entonces
  retorna 401; esto no demuestra autenticación del token.
- **AC-CAM-005**: Dado un campo `link`, cuando se guarda un valor no HTTP(S), sin
  esquema o malformado, entonces retorna 400 con detalle asociado al campo.
- **AC-CAM-006**: Dado un contexto válido, el POST retorna 200 y `{referencia}`;
  entrada inválida retorna 400, Bearer inválido 401, asociación inválida 404,
  tasa 429 y dependencia/configuración 503.
- **AC-CAM-007**: Dada una referencia válida y asociación vigente, el GET retorna
  el JSON del Gestor con `private, no-store`, `no-cache` y `nosniff`; sus errores
  documentados son 401, 403, 404, 413, 429, 502, 503 y 504.

## Contratos, NFR y pruebas

Ver [`../api/openapi.yaml`](../api/openapi.yaml) y
[`../data/modelo-e-indices.md`](../data/modelo-e-indices.md). Existen 9 pruebas de
vista previa, pruebas unitarias/API de referencias documentales y 7 pruebas
unitarias del tipo Enlace en `apps/campos/tests.py`; la cobertura de registros
continúa limitada a su conversión pura. No se ejecutó una prueba end-to-end con
Elasticsearch y Gestor reales. [NO VERIFICADO]
Rendimiento con arreglos grandes, concurrencia y mappings reales.

## Riesgos

IDs inestables, `page_size` sin máximo, actualizaciones perdidas, alias confuso y
Bearer no validado. La referencia es transferible entre sesiones durante su TTL y
una credencial amplia conserva acceso directo al Gestor. `datosArchivo` no debe
reactivarse sin spec TO-BE y migración.
