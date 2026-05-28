# Backlog SDD — observatorios_crud

| ID | Spec propuesta | Valor | Riesgo | Esfuerzo | Dependencias | Evidencia base AS-IS |
|---|---|---|---|---|---|---|
| PROY-TOBE-001 | Contrato versionado de `datosArchivo` (request/response/errores) | Alto | Alto | M | `observatorios_mid`, `apps/datos/*` | `docs/specs/CRUD-ASIS-002_datos_archivo.md`, `observatorios_mid/docs/specs/PROY-ASIS-003_integracion_mid_crud_datos_archivo.md` |
| PROY-TOBE-002 | Estrategia de resiliencia y fallback ante indisponibilidad de Elasticsearch | Alto | Alto | L | `apps/elasticsearch_utils/*` | `docs/arquitectura_e_integraciones.md` |
| PROY-TOBE-003 | Cobertura de pruebas de integración por recurso crítico | Alto | Medio | M | suites `apps/*/tests.py` | `osiris/apps/observatorios/tests/test_views.py` |
| PROY-TOBE-004 | Especificación de paginación, ordenamiento y filtros por endpoint | Medio | Medio | S | `apps/datos/views.py` y módulos homólogos | `docs/flujos.md` |
| PROY-TOBE-005 | Endurecer operación local: validación previa/creación de `elastic_net` en `run_crud.sh` y checklist de conectividad Elastic | Medio | Medio | S | `run_crud.sh`, `osiris/docker-compose.yml` | `README.md` sección troubleshooting |
| PROY-TOBE-006 | Correlation-id y trazabilidad distribuida para flujos con MID (`datosArchivo`) | Alto | Medio | S | `observatorios_mid`, `osiris/apps/datos/*`, capa de logging/middleware | `docs/sdd/matriz_interacciones.md`, `docs/sdd/correspondencia_tobe_crud_mid.md` |

## Nota
- Convención vigente de requerimientos nuevos: `PROY-TOBE-XXX`.
- Requerimientos con impacto MID↔CRUD deben mantener trazabilidad cruzada en ambos repositorios.
- Ver matriz de correspondencia: `docs/sdd/correspondencia_tobe_crud_mid.md`.
