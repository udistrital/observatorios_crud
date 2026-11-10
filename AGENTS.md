# AGENTS.md - Guia tecnica de observatorios_crud

## Proposito del repositorio

`observatorios_crud` expone la API REST del dominio Observatorios. Administra procesos, factores, caracteristicas, aspectos, estructuras de evidencia, campos, registros, observatorios y configuraciones de graficos.

Es un backend independiente del cliente. Persiste los datos funcionales principalmente en Elasticsearch. SQLite existe para las aplicaciones internas de Django, no para los documentos de dominio. En el flujo documental activo, este repositorio guarda metadatos y el hash del archivo; el binario pertenece al Gestor Documental consumido por `observatorios_cliente`.

## Tecnologias verificadas

- Python 3.11 en el `Dockerfile`.
- Django 4.2.17.
- Django REST Framework 3.15.2.
- Elasticsearch Python client 8.17.0.
- Elasticsearch y Kibana 8.10.2 en la composicion principal de infraestructura.
- drf-yasg para OpenAPI, Swagger UI y ReDoc.
- python-dotenv para configuracion local.
- Gunicorn en la imagen de aplicacion.
- LibreOffice Writer/Calc para vistas previas temporales de Word y Excel.
- Docker y Docker Compose para operacion local y despliegue.

Las dependencias Python estan en `osiris/requirements.txt`.

## Archivos que se deben leer primero

1. `README.md`: instalacion, configuracion y operacion.
2. `osiris/requirements.txt`: dependencias y versiones.
3. `osiris/osiris/settings.py`: Django, Elasticsearch, CORS, media y REST Framework.
4. `osiris/osiris/urls.py`: prefijos globales, documentacion y healthcheck.
5. `osiris/apps/<dominio>/urls.py`: registro de rutas del dominio.
6. `osiris/apps/<dominio>/views.py`: validacion, flujo y persistencia.
7. `osiris/apps/<dominio>/serializers.py` y `models.py`: contratos y acceso a Elasticsearch.
8. `docs/README.md`: índice canónico de arquitectura, API, datos, operación y SDD.
9. `docs/specs/README.md`, `docs/specs/backlog_specs.md` y `docs/sdd/matriz_interacciones.md`: reglas SDD y contratos entre repositorios.

Para Estructuras Documentales revise como minimo `apps/estructuras/`, `apps/campos/`, los archivos de `apps/aspectos/` que sincronizan referencias y el contrato consumidor en `observatorios_cliente`.

## Estructura del proyecto

```text
observatorios_crud/
|-- docs/                    Arquitectura, flujos, specs y matrices SDD.
|-- infraestructura/         Compose de Elasticsearch, Kibana y Nginx.
|-- osiris/
|   |-- apps/                Aplicaciones Django por dominio.
|   |-- osiris/              Settings, URLs, WSGI, ASGI y soporte AWS SSM.
|   |-- manage.py            CLI de Django.
|   |-- requirements.txt     Dependencias Python.
|   |-- Dockerfile           Imagen Python 3.11/Gunicorn.
|   |-- docker-compose.yml   API local en el puerto 8000.
|   `-- .env.template        Variables de ejemplo sin credenciales reales.
|-- swagger/                 Esquemas Swagger 2 históricos.
|-- run_crud.sh              Prepara .env si falta y levanta la API.
`-- .drone.yml               Build, analisis y despliegue CI.
```

Aplicaciones relevantes:

- `apps/estructuras`: crea y administra estructuras de evidencia.
- `apps/campos`: administra definicion de campos y registros embebidos.
- `apps/aspectos`: contiene referencias resumidas a estructuras.
- `apps/datos`: rutas heredadas de datos y `datosArchivo`.
- `apps/elasticsearch_utils`: cliente y utilidades comunes de Elasticsearch.
- `apps/utils`: healthcheck y manejador de excepciones DRF.

No existen capas `services/` ni `repositories/`. No documente ni implemente sobre una arquitectura que el proyecto no usa.

## Arquitectura y flujo de una peticion

```text
HTTP request
  -> osiris/osiris/urls.py
  -> apps/<dominio>/urls.py
  -> APIView o ViewSet en apps/<dominio>/views.py
  -> serializer o validacion manual
  -> modelo descriptor/utilidad y cliente Elasticsearch
  -> indice Elasticsearch
  -> Response DRF JSON
```

Los views contienen actualmente la mayor parte de la logica y llaman directamente modelos/utilidades de Elasticsearch. Los modelos de dominio no heredan de `django.db.models.Model`; describen indices, mappings y operaciones de Elasticsearch.

