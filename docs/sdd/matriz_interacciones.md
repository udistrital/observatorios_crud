# Matriz de interacciones AS-IS

Referencia: checkouts locales con CRUD `PROY-TOBE-008` y cliente
`PROY-TOBE-009`, inspeccionados el 2026-11-12. La fuente canónica del
contrato HTTP provisto por este repositorio es
[`../api/openapi.yaml`](../api/openapi.yaml).

| ID | Estado | Origen | Destino | Disparador y contrato observado | Respuesta/efecto | Fallos relevantes | Evidencia |
|---|---|---|---|---|---|---|---|
| INT-001 | [VERIFICADO] activo | Cliente | CRUD | Servicios Vue llaman familias `/procesos`, `/factores`, `/caracteristicas`, `/aspectos` y `/estructuras-evidencias` sobre `MAIN_BACKEND`. | JSON; actualiza componentes y stores. | Errores heterogéneos; token de `sessionStorage` no se adjunta en todos los clientes. | `observatorios_cliente/src/service/*.service.js`; `osiris/apps/*/urls.py` |
| INT-002 | [VERIFICADO] activo | Cliente | CRUD | `GET/POST/PUT/PATCH/DELETE /campos/...` para definición y registros; `tipo_campo: link` transporta URL HTTP(S) o `null`. | Estructura o registros embebidos en Elasticsearch; enlaces se mapean como `keyword`. | IDs posicionales, paginación manual, validación 400 de enlaces y efectos de limpieza. | `campos.service.js`; `apps/campos/views.py`; `apps/campos/utils.py` |
| INT-003 | [VERIFICADO] activo | Cliente | Gestor Documental | Carga, reemplazo y eliminación mediante `GESTOR_DOCUMENTAL`; la consulta directa ya no pertenece al visor activo. | Retorna hash/enlace para persistir en INT-002 o confirma eliminación. | Operaciones entre servicios no son transaccionales y pueden dejar binarios huérfanos. | `gestorDocumentalService.js`; `Tablero.vue` |
| INT-004 | [VERIFICADO] activo | Cliente | CRUD | `POST /campos/archivos/vista-previa/` multipart para Word/Excel. | PDF temporal `inline`; no persiste binario. | Bearer solo se comprueba sintácticamente; 413/415/422/429/503/504. | `apps/campos/views.py: VistaPreviaDocumentoView` |
| INT-005 | [VERIFICADO] consumo legado / [INFERIDO] no operativo | Cliente | MID | Componentes `archivos/` intentan `POST/PUT /documento` con URL base vacía. | Pretende coordinar antivirus, gestor y `datosArchivo`. | Mismo origen, sin Bearer y manejo incompleto de errores. | `components/archivos/AgregarArchivo.vue`; `RegistroArchiGestion.vue` |
| INT-006 | [VERIFICADO] declarado / [INFERIDO] no operativo | MID | CRUD | `POST/PUT datosArchivo/{estructura}/{registro}`. | Pretende persistir metadatos documentales. | Modelo actual no contiene miembros usados por `DatosArchivoViewSet`. | `observatorios_mid/services/observatorios_service.py`; `apps/datos/views.py`; `apps/campos/models.py` |
| INT-007 | [VERIFICADO] | CRUD | Elasticsearch | Consultas e indexación en índices `atlas_*` y dinámicos. | Persistencia de dominio. | Sin transacción multiíndice; TLS desactivado en una construcción de cliente. | `apps/elasticsearch_utils/`; [`../data/modelo-e-indices.md`](../data/modelo-e-indices.md) |
| INT-008 | [VERIFICADO] condicional | CRUD | AWS SSM | Cuando `PARAMETER_STORE` tiene valor, settings obtiene configuración remota. | Variables de conexión y seguridad. | Disponibilidad/permisos IAM no verificados. | `osiris/osiris/settings.py` |
| INT-009 | [VERIFICADO] activo | Cliente | CRUD | POST `/campos/documentos/referencias/` con `proceso_id`, `factor_id`, `estructura_id`, `documento_id` y Bearer sintáctico. | Tras validar cadena ES activa y exactamente una coincidencia `hash`, retorna `{referencia}`. | 400/401/404/429/503; no valida JWT ni ACL por proceso. | `campos.service.js`; `ReferenciaDocumentoView`; `documentos.py` |
| INT-010 | [VERIFICADO] activo | Cliente | CRUD | GET `/campos/documentos/{referencia}/` con Bearer sintáctico. | Descifra `v1_`, revalida ES y retorna el JSON del Gestor con `private, no-store`, `no-cache` y `nosniff`. | 401/403/404/413/429/502/503/504; referencia transferible durante TTL. | `DocumentoVisor.vue`; `ContenidoDocumentoView` |
| INT-011 | [VERIFICADO] activo | CRUD | Gestor Documental | GET fijo `GESTOR_DOCUMENTAL/document/{documento_id}`, HTTPS, sin redirects y con Bearer reenviado. | JSON se limita y almacena temporalmente antes de responder 200. | El Gestor decide permisos; una credencial amplia conserva acceso directo como riesgo residual. | `apps/campos/views.py: obtener_documento_gestor` |

## Reglas de compatibilidad

- Un cambio de ruta, método, payload, respuesta, error, permiso o paginación debe
  revisar INT-001 a INT-011 y la matriz homóloga del cliente.
- La mera presencia de Bearer en el cliente no demuestra autenticación en el CRUD.
- `datosArchivo` no debe presentarse como integración activa hasta reproducirla con
  el modelo actual.
- No se documentan valores de variables, hashes reales ni URLs internas.
