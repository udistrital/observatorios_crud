# SDD — observatorios_crud

## Propósito
Consolidar especificaciones del backend CRUD con enfoque en **historias de usuario**, comportamiento esperado y reglas funcionales del dominio.

## Estructura
- `specs/plantillas/spec_template.md`
- `specs/PROY-ASIS-*_*.md` (convención vigente)
- `specs/CRUD-ASIS-*_*.md` (legado conservado por trazabilidad)
- `specs/backlog_specs.md`

## Mapa documental SDD
- Visión y alcance: `../README.md`
- Arquitectura e integraciones: `../arquitectura_e_integraciones.md`
- Flujos funcionales: `../flujos.md`

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
- `PROY-TOBE-006_correlation_id_trazabilidad_mid_crud.md`
