# Correspondencia TO-BE CRUD ↔ MID

> Estado: [NO VERIFICADO]. El checkout local de `observatorios_mid@92e9ca9` no
> contiene los documentos MID citados. Esta tabla conserva propuestas históricas,
> no contratos aprobados ni implementados.

## Objetivo
Mantener trazabilidad explícita de requerimientos evolutivos compartidos entre `observatorios_crud` y `observatorios_mid`.

## Matriz de correspondencia
| TO-BE CRUD | TO-BE MID relacionado | Relación funcional | Estado de alineación |
|---|---|---|---|
| `PROY-TOBE-001` Contrato versionado `datosArchivo` | `PROY-TOBE-001` Contrato completo `/api/v1/documento` | MID consumiría y sincronizaría metadatos | Propuesto; contraparte [NO VERIFICADO] |
| `PROY-TOBE-001` Contrato versionado `datosArchivo` | `PROY-TOBE-004` Pruebas de contrato hacia CRUD | MID validaría compatibilidad por pruebas | Propuesto; contraparte [NO VERIFICADO] |
| `PROY-TOBE-006` Correlation-id y trazabilidad distribuida con MID | `PROY-TOBE-003` Correlation-id distribuido | Trazabilidad end-to-end propuesta | Propuesto; contraparte [NO VERIFICADO] |

## Evidencia
- `docs/specs/backlog_specs.md` (CRUD)
- `observatorios_mid/docs/specs/backlog_specs.md` (MID, [NO VERIFICADO]: ausente en checkout local)
- `docs/specs/PROY-TOBE-006_correlation_id_trazabilidad_mid_crud.md` (CRUD)
- `observatorios_mid/docs/specs/PROY-TOBE-003_correlation_id_trazabilidad_distribuida.md` (MID, [NO VERIFICADO]: ausente en checkout local)

## Brechas
- Pendiente decisión sobre continuidad de MID y `datosArchivo`.
- No hay evidencia local de formalización equivalente en ambos repositorios.
