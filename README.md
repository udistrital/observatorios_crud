# Observatorios CRUD

## Descripcion

`observatorios_crud` es la API REST del sistema Observatorios. Expone operaciones para procesos, factores, caracteristicas, aspectos, estructuras de evidencia, campos, registros, observatorios y graficos. La informacion funcional se indexa principalmente en Elasticsearch.

El API es consumido por `observatorios_cliente`. En el flujo documental vigente, el CRUD conserva metadatos y el hash que identifica al archivo; los binarios se almacenan y consultan a traves de un Gestor Documental externo.

La guia tecnica para agentes de codigo esta en `AGENTS.md`; la documentacion SDD se encuentra en `docs/`.

## Tecnologias

- Python 3.11 en Docker.
- Django 4.2.17.
- Django REST Framework 3.15.2.
- Elasticsearch client 8.17.0.
- Elasticsearch y Kibana 8.10.2 en la infraestructura Compose principal.
- drf-yasg para OpenAPI, Swagger UI y ReDoc.
- LibreOffice Writer/Calc para convertir temporalmente Word y Excel a PDF.
- SQLite para componentes internos de Django.
- Docker, Docker Compose y Gunicorn.

Consulte `osiris/requirements.txt` para el inventario completo. Algunas dependencias auxiliares no tienen version fijada; no se debe inferir una version exacta para ellas.

## Requisitos

Opcion recomendada:

- Docker.
- Docker Compose.
- Red Docker externa `elastic_net`.
- Elasticsearch accesible y credenciales validas.

Opcion de ejecucion directa:

- Python 3.11, de acuerdo con la imagen del proyecto.
- pip.
- Elasticsearch accesible.

El stack de infraestructura publica Elasticsearch en 9200 y Kibana en 5601.

## Configuracion

La plantilla local esta en `osiris/.env.template`:

```bash
cp osiris/.env.template osiris/.env
```

Complete valores locales sin subir el archivo real al repositorio. Las credenciales de Elasticsearch no pueden quedar vacias porque `settings.py` detiene el arranque.

### Servidor

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DJANGO_LOG_LEVEL`
- `STATIC_ROOT`
- `SECURE_SSL_REDIRECT`

`DEBUG` y `ALLOWED_HOSTS` estan presentes en la plantilla, pero el codigo actual fija `DEBUG=True` y `ALLOWED_HOSTS=["*"]`.

### Elasticsearch

- `ELASTICSEARCH_HOST`
- `ELASTICSEARCH_PORT`
- `ELASTICSEARCH_SCHEME`
- `ELASTICSEARCH_MAIN_INDEX`
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`

`ELASTICSEARCH_SCHEME` tiene valor predeterminado `http` en el codigo aunque no aparece en la plantilla actual. Muchos indices usan nombres `atlas_*` definidos en codigo.

### AWS SSM

- `PARAMETER_STORE`
- `AWS_REGION`

Sin `PARAMETER_STORE`, las credenciales se leen del entorno local. Con un valor no vacio, se consultan parametros AWS SSM bajo la ruta construida por `settings.py`.

### CORS

- `CORS_ALLOW_ALL_ORIGINS`
- `CORS_ALLOWED_ORIGINS`

Estas variables figuran en la plantilla, pero la configuracion efectiva actual distingue local/remoto mediante `PARAMETER_STORE`.

No incluya valores sensibles en documentacion ni commits.

## Instalacion y ejecucion con Docker

### 1. Preparar infraestructura

```bash
./infraestructura/run_infra.sh
```

El script prepara la red `elastic_net` y levanta los servicios definidos en `infraestructura/docker-compose.yml`.

### 2. Preparar la API

```bash
cp osiris/.env.template osiris/.env
```

Complete en `osiris/.env` la conexion a Elasticsearch y las variables necesarias.

### 3. Levantar el CRUD

```bash
./run_crud.sh
```

Si `osiris/.env` no existe, el script lo crea desde la plantilla. Luego construye y levanta `osiris_back`, ejecuta migraciones y arranca Django en:

```text
http://localhost:8000
```

### 4. Detener servicios

```bash
docker compose -f osiris/docker-compose.yml down
docker compose -f infraestructura/docker-compose.yml down
```

## Ejecucion directa con Python

Desde `observatorios_crud/osiris`, con las variables y Elasticsearch preparados:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

La aplicacion se sirve en el puerto 8000.

## Arquitectura

```text
osiris/
|-- apps/                 aplicaciones Django por dominio
|   |-- estructuras/      estructuras de evidencia
|   |-- campos/           definicion de campos y datos embebidos
|   |-- aspectos/         aspectos y referencias a estructuras
|   |-- datos/            contratos heredados de datos/datosArchivo
|   |-- observatorios/    observatorios e imagenes asociadas
|   `-- utils/            healthcheck y errores DRF
|-- osiris/               settings, URLs, WSGI, ASGI y AWS SSM
|-- manage.py
|-- requirements.txt
|-- Dockerfile
`-- docker-compose.yml
```

Los snapshots Swagger 2 históricos están en `../swagger/` respecto de esta carpeta
`osiris/`; el contrato AS-IS mantenido está en `docs/api/openapi.yaml` desde la
raíz del repositorio.

