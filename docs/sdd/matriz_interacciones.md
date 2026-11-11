# Matriz de interacciones AS-IS

Referencia: `observatorios_crud@3de996b`, `observatorios_cliente@8537cb7` y
`observatorios_mid@92e9ca9`, inspeccionados el 2026-11-10. La fuente canónica del
contrato HTTP provisto por este repositorio es
[`../api/openapi.yaml`](../api/openapi.yaml).

| ID | Estado | Origen | Destino | Disparador y contrato observado | Respuesta/efecto | Fallos relevantes | Evidencia |
|---|---|---|---|---|---|---|---|
| INT-001 | [VERIFICADO] activo | Cliente | CRUD | Servicios Vue llaman familias `/procesos`, `/factores`, `/caracteristicas`, `/aspectos` y `/estructuras-evidencias` sobre `MAIN_BACKEND`. | JSON; actualiza componentes y stores. | Errores heterogéneos; token de `sessionStorage` no se adjunta en todos los clientes. | `observatorios_cliente/src/service/*.service.js`; `osiris/apps/*/urls.py` |
| INT-002 | [VERIFICADO] activo | Cliente | CRUD | `GET/POST/PUT/PATCH/DELETE /campos/...` para definición y registros; `tipo_campo: link` transporta URL HTTP(S) o `null`. | Estructura o registros embebidos en Elasticsearch; enlaces se mapean como `keyword`. | IDs posicionales, paginación manual, validación 400 de enlaces y efectos de limpieza. | `campos.service.js`; `apps/campos/views.py`; `apps/campos/utils.py` |
| INT-003 | [VERIFICADO] activo | Cliente | Gestor Documental | Carga, consulta y eliminación del binario mediante `GESTOR_DOCUMENTAL`. | Retorna hash/enlace o archivo base64; el cliente registra hash en INT-002. | Si una segunda operación falla puede quedar binario o metadato huérfano. | `gestorDocumentalService.js`; `Tablero.vue`; `DocumentoVisor.vue` |
| INT-004 | [VERIFICADO] activo | Cliente | CRUD | `POST /campos/archivos/vista-previa/` multipart para Word/Excel. | PDF temporal `inline`; no persiste binario. | Bearer solo se comprueba sintácticamente; 413/415/422/429/503/504. | `apps/campos/views.py: VistaPreviaDocumentoView` |
| INT-005 | [VERIFICADO] consumo legado / [INFERIDO] no operativo | Cliente | MID | Componentes `archivos/` intentan `POST/PUT /documento` con URL base vacía. | Pretende coordinar antivirus, gestor y `datosArchivo`. | Mismo origen, sin Bearer y manejo incompleto de errores. | `components/archivos/AgregarArchivo.vue`; `RegistroArchiGestion.vue` |
| INT-006 | [VERIFICADO] declarado / [INFERIDO] no operativo | MID | CRUD | `POST/PUT datosArchivo/{estructura}/{registro}`. | Pretende persistir metadatos documentales. | Modelo actual no contiene miembros usados por `DatosArchivoViewSet`. | `observatorios_mid/services/observatorios_service.py`; `apps/datos/views.py`; `apps/campos/models.py` |
| INT-007 | [VERIFICADO] | CRUD | Elasticsearch | Consultas e indexación en índices `atlas_*` y dinámicos. | Persistencia de dominio. | Sin transacción multiíndice; TLS desactivado en una construcción de cliente. | `apps/elasticsearch_utils/`; [`../data/modelo-e-indices.md`](../data/modelo-e-indices.md) |
| INT-008 | [VERIFICADO] condicional | CRUD | AWS SSM | Cuando `PARAMETER_STORE` tiene valor, settings obtiene configuración remota. | Variables de conexión y seguridad. | Disponibilidad/permisos IAM no verificados. | `osiris/osiris/settings.py` |

## Reglas de compatibilidad

- Un cambio de ruta, método, payload, respuesta, error, permiso o paginación debe
  revisar INT-001 a INT-006 y la matriz homóloga del cliente.
- La mera presencia de Bearer en el cliente no demuestra autenticación en el CRUD.
- `datosArchivo` no debe presentarse como integración activa hasta reproducirla con
  el modelo actual.
- No se documentan valores de variables, hashes reales ni URLs internas.
