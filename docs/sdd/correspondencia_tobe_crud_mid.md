# Correspondencia TO-BE CRUD ↔ MID

## Objetivo
Mantener trazabilidad explícita de requerimientos evolutivos compartidos entre `observatorios_crud` y `observatorios_mid`.

## Matriz de correspondencia
| TO-BE CRUD | TO-BE MID relacionado | Relación funcional | Estado de alineación |
|---|---|---|---|
| `PROY-TOBE-001` Contrato versionado `datosArchivo` | `PROY-TOBE-001` Contrato completo `/api/v1/documento` | MID consume y sincroniza metadatos usando contrato CRUD | Alineado |
| `PROY-TOBE-001` Contrato versionado `datosArchivo` | `PROY-TOBE-004` Pruebas de contrato hacia CRUD | MID valida compatibilidad de contrato CRUD por pruebas | Alineado |
| `PROY-TOBE-006` Correlation-id y trazabilidad distribuida con MID | `PROY-TOBE-003` Correlation-id distribuido | Requerido para trazabilidad end-to-end entre cliente, MID y CRUD | Alineado |

## Evidencia
- `docs/specs/backlog_specs.md` (CRUD)
- `observatorios_mid/docs/specs/backlog_specs.md` (MID)
- `docs/specs/PROY-TOBE-006_correlation_id_trazabilidad_mid_crud.md` (CRUD)
- `observatorios_mid/docs/specs/PROY-TOBE-003_correlation_id_trazabilidad_distribuida.md` (MID)

## Brechas
- Pendiente de implementación en código (documentación TO-BE de correlación ya formalizada en ambos repositorios).
