# SDD de `observatorios_crud`

## Propósito
Consolidar especificaciones del backend CRUD con enfoque en **historias de usuario**, comportamiento esperado y reglas funcionales del dominio.

## Estructura y plantillas

- [Spec](plantillas/spec_template.md): qué y por qué.
- [Plan](plantillas/plan_template.md): cómo.
- [Tareas](plantillas/tasks_template.md): orden de ejecución.
- [Checklist](plantillas/checklist_template.md): puertas de calidad.
- [ADR](adr/adr_template.md): decisiones arquitectónicas aprobadas.
- [Backlog](backlog_specs.md): propuestas; no concede autorización.

## Mapa documental

- [Índice técnico](../README.md)
- [Arquitectura AS-IS](../sdd/arquitectura-as-is.md)
- [Matriz de trazabilidad](../sdd/matriz-trazabilidad.md)
- [Flujo SDD](../sdd/flujo-sdd.md)

## Convenciones
- Cada especificación debe iniciar con una **Historia de Usuario** (Como / Quiero / Para).
- Redactar primero el valor funcional y luego los detalles técnicos.
- Evidencia obligatoria por ruta.
- Identificar comportamiento no confirmado como **INFERENCIA**.
- Nomenclatura de specs: `ID_nombre.md`.
  - AS-IS vigente recomendado: `PROY-ASIS-XXX_nombre.md`.
  - TO-BE obligatorio: `PROY-TOBE-XXX_nombre.md`.
  - **Nota:** se mantienen IDs `CRUD-*` en documentos históricos para no romper referencias existentes.

## TO-BE documentados

- [PROY-TOBE-006 Correlation ID](PROY-TOBE-006_correlation_id_trazabilidad_mid_crud.md)

## AS-IS canónico

- [PROY-ASIS-001 Enrutamiento](PROY-ASIS-001_enrutamiento_api_v1.md)
- [PROY-ASIS-002 Jerarquía y evidencias](PROY-ASIS-002_jerarquia_y_evidencias.md)
- [PROY-ASIS-003 Campos y registros](PROY-ASIS-003_campos_y_registros.md)
- [PROY-ASIS-004 Observatorios, paneles y gráficos](PROY-ASIS-004_observatorios_paneles_y_graficos.md)

Los `CRUD-ASIS-*` se conservan como historia. No deben usarse para afirmar que
`datos` o `datosArchivo` están operativos sin reproducirlos.

## Puertas

Una evolución debe completar spec, aclaraciones, plan, tareas y checklist. Solo
una autorización explícita permite modificar código. Al converger se actualizan
OpenAPI, matrices, pruebas y documentación AS-IS.
