# PROY-TOBE-006 — Correlation-id y trazabilidad distribuida en integración MID↔CRUD

## Historia de Usuario (TO-BE)
**Como** equipo de mantenimiento de `observatorios_crud`
**Quiero** aceptar y registrar un identificador de correlación en endpoints `datosArchivo`
**Para** facilitar trazabilidad end-to-end del flujo documental iniciado en MID.

## Criterios de aceptación funcionales
1. Endpoints `datosArchivo` deben aceptar `X-Correlation-Id` en request.
2. CRUD debe incluir `X-Correlation-Id` en logs y respuestas asociadas al flujo.
3. Debe existir compatibilidad documental con `observatorios_mid/docs/specs/PROY-TOBE-003_correlation_id_trazabilidad_distribuida.md`.

---

## Problema funcional
Sin contrato de correlación, rastrear incidentes entre MID y CRUD exige análisis manual no determinístico.

## Objetivo del usuario
Estandarizar correlación técnica en operaciones `datosArchivo`.

## Impacto institucional
- Menor tiempo de diagnóstico de incidentes inter-repo.
- Mayor gobernanza en auditoría de integraciones.

---

## Soporte técnico propuesto
### Contrato de correlación
- Header canónico: `X-Correlation-Id`.
- Formato sugerido: UUID v4 en minúsculas.
- Si no se recibe, CRUD registra **INFERENCIA:** correlación no propagada por consumidor aguas arriba.

### Evidencia base AS-IS
- `docs/specs/PROY-ASIS-001_enrutamiento_api_v1.md`
- `docs/specs/CRUD-ASIS-002_datos_archivo.md`
- `docs/sdd/matriz_interacciones.md`

### Dependencias
- `osiris/apps/datos/*`
- capa de logging/configuración
- trazabilidad cruzada con MID
