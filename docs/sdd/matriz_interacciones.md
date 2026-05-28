# Matriz de interacciones (AS-IS)

| Origen | Destino | Contrato observado | Riesgo | Evidencia |
|---|---|---|---|---|
| observatorios_cliente | observatorios_crud | CRUD `api/v1/...` | Medio | `osiris/osiris/urls.py`, `docs/specs/CRUD-ASIS-001_enrutamiento_api_v1.md` |
| observatorios_mid | observatorios_crud | `datosArchivo/*` | Alto | `docs/arquitectura_e_integraciones.md`, `docs/specs/CRUD-ASIS-002_datos_archivo.md` |

## INFERENCIA y brechas
- **INFERENCIA:** El detalle de payload/respuesta consumido por MID para `datosArchivo` no está consolidado en un único contrato versionado compartido entre ambos repositorios.
