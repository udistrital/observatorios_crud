# Arquitectura distribuida SDD (referencia local)

> Estado: referencia histórica. Consulte
> [`arquitectura-as-is.md`](arquitectura-as-is.md) para la vista verificada.

## Contexto
`observatorios_crud` forma parte de una arquitectura distribuida de 3 repositorios separados.

## Límites de responsabilidad
- **CRUD (este repo)**: API de dominio y persistencia/indexación.
- **observatorios_cliente**: consumo UI.
- **Gestor Documental**: almacenamiento binario; cliente lo consume para
  carga/reemplazo/eliminación y CRUD para la consulta activa del visor.
- **observatorios_mid**: dependencia legada para un flujo `datosArchivo` no verificado.

## Integraciones críticas
1. Cliente -> CRUD (`api/v1/*`).
2. Cliente -> Gestor Documental para mutaciones y cliente -> CRUD
   (`campos/datos/*`, `campos/documentos/*`).
3. CRUD -> Gestor Documental para el GET validado de visualización.
4. MID -> CRUD (`datosArchivo/*`) como integración legada.
