# Diferencias de contrato

## Referencia y cobertura

Comparación estática actualizada el 2026-11-12 entre runtime Django, Swagger 2 en
`swagger/` y los checkouts locales de cliente/CRUD. El OpenAPI AS-IS registra 35 rutas y 92
operaciones de dominio, más `GET /health/`. No incluye las UIs Swagger/ReDoc, sus
representaciones JSON/YAML, variantes `.{format}`, `HEAD`, `OPTIONS` ni media.

| ID | Severidad | Fuentes en conflicto | Diferencia | Estado/correctivo |
|---|---|---|---|---|
| DIF-001 | Alta | Runtime vs Swagger 2 | Swagger omite `/api/{version}` y usa `basePath: /`. | [VERIFICADO]; usar OpenAPI AS-IS. |
| DIF-002 | Alta | Settings/views vs Swagger 2 | Swagger declara Basic global; runtime no exige autenticación global. | [VERIFICADO]; no se declaró seguridad en OpenAPI. |
| DIF-003 | Alta | Runtime vs Swagger 2 | Vista previa no aparece en snapshot histórico. | [VERIFICADO]; incluida con multipart y estados reales. |
| DIF-004 | Alta | Runtime vs Swagger 2 | Estados de observatorios y gráficos incluyen 201 donde runtime responde 200. | [VERIFICADO]; corregido en AS-IS. |
| DIF-005 | Alta | Runtime/docs MID | `datosArchivo` se presenta operativo, pero usa atributos inexistentes. | [INFERIDO] no operativo; marcado deprecated/degradado. |
| DIF-006 | Alta | Cliente vs CRUD | Cliente envía Bearer, pero CRUD no lo valida globalmente. | [VERIFICADO] código; control perimetral [NO VERIFICADO]. |
| DIF-007 | Alta | Vista previa/docs | “Requiere Bearer” podía interpretarse como autenticación. | [VERIFICADO] solo sintaxis; aclarado. |
| DIF-008 | Media | Runtime vs semántica HTTP | PUT es parcial en varias familias; errores/borrados no son uniformes. | [VERIFICADO]; descrito por operación, no normalizado. |
| DIF-009 | Media | Cliente vs helper | Cliente puede recibir 204 y obtener `undefined`. | [VERIFICADO] en `conexion_api.js`; no cambia contrato servidor. |
| DIF-010 | Media | Constructor vs gráficos persistidos | Constructor enumera cinco tipos y validación persistida admite menos. | [VERIFICADO]; decisión pendiente. |
| DIF-011 | Media | Licencia | Swagger/dynamic info declara MIT; README declara GPL-3+. | [VERIFICADO]; OpenAPI referencia README, decisión legal pendiente. |
| DIF-012 | Media | Cliente activo vs docs antiguas | Flujo activo usa Gestor+CRUD; docs antiguas presentan MID. | [VERIFICADO]; matrices canónicas distinguen legado. |
| DIF-013 | Alta | Runtime vs Swagger 2 | Las rutas `/campos/documentos/referencias/` y `/campos/documentos/{referencia}/` no aparecen en el snapshot histórico. | [VERIFICADO]; incluidas con Bearer sintáctico, cuerpos y estados reales. |

## Validación

- [VERIFICADO] Un parser YAML cargó el documento sin error y el control estructural
  contó 36 paths, 93 operaciones totales, 35 paths/92 operaciones de dominio, 93
  `operationId` únicos y 391 referencias internas sin destinos rotos.
- [NO VERIFICADO] No hay en el entorno un validador OpenAPI 3.1.2 (`redocly`,
  `spectral`, `swagger-cli`, `openapi-spec-validator` o `prance`).
- [NO VERIFICADO] No se inició Django para comparar el esquema drf-yasg dinámico.
