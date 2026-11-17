# Checklist de PROY-TOBE-008

## Antes de implementar

- [x] Spec aprobada y ambigüedades críticas resueltas.
- [x] Plan y tareas trazan todos los AC.
- [x] Contrato, datos, permisos, errores y consumidores revisados.
- [x] Sin migración; despliegue y rollback definidos.
- [x] Autorización explícita recibida el 2026-11-11.

## Antes de cerrar

- [x] `apps.campos` (47 casos) y `manage.py check` ejecutados; la suite global
  conserva dos fallos ajenos por permisos de Elasticsearch al crear
  `test_observatorios`.
- [x] OpenAPI, matrices, trazabilidad y AS-IS convergen.
- [x] No se incorporaron secretos ni datos reales.
- [x] Riesgos residuales y ausencia de E2E están visibles.
