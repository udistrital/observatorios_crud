# CRUD-ASIS-002 — Persistencia de metadatos documentales (`datosArchivo`)

## Historia de Usuario (AS-IS)
**Como** proceso documental institucional
**Quiero** persistir metadatos de archivo asociados a una estructura
**Para** garantizar trazabilidad documental en el dominio observatorios.

## Criterios de aceptación funcionales
- Dado un metadato válido, cuando se registra, entonces queda disponible para consulta/actualización.
- Dado una actualización documental, cuando se ejecuta, entonces se conserva integridad del registro asociado.

## 1. Contexto
El CRUD expone rutas específicas `datosArchivo` para registro y actualización de metadatos de archivos, consumidas por MID.

## 2. Problema
No hay contrato documental formal del recurso `datosArchivo` pese a su criticidad inter-repositorio.

## 3. Objetivo
Definir comportamiento AS-IS del recurso `datosArchivo` y su patrón de enrutamiento.

## 4. Alcance
### Incluye
- Endpoints list/create/destroy y retrieve/update/destroy.
- Dependencia de `id_archivos` y `pk`.
### Excluye (Fuera de alcance)
- Semántica detallada de cada campo dentro de `DatosArchivo`.

## 5. Actores
- `observatorios_mid`.
- `DatosArchivoViewSet`.

## 6. Flujo principal
1. MID invoca `POST datosArchivo/{id_archivos}/` para crear metadato.
2. CRUD persiste en índice asociado.
3. MID invoca `PUT datosArchivo/{id_archivos}/{pk}/` para actualización.

## 7. Flujos alternos / excepciones
- A1: `id_archivos` no mapeado -> ViewSet deja `_nombre_indice=None`.
- **INFERENCIA**: respuesta de error depende de manejo posterior del ViewSet cuando no hay índice.

## 8. Reglas de negocio
- RN-01: La clave de enrutamiento primaria es `id_archivos`.
- RN-02: Operaciones por `pk` exigen identificación de documento previo.

## 9. Contratos técnicos
- `datosArchivo/<str:id_archivos>/`
- `datosArchivo/<str:id_archivos>/<str:pk>/`

## 10. Criterios de aceptación verificables
- [ ] Existen rutas separadas para creación/listado y actualización puntual.
- [ ] MID puede invocar POST y PUT con los identificadores esperados.

## 11. Dependencias
- `apps.datos.views.DatosArchivoViewSet`
- Consumidor `observatorios_mid/services/observatorios_service.py`

## 12. Riesgos
- Contrato no versionado explícitamente por schema.

## 13. Pendientes
- Publicar schema OpenAPI específico para `datosArchivo`.

## 14. Evidencia
- `observatorios_crud/osiris/apps/datos/urls.py`
- `observatorios_crud/osiris/apps/datos/views.py`

## 15. Clasificación SDD
- Tipo: AS-IS
- Tamaño relativo: M
- Prioridad: Alta
