# Brechas y riesgos AS-IS

## Criterio

Registro documental basado en código de `observatorios_crud@3de996b`. Las
categorías OWASP API Security Top 10 2023 se usan para clasificar preocupaciones;
no se afirma cumplimiento ni auditoría de seguridad formal.

| ID | Criticidad | Estado | Brecha o riesgo | Evidencia | Referencia |
|---|---|---|---|---|---|
| CRUD-R-001 | Crítica | [VERIFICADO] código / [NO VERIFICADO] perímetro | No hay autenticación/autorización de dominio configurada; mutaciones podrían ser anónimas. | `settings.py: REST_FRAMEWORK`; vistas sin permisos | OWASP API2/API5 |
| CRUD-R-002 | Alta | [VERIFICADO] | Vista previa acepta cualquier texto con prefijo Bearer; no valida token ni rol. | `campos/views.py: VistaPreviaDocumentoView` | OWASP API2 |
| CRUD-R-003 | Alta | [VERIFICADO] | `DEBUG=True`, hosts abiertos y media servida por Django. | `settings.py`; `osiris/urls.py` | OWASP API8 |
| CRUD-R-004 | Alta | [VERIFICADO] | No hay `.dockerignore`; contexto de imagen puede incorporar archivos locales sensibles. | `osiris/Dockerfile`; ausencia del archivo | OWASP API8 |
| CRUD-R-005 | Alta | [INFERIDO] | `datos`, `datosArchivo` y constructor usan miembros inexistentes y fallarían. | `datos/views.py`; `campos/models.py`; `graficos/views.py` | Fiabilidad |
| CRUD-R-006 | Alta | [VERIFICADO] | Relaciones denormalizadas se escriben sin transacción y con compensación desigual. | views de jerarquía | Integridad |
| CRUD-R-007 | Alta | [VERIFICADO] | IDs posicionales cambian después de borrar registros. | `DatosEstructuraDocumentoView.delete` | Compatibilidad |
| CRUD-R-008 | Alta | [VERIFICADO] | Varias respuestas exponen `str(error)` y el contrato de errores es heterogéneo. | `apps/*/views.py`; `custom_exception_handler` | OWASP API8 |
| CRUD-R-009 | Alta | [VERIFICADO] latente | Un validador usa `eval` sobre texto si se reactiva carga heredada. | `elasticsearch_utils/validadores.py` | OWASP API3/API8 |
| CRUD-R-010 | Media | [VERIFICADO] | Listados usan límites 1.000/10.000 o `page_size` sin máximo; riesgo de consumo. | views y `campos/utils.py` | OWASP API4 |
| CRUD-R-011 | Media | [VERIFICADO] | Regex de filtros no escapa entrada en utilidades. | `elasticsearch_utils/utils.py` | OWASP API4/API8 |
| CRUD-R-012 | Media | [VERIFICADO] | TLS del cliente Elasticsearch se desactiva en una ruta de construcción. | `elasticsearch_utils/views.py` | OWASP API8 |
| CRUD-R-013 | Media | [VERIFICADO] | Mappings e índices se crean perezosamente en peticiones, incluso lecturas. | `initial` de varios ViewSets | Operación |
| CRUD-R-014 | Media | [VERIFICADO] | CI publica sin ejecutar tests ni `manage.py check`. | `.drone.yml` | Cadena de entrega |
| CRUD-R-015 | Media | [VERIFICADO] | Compose con nombre productivo usa `runserver`; puerto Nginx diverge. | Compose y Nginx | Operación |
| CRUD-R-016 | Media | [NO VERIFICADO] | No hay procedimiento versionado de backup/restore ni objetivos RPO/RTO. | revisión documental | Recuperabilidad |
| CRUD-R-017 | Alta | [VERIFICADO] | POST/GET documental solo comprueban sintaxis Bearer; no validan JWT ni ACL por proceso. | `DocumentoProtegidoMixin`; `ReferenciaDocumentoView`; `ContenidoDocumentoView` | OWASP API2/API5 |
| CRUD-R-018 | Alta | [VERIFICADO] | Una referencia cifrada puede transferirse entre sesiones autenticadas durante el TTL. | `documentos.py: descifrar_referencia_documento` | OWASP API2 |
| CRUD-R-019 | Alta | [VERIFICADO] diseño / [NO VERIFICADO] permisos | Una credencial con alcance amplio puede omitir el CRUD y consultar directamente el Gestor; el proxy reenvía el Bearer y depende de sus permisos. | `obtener_documento_gestor` | OWASP API5 |
| CRUD-R-020 | Media | [VERIFICADO] | Tasa y semáforo del proxy son locales al proceso; el límite agregado crece con workers/réplicas. | `SEMAFORO_PROXY_DOCUMENTAL`; DRF throttle | OWASP API4 |

## Controles positivos observados

- [VERIFICADO] La vista previa valida extensión, MIME, firmas, ZIP expandido,
  macros, cifrado, relaciones externas, tiempo y tamaños.
- [VERIFICADO] Usa directorios temporales y cabeceras `no-store`/`nosniff`.
- [VERIFICADO] El proxy fija el destino, exige HTTPS por defecto, verifica TLS, no
  sigue redirects, limita bytes y completa el spool antes de responder 200.
- [VERIFICADO] Las llamadas a Elasticsearch requieren credenciales no vacías.
- [VERIFICADO] La plantilla no debe contener credenciales reales y SSM está
  soportado para ambientes remotos.

## Decisiones pendientes

- [PROPUESTA] Definir dónde se aplica autenticación y autorización por objeto.
- [PROPUESTA] Decidir si se retiran, reparan o aíslan rutas heredadas.
- [PROPUESTA] Estabilizar IDs de registros y estrategia de migración.
- [PROPUESTA] Normalizar errores solo mediante una spec TO-BE compatible.
- [PROPUESTA] Versionar mappings, consistencia y recuperación antes de cambios de
  datos.
- [PROPUESTA] Incorporar verificación JWT y autorización por proceso sin presentar
  el cifrado de referencias como sustituto.

Estas propuestas no autorizan cambios de código.
