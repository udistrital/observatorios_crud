# Guía de trabajo para agentes

## Lectura mínima por tarea

| Tarea | Leer primero | Después |
|---|---|---|
| Endpoint/backend | `inventario-evidencias.md`, `../api/openapi.yaml` | `osiris/osiris/urls.py`, URL/view/serializer/modelo del dominio |
| Integración con cliente | `matriz_interacciones.md` | servicio y componente consumidor en `observatorios_cliente` |
| Elasticsearch/datos | `../data/modelo-e-indices.md` | mapping, modelo y utilidades afectados |
| Seguridad | `brechas-y-riesgos.md` | settings, permisos, CORS, validación y límites de confianza |
| Vista previa | Spec, OpenAPI y `apps/campos/` | tests y consumidor `DocumentoVisor.vue` |
| Despliegue | `../operations/ejecucion-y-despliegue.md` | Docker, Compose, Drone y settings |
| Cambio de contrato | OpenAPI, matrices y trazabilidad | todos los consumidores y tests |

## Reglas de contexto

1. Leer el índice y el módulo afectado; no cargar el repositorio completo.
2. Buscar la ruta global, URL de aplicación, handler y consumidor.
3. Referenciar `ruta:símbolo` o líneas verificadas; no inventar evidencia.
4. No leer ni reproducir valores de `.env`, tokens o datos reales.
5. Distinguir ruta activa, alias, legado y propuesta.

## Protocolo

Seguir [`flujo-sdd.md`](flujo-sdd.md). Una spec TO-BE y un plan no autorizan por
sí mismos implementar. La autorización debe ser explícita.

## Compatibilidad

Un cambio de ruta, campo, mapping, error, permiso, paginación o variable exige
revisar en la misma entrega:

- OpenAPI AS-IS/TO-BE según fase.
- Servicio y componente consumidor.
- `matriz_interacciones.md` y `matriz-trazabilidad.md`.
- Migración/compatibilidad de datos y rollback cuando corresponda.
- Pruebas positivas, negativas y de límites.

## Discrepancias

Registrar: comportamiento encontrado, fuentes en conflicto, criticidad, evidencia,
decisión pendiente y responsable solo si está identificado. El código ejecutable
prevalece para AS-IS; un requisito aprobado prevalece para definir TO-BE, pero no
debe presentarse como implementado.

## Definición de terminado documental

- Evidencia y etiqueta de certeza por afirmación crítica.
- Enlaces relativos y rutas existentes.
- REQ, BR y AC trazados a código, contrato y prueba o vacío explícito.
- Diagramas consistentes con la matriz.
- OpenAPI y ejemplos sin datos sensibles.
- AS-IS y TO-BE separados.
- Validaciones ejecutadas y omitidas registradas.
- Documentos afectados actualizados sin duplicar una fuente canónica.