## Registro y versionado de endpoints

`osiris/osiris/urls.py` monta las aplicaciones bajo `api/<str:version>/`. El segmento se usa como prefijo pero no se valida contra una lista de versiones. El cliente vigente usa `v1`.

Familias principales:

- `/api/{version}/procesos`
- `/api/{version}/factores`
- `/api/{version}/caracteristicas`
- `/api/{version}/aspectos`
- `/api/{version}/estructuras-evidencias`
- `/api/{version}/campos/estructuras/`
- `/api/{version}/campos/datos/`
- `/api/{version}/campos/archivos/`
- `/api/{version}/datosArchivo`
- `/api/{version}/observatorios`

Swagger y ReDoc se generan con drf-yasg en `/documentacion/swagger/` y `/documentacion/redoc/`. Los archivos estaticos de `swagger/` pueden tener diferencias con las rutas ejecutables; confirme siempre `urls.py`, `views.py` y `docs/api/openapi.yaml`.

El manejador `apps.utils.views.custom_exception_handler` normaliza excepciones procesadas por DRF, pero varios views retornan manualmente `detalle`, `error` o ambos. Preserve el contrato de la ruta que modifica y no exponga excepciones internas nuevas.

## Persistencia

### Elasticsearch

El cliente se construye con `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_SCHEME`, usuario y contrasena. Con `PARAMETER_STORE` se obtienen credenciales desde AWS SSM; sin esa variable se leen del entorno local.

Las estructuras se almacenan en indices dinamicos con forma `atlas_estructura_<tipo>_<uuid>`. El documento de estructura incluye `campos` y una lista `data`. El aspecto relacionado conserva una referencia resumida. Cambios que afecten ambos documentos no cuentan con una transaccion entre indices.

### SQLite y migraciones

`settings.py` configura `db.sqlite3` para componentes internos de Django. Los directorios de migraciones de las aplicaciones de dominio no contienen migraciones funcionales. No cree una migracion SQL para un cambio en documentos Elasticsearch salvo que se introduzca deliberadamente un modelo Django.

## Estructuras Documentales - estado actual

### Estructura y registros

`POST /api/{version}/estructuras-evidencias/` crea estructuras `Documental` o `Tabla`; ambas usan el mismo modelo de `campos` y `data`. `GET`, `PUT/PATCH` y `DELETE` sobre `/{id}/` consultan, actualizan metadatos o desactivan la estructura.

`apps/campos/views.py` expone:

- `GET /campos/tipos`: tipos de campo disponibles.
- `GET|PUT|PATCH|DELETE /campos/estructuras/{estructura_id}/`: estructura y campos.
- `GET|POST|DELETE /campos/datos/{estructura_id}/`: consulta, creacion y limpieza de registros.
- `PUT|PATCH|DELETE /campos/datos/{estructura_id}/{registro_id}/`: actualizacion, estado y eliminacion.

Los registros se guardan dentro de la lista `data` de la estructura. El identificador visible es la posicion del arreglo y puede cambiar al eliminar elementos.

### Binarios y formatos

Este repositorio no almacena el binario documental. El cliente guarda en un campo reservado `hash` el identificador retornado por el Gestor Documental externo. La excepción es `POST /campos/archivos/vista-previa/`, que recibe temporalmente Word o Excel, valida el formato, convierte a PDF `inline` y elimina los temporales; no carga ni conserva el original.

`/campos/archivos/{estructura_id}/` no es un upload: `ArchivosDatosView` hereda sin cambios de `DatosEstructuraDocumentoView`, por lo que se comporta como `/campos/datos/` y maneja JSON.

La vista previa exige sintácticamente un header `Authorization: Bearer <texto>`, pero no valida firma, identidad, expiración ni rol. Además valida extensión/MIME/firma, rechaza macros y recursos externos, limita tamaño, frecuencia y tiempo, y ejecuta LibreOffice con un usuario dedicado. Sus límites y ejecutable se configuran mediante las variables `LIBREOFFICE_*` y `DOCUMENT_PREVIEW_*` de `.env.template`.

Las rutas heredadas `/datosArchivo/...` pretenden manejar metadata, no bytes. En el codigo actual dependen de atributos antiguos de `EstructuraCamposModelo`; no las asuma operativas sin reproducir y corregir ese flujo.

La carga de imagenes de observatorios en `apps/elasticsearch_utils/models.py` es otro caso de uso y no constituye almacenamiento documental.

## Integracion con observatorios_cliente

El contrato activo es:

```text
observatorios_cliente
  -> Gestor Documental: carga/consulta/eliminacion del binario
  -> observatorios_crud: estructura, campos, metadatos y hash
  -> Elasticsearch: documento de estructura y registros embebidos
```

El cliente configura este API mediante `MAIN_BACKEND` y usa las familias `/estructuras-evidencias/` y `/campos/...`. No copie aqui detalles internos de componentes Vue; revise el payload consumidor antes de modificar campos o respuestas.

## Configuracion por variables de entorno

### Servidor Django

- `SECRET_KEY`
- `DEBUG` y `ALLOWED_HOSTS` aparecen en la plantilla, aunque el codigo actual fija `DEBUG=True` y `ALLOWED_HOSTS=["*"]`.
- `DJANGO_LOG_LEVEL`
- `STATIC_ROOT`
- `SECURE_SSL_REDIRECT`

### Elasticsearch

- `ELASTICSEARCH_HOST`
- `ELASTICSEARCH_PORT`
- `ELASTICSEARCH_SCHEME`
- `ELASTICSEARCH_MAIN_INDEX`
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`

El arranque falla si usuario o contrasena de Elasticsearch quedan vacios.

### AWS SSM

- `PARAMETER_STORE`
- `AWS_REGION`

### CORS

- `CORS_ALLOW_ALL_ORIGINS`
- `CORS_ALLOWED_ORIGINS`

Estas variables aparecen en `.env.template`, pero el comportamiento CORS actual se decide en codigo segun `PARAMETER_STORE`.

Nunca escriba valores sensibles en documentacion, pruebas, logs ni commits. El archivo real `osiris/.env` y variantes locales no son documentacion.

## Comandos reales

Desde la raiz del repositorio:

```bash
cp osiris/.env.template osiris/.env  # crea configuracion local para completar
./infraestructura/run_infra.sh       # levanta Elasticsearch/Kibana/Nginx
./run_crud.sh                        # construye y levanta osiris_back
docker compose -f osiris/docker-compose.yml down
docker compose -f infraestructura/docker-compose.yml down
```

Ejecucion Python directa desde `osiris/`, con entorno y Elasticsearch configurados:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
python manage.py check
python manage.py test
```

Build de imagen:

```bash
docker build -t observatorios-crud osiris
```

No hay configuracion de Ruff, Black, Flake8, pylint, mypy o pytest. El formato/lint automatizado disponible en CI es el analisis Sonar; no invente un comando local de lint.

## Reglas para agentes

- Revise ruta global, ruta de aplicacion y metodo del view antes de editar.
- Identifique serializer, modelo Elasticsearch, indice y referencias denormalizadas.
- No invente capas `service` o `repository`; agreguelas solo si un cambio arquitectonico aprobado lo exige.
- No cree endpoints duplicados si una ruta vigente representa el recurso.
- No cambie payloads o codigos de respuesta sin revisar `observatorios_cliente` y la matriz SDD.
- No trate `/campos/archivos/` como almacenamiento binario mientras siga siendo un alias JSON.
- Valide datos del lado servidor; la validacion del cliente no es una frontera de seguridad.
- Preserve el manejo de errores de la ruta y no retorne `str(error)` nuevo a consumidores.
- Evite migraciones SQL para datos que viven en Elasticsearch.
- No exponga credenciales, rutas privadas ni contenido de archivos `.env`.
- Mantenga cambios fuera del alcance separados.
- Toda modificacion de endpoints o datos inicia con spec TO-BE y actualiza `docs/sdd/matriz_interacciones.md` si afecta consumidores.
- Ejecute pruebas, `manage.py check` y build aplicables antes de entregar.

## Checklist para agentes

Antes de modificar:

- Leer `AGENTS.md`, `README.md` y las convenciones SDD.
- Identificar `urls.py`, view, serializer y modelo/utilidad.
- Confirmar indice Elasticsearch y estructura real del documento.
- Revisar request, response, errores y consumidor frontend.
- Comprobar si la ruta es vigente, alias o legado.
- Confirmar variables de entorno y servicios requeridos.

Despues de modificar:

- Ejecutar `python manage.py check`.
- Ejecutar `python manage.py test` o la suite de la aplicacion afectada.
- Construir la imagen Docker cuando cambien dependencias o configuracion.
- Probar casos exitosos, validaciones, 404 y errores de persistencia.
- Verificar el endpoint real con Elasticsearch disponible.
- Probar la integracion con `observatorios_cliente` si cambio el contrato.
- Actualizar Swagger/specs/matriz y documentacion aplicable.