El flujo habitual es `urls.py -> APIView/ViewSet -> serializer o validacion manual -> modelo/utilidad -> Elasticsearch -> Response`. No hay capas separadas de servicio y repositorio.

Las estructuras usan indices dinamicos `atlas_estructura_<tipo>_<uuid>` y guardan en un documento la definicion de campos y la lista de registros. Los aspectos mantienen referencias resumidas a sus estructuras.

## Endpoints y documentacion

La API monta sus recursos bajo:

```text
/api/{version}/
```

El cliente actual usa `v1`. El parametro de version es dinamico y no se valida contra una lista cerrada.

- Swagger UI: `http://localhost:8000/documentacion/swagger/`
- ReDoc: `http://localhost:8000/documentacion/redoc/`
- OpenAPI JSON: `http://localhost:8000/documentacion/swagger.json`
- OpenAPI YAML: `http://localhost:8000/documentacion/swagger.yaml`
- Healthcheck: `http://localhost:8000/health/`

Use la documentacion generada para explorar contratos, pero confirme rutas y metodos en `osiris/osiris/urls.py` y `apps/*/urls.py`: los archivos OpenAPI estaticos pueden estar desactualizados.

## Estructuras Documentales

Las estructuras con `tipo_evidencia: "Documental"` se crean mediante `/api/{version}/estructuras-evidencias/`. Comparten la misma representacion de campos y datos que las estructuras `Tabla`.

El cliente usa:

- `/estructuras-evidencias/` para crear y consultar la estructura.
- `/campos/estructuras/{estructura_id}/` para su definicion de campos.
- `/campos/datos/{estructura_id}/` para metadatos y hash.
- `/campos/datos/{estructura_id}/{registro_id}/` para actualizar o eliminar un registro.

El original no se almacena en este API. `observatorios_cliente` lo envia al Gestor Documental y registra aqui el hash retornado. Para visualizar Word y Excel, `POST /campos/archivos/vista-previa/` recibe una copia temporal, valida el formato y retorna un PDF `inline`; los temporales se eliminan al terminar.

El `Dockerfile` instala LibreOffice Writer/Calc. En ejecucion directa debe existir `/usr/bin/libreoffice`; `.env.template` permite configurar ejecutable, usuario, limites, timeout y tasa mediante `LIBREOFFICE_*` y `DOCUMENT_PREVIEW_*`.

La ruta `/campos/archivos/...` existe por compatibilidad, pero se comporta exactamente como `/campos/datos/...`: recibe y retorna JSON, no archivos. Las rutas antiguas `/datosArchivo/...` son de metadata y dependen de un modelo anterior; no deben usarse como evidencia de almacenamiento binario.

## Integracion con el frontend

`observatorios_cliente` configura la URL de este API mediante `MAIN_BACKEND`. En local espera `http://localhost:8000/api/v1`.

El frontend gestiona el binario con otro servicio y envia al CRUD metadatos mas un campo reservado `hash`. Cualquier cambio en nombres de campos, estructura de respuesta, paginacion o codigos HTTP debe comprobarse contra el cliente antes de publicarse.

## Pruebas y verificaciones

Desde `osiris/`:

```bash
python manage.py check
python manage.py test
```

Puede limitar la suite a una aplicacion:

```bash
python manage.py test apps.campos
```

Las pruebas existentes son limitadas y varias operaciones requieren una instancia real de Elasticsearch. No hay configuracion de pytest ni un comando de lint/formato; CI ejecuta analisis Sonar.

## Build

Desde la raiz del repositorio:

```bash
docker build -t observatorios-crud osiris
```

La imagen instala `requirements.txt`, ejecuta migraciones y sirve la aplicacion con Gunicorn en el puerto 8000.

## Solucion de problemas

### `network elastic_net not found`

Levante primero la infraestructura:

```bash
./infraestructura/run_infra.sh
```

O cree la red antes de iniciar solamente la API:

```bash
docker network create elastic_net
```

### El arranque falla por credenciales de Elasticsearch

`settings.py` exige usuario y contrasena no vacios. Complete `ELASTICSEARCH_USERNAME` y `ELASTICSEARCH_PASSWORD` en el entorno local, o configure `PARAMETER_STORE` y AWS SSM para el ambiente remoto.

### La API no conecta con Elasticsearch del host

El Compose agrega `host.docker.internal`. Revise host, puerto, esquema y credenciales en `osiris/.env`, y confirme que Elasticsearch responda en el puerto configurado.

### El Nginx de infraestructura no responde en el puerto publicado

La composicion publica `80:80`, pero la configuracion actual de Nginx escucha internamente en 8080. Esta inconsistencia debe corregirse en la infraestructura o en el mapeo antes de depender de ese proxy.

### Swagger no coincide con una respuesta

Confirme el view ejecutable y el `urls.py`. Parte del esquema estatico conserva metodos o codigos de estado anteriores.

## Licencia

Este proyecto se distribuye bajo GNU General Public License, version 3 o posterior. Consulte el texto de la GPL para sus condiciones.
