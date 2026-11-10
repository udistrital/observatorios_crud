# Documentación técnica de `observatorios_crud`

Fuente inspeccionada: rama `feature/campo_orden`, commit `3de996b`, 2026-11-10.

## Ruta de lectura mínima

1. [Guía del repositorio](../AGENTS.md)
2. [Inventario de evidencias](sdd/inventario-evidencias.md)
3. [Arquitectura AS-IS](sdd/arquitectura-as-is.md)
4. [OpenAPI AS-IS](api/openapi.yaml)
5. [Matriz de interacciones](sdd/matriz_interacciones.md)
6. [Matriz de trazabilidad](sdd/matriz-trazabilidad.md)
7. [Especificaciones SDD](specs/README.md)

## Índice por responsabilidad

| Tema | Fuente canónica |
|---|---|
| Módulos y evidencia | [Inventario](sdd/inventario-evidencias.md) |
| Contexto, contenedores y secuencias | [Arquitectura AS-IS](sdd/arquitectura-as-is.md) |
| Endpoints, request, response y errores | [OpenAPI](api/openapi.yaml) y [diferencias](api/diferencias-contrato.md) |
| Índices, campos y consistencia | [Modelo de datos](data/modelo-e-indices.md) |
| Integraciones cliente/CRUD/MID/Gestor | [Matriz de interacciones](sdd/matriz_interacciones.md) |
| REQ/BR/AC/código/prueba | [Trazabilidad](sdd/matriz-trazabilidad.md) |
| Seguridad y deuda | [Brechas y riesgos](sdd/brechas-y-riesgos.md) |
| Arranque, Docker y CI | [Ejecución y despliegue](operations/ejecucion-y-despliegue.md) |
| Trabajo de agentes | [Guía](sdd/guia-agentes.md) y [flujo SDD](sdd/flujo-sdd.md) |

## Documentos anteriores

[Arquitectura e integraciones](arquitectura_e_integraciones.md),
[flujos](flujos.md), [arquitectura distribuida](sdd/arquitectura_distribuida.md) y
[reglas históricas](REGLAS_DESARROLLO_AGENTES_IA.md) se conservan por trazabilidad.
Cuando difieran, las fuentes canónicas de la tabla y el código del commit de
referencia describen el AS-IS.

## Convención de certeza

- `[VERIFICADO]`: evidencia directa en checkout.
- `[INFERIDO]`: consecuencia estática razonable, pendiente de ejecución.
- `[NO VERIFICADO]`: evidencia insuficiente o dependencia inaccesible.
- `[PROPUESTA]`: evolución no implementada ni autorizada.
- `[NO APLICA]`: dimensión evaluada que no corresponde, con justificación.
