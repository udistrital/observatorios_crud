# Ejecución y despliegue AS-IS

## Referencia y límites

[VERIFICADO] Documento basado en `observatorios_crud@3de996b` inspeccionado el
2026-11-10. No se iniciaron contenedores, no se ejecutaron migraciones y no se
contactaron AWS ni Elasticsearch.

## Dependencias

| Dependencia | Evidencia | Estado |
|---|---|---|
| Python 3.11 | `osiris/Dockerfile` | [VERIFICADO] |
| Django/DRF 4.2.17/3.15.2 | `osiris/requirements.txt` | [VERIFICADO] |
| Cliente Elasticsearch 8.17.0 | `osiris/requirements.txt` | [VERIFICADO] |
| Elasticsearch/Kibana 8.10.2 | `infraestructura/docker-compose*.yml` | [VERIFICADO] divergencia de versión |
| LibreOffice Writer/Calc | `osiris/Dockerfile` | [VERIFICADO] para vista previa |

## Variables documentables

Solo se enumeran nombres. Los valores reales y archivos `.env` quedan fuera de la
documentación.

| Área | Nombres consumidos o relevantes |
|---|---|
| Django | `SECRET_KEY`, `DJANGO_LOG_LEVEL`, `STATIC_ROOT`, `SECURE_SSL_REDIRECT` |
| Elasticsearch | `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_MAIN_INDEX`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD` |
| AWS SSM | `PARAMETER_STORE`, `AWS_REGION` |
| Vista previa | `LIBREOFFICE_EXECUTABLE`, `LIBREOFFICE_USER`, `DOCUMENT_PREVIEW_MAX_BYTES`, `DOCUMENT_PREVIEW_MAX_PDF_BYTES`, `DOCUMENT_PREVIEW_TIMEOUT_SECONDS`, `DOCUMENT_PREVIEW_RATE` |
| Plantilla pero no gobernantes en AS-IS | `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOWED_ORIGINS` |

[VERIFICADO] `DEBUG=True` y `ALLOWED_HOSTS=["*"]` están fijados en settings. La
política CORS depende de `PARAMETER_STORE`, no solamente de las variables con
nombre CORS.

## Arranque documentado

Desde la raíz:

```bash
cp osiris/.env.template osiris/.env
./infraestructura/run_infra.sh
./run_crud.sh
```

Ejecución directa, desde `osiris/` y con dependencias externas preparadas:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

[VERIFICADO] `run_crud.sh` y los Compose ejecutan migraciones. Este documento no
autoriza ejecutarlas en un ambiente compartido.

## Contenedores

- [VERIFICADO] `osiris/Dockerfile` sirve con Gunicorn y dos workers.
- [VERIFICADO] Los Compose de la API usan `runserver`, incluso el archivo con nombre
  de producción.
- [VERIFICADO] No existe `.dockerignore`; el contexto `osiris/` puede incluir
  archivos locales no destinados a imagen.
- [VERIFICADO] Los Compose montan el código como volumen y publican 8000.
- [VERIFICADO] Nginx escucha 8080, mientras el Compose publica el puerto 80 del
  contenedor (`infraestructura/nginx/default.conf`).
- [NO VERIFICADO] Construcción y arranque efectivos de la imagen actual.

## CI/CD

`/.drone.yml` define Sonar, publicación en ECR y despliegue ECS según rama.

- [VERIFICADO] No ejecuta `manage.py check` ni pruebas antes de publicar.
- [VERIFICADO] Usa imágenes `latest` en partes del pipeline.
- [VERIFICADO] Sonar excluye pruebas según `sonar-project.properties`.
- [NO VERIFICADO] Credenciales, permisos AWS, estabilidad del servicio y rollback.

## Salud y observabilidad

- `GET /health/` responde un objeto fijo y no comprueba Elasticsearch ni
  LibreOffice (`apps/utils/views.py: healthcheck`).
- [VERIFICADO] El logging usa configuración Django y `DJANGO_LOG_LEVEL`.
- [VERIFICADO] No se identificaron métricas, tracing ni correlation ID implementado.
- [NO VERIFICADO] Agregación externa de logs o monitoreo del entorno.

## Verificación segura

```bash
python manage.py check
python manage.py test
docker build -t observatorios-crud osiris
```

Las pruebas pueden requerir Elasticsearch y LibreOffice. Antes de ejecutarlas se
debe confirmar que no apunten a datos compartidos. No hay comando de lint local
declarado.

## Troubleshooting con evidencia

| Síntoma | Comprobación no destructiva |
|---|---|
| Falla al iniciar por Elasticsearch | Revisar presencia, no valor, de las variables `ELASTICSEARCH_*`; settings exige usuario y contraseña no vacíos. |
| Red `elastic_net` ausente | Levantar primero infraestructura o crear la red local según README. |
| Swagger difiere del runtime | Usar `osiris/osiris/urls.py`, `apps/*/urls.py` y `views.py`; consultar [`../api/diferencias-contrato.md`](../api/diferencias-contrato.md). |
| Vista previa 503/504 | Comprobar ejecutable/usuario LibreOffice, límites y timeout por nombre de variable. |
| Nginx no responde | Contrastar puerto publicado 80 con `listen 8080`. |

## Recuperación

- [NO VERIFICADO] No se halló procedimiento versionado de snapshot/restore de
  Elasticsearch, RPO/RTO, rollback de mappings ni recuperación de archivos.
- [PROPUESTA] Definir y probar esos procedimientos en una especificación TO-BE
  autorizada; no improvisarlos desde este documento.
