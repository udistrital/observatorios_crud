# Tareas de PROY-TOBE-007

| ID | Estado | Dependencias | Tarea y archivos | Verificación |
|---|---|---|---|---|
| TASK-001 | completada | Ninguna | Crear spec, plan, tareas y checklist. | Artefactos enlazados desde índice/backlog. |
| TASK-002 | completada | TASK-001 | Implementar catálogo, mapping y validación en `apps/campos/utils.py` y `apps/estructuras/serializers.py`. | Suite de campos aprobada. |
| TASK-003 | completada | TASK-002 | Agregar cobertura en `apps/campos/tests.py`. | 16 pruebas aprobadas. |
| TASK-004 | completada | TASK-002 | Actualizar OpenAPI, datos, AS-IS y matriz. | YAML válido y referencias revisadas. |
| TASK-005 | completada | TASK-003, TASK-004 | Ejecutar check y revisar diff final coordinado. | `manage.py check` sin problemas; revisión cruzada aplicada. |
