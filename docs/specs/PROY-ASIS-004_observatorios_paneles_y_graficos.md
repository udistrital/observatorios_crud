# PROY-ASIS-004 Observatorios, paneles y gráficos

## Identidad

Sistema `observatorios_crud`; estado AS-IS; referencia `3de996b`, 2026-11-10.
Evidencia: `apps/observatorios/`, `apps/dashboards/` y `apps/graficos/`.

## Objetivo y alcance

**Como** consumidor, **quiero** administrar observatorios, dashboards y gráficos,
**para** configurar visualizaciones. Incluye configuración persistida y constructor;
excluye exactitud analítica y autorización de usuarios.

## Requisitos y reglas

| ID | Requisito | Regla |
|---|---|---|
| REQ-VIS-001 | CRUD de observatorios con imagen. | BR-VIS-001: DELETE desactiva; IDs se generan con lógica propia. |
| REQ-VIS-002 | CRUD de dashboard. | BR-VIS-002: cada dashboard deriva un índice de gráficos. |
| REQ-VIS-003 | Posicionar y configurar gráficos. | BR-VIS-003: fila/columna se actualizan mediante bulk. |
| REQ-VIS-004 | Construir resultados. | BR-VIS-004: usa estructura y configuración; [INFERIDO] depende de API antigua. |
| REQ-VIS-005 | Exponer catálogos/configuración. | BR-VIS-005: cinco tipos en constructor, pero validación persistida admite menos. |

## Criterios

- **AC-VIS-001**: Dado un observatorio válido, cuando se crea, entonces retorna
  201 y almacena imagen/ruta según el modelo.
- **AC-VIS-002**: Dado `observatorio` en query, cuando se listan dashboards,
  entonces se aplica filtro exacto.
- **AC-VIS-003**: Dado un dashboard existente, cuando se crea un gráfico válido,
  entonces queda en su índice dinámico.
- **AC-VIS-004**: La construcción de gráfico no se considera verificada hasta
  ejecutar una configuración válida con el modelo actual.

## Contratos, pruebas y riesgos

Ver [`../api/openapi.yaml`](../api/openapi.yaml). Hay dos pruebas de observatorios
dependientes de Elasticsearch; no hay pruebas efectivas de panel/gráficos. Riesgos:
imagen anterior no eliminada, respuesta nula en creación de dashboard, divergencia
de tipos y rutas de construcción probablemente rotas.
