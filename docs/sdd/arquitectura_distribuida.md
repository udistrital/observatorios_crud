# Arquitectura distribuida SDD (referencia local)

## Contexto
`observatorios_crud` forma parte de una arquitectura distribuida de 3 repositorios separados.

## Límites de responsabilidad
- **CRUD (este repo)**: API de dominio y persistencia/indexación.
- **observatorios_cliente**: consumo UI.
- **observatorios_mid**: orquestación documental y sincronización con CRUD.

## Integraciones críticas
1. Cliente -> CRUD (`api/v1/*`).
2. MID -> CRUD (`datosArchivo/*`).
