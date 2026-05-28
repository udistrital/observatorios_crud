# AGENTS.md — Punto de entrada técnico

## Propósito del repositorio
API backend CRUD del dominio Observatorios, con persistencia/indexación y exposición de contratos REST.

## Dónde empezar
1. `README.md`
2. `docs/README.md`
3. `docs/specs/README.md`

## Interacciones obligatorias con otros repositorios
- Atiende consumo de `observatorios_cliente`.
- Recibe sincronización documental desde `observatorios_mid` (metadatos `datosArchivo`).

## Convención SDD
- Toda modificación de endpoints o datos inicia en `docs/specs/`.
- Cambios que afecten a cliente o MID deben reflejarse en `docs/sdd/matriz_interacciones.md`.

## Flujo documental obligatorio (alineado)
1. Levantar contexto real desde `README.md`, `docs/` y configuración (`.drone.yml`, `docker-compose`, scripts).
2. Marcar como **INFERENCIA** todo dato no verificable en código/configuración.
3. Documentar primero estado **AS-IS** y luego registrar evolución **TO-BE** en backlog.
4. Mantener trazabilidad historia funcional → criterios → evidencia (ruta/archivo/endpoint).
5. Aplicar regla de no regresión documental: si cambia contrato, flujo o variable, actualizar documentación en el mismo cambio.
