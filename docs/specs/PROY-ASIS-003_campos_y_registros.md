# PROY-ASIS-003 Campos, registros y vista previa

## Identidad

| Campo | Valor |
|---|---|
| Sistema/estado | `observatorios_crud` / AS-IS |
| Referencia | `3de996b`, 2026-11-10 |
| Evidencia | `osiris/apps/campos/`; `osiris/apps/datos/` |

## Objetivo y alcance

**Como** consumidor, **quiero** definir campos y registrar valores en una
estructura, **para** capturar datos tabulares o metadatos documentales.

Incluye catálogo de tipos, estructura, datos embebidos, alias `archivos` y vista
previa. Las rutas antiguas `datos`/`datosArchivo` se documentan como legado, no
como operativas.

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

## Criterios

- **AC-CAM-001**: Dado un registro válido, cuando se hace POST, entonces retorna
  201 y aparece en `results`.
- **AC-CAM-002**: Dado un borrado por posición, cuando termina, entonces el arreglo
  pierde ese elemento y posiciones posteriores cambian.
- **AC-CAM-003**: Dado Word/Excel válido y capacidad disponible, cuando se solicita
  vista previa, entonces retorna PDF `inline` sin conservar temporales.
- **AC-CAM-004**: Dado un Bearer ausente, cuando se solicita vista previa, entonces
  retorna 401; esto no demuestra autenticación del token.

## Contratos, NFR y pruebas

Ver [`../api/openapi.yaml`](../api/openapi.yaml) y
[`../data/modelo-e-indices.md`](../data/modelo-e-indices.md). Existen 9 pruebas de
vista previa en `apps/campos/tests.py`; no se identificaron pruebas de registros.
[NO VERIFICADO] Rendimiento con arreglos grandes, concurrencia y mappings reales.

## Riesgos

IDs inestables, `page_size` sin máximo, actualizaciones perdidas, alias confuso y
Bearer no validado. `datosArchivo` no debe reactivarse sin spec TO-BE y migración.
