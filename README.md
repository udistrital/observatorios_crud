
# Proyecto Observatorios CRUD

## Punto de entrada técnico
- `AGENTS.md`
- `docs/README.md`
- `docs/specs/README.md`

Backend CRUD del dominio Observatorios, implementado en Django/DRF, con integracion a Elasticsearch.

## Especificaciones Técnicas

### Tecnologías Implementadas

- [Django](https://www.djangoproject.com/): Framework principal para el desarrollo web.
- [Django Rest Framework](https://www.django-rest-framework.org/): Para la creación de la API RESTful.
- [Elasticsearch](https://www.elastic.co/es/elasticsearch): Motor de búsqueda utilizado para indexar y realizar consultas avanzadas sobre los datos.
- [Docker](https://www.docker.com/): Para contenerizar la aplicación.
- [Docker Compose](https://docs.docker.com/compose/): Para orquestar contenedores y facilitar la configuración de la base de datos y otros servicios.

### Variables de entorno

La API usa un unico archivo `osiris/.env` y selecciona comportamiento por la presencia de `PARAMETER_STORE` (local si está vacío, SSM si está definido):

- Local (sin PARAMETER_STORE): usa credenciales de Elasticsearch desde `.env`.
- Remoto (con PARAMETER_STORE): usa credenciales desde AWS SSM.

Plantilla base: `osiris/.env.template`.


### Requisitos

- **Docker**
- **Docker Compose**
- (Opcional) acceso SSH si usaras tunel a Elasticsearch remoto

## Ejecucion local

### 1. Ubicarse en el proyecto

Clona el repositorio del proyecto:

```bash
cd observatorios_crud
```

### 2. Configurar `.env`

Crear archivo desde plantilla:

```bash
cp osiris/.env.template osiris/.env
```

Editar `osiris/.env` segun tu escenario.

Variables minimas (local):

```env
DEBUG=true
SECRET_KEY=tu_clave
ALLOWED_HOSTS=localhost,127.0.0.1
ELASTICSEARCH_HOST=host.docker.internal
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_MAIN_INDEX=
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
```

### 3. Levantar solo API CRUD

Script recomendado:

```bash
./run_crud.sh
```

Esto construye/levanta el contenedor `osiris_back` en `http://localhost:8000`.

Verifica estado:

```bash
docker ps --filter name=osiris_back
```

### 4. (Opcional) Levantar infraestructura local

Si necesitas Elasticsearch/Kibana/Nginx local:

```bash
./infraestructura/run_infra.sh
```

Servicios esperados:

- Elasticsearch: `http://localhost:9200`
- Kibana: `http://localhost:5601`
- Nginx: `http://localhost:80`


### 5. (Opcional) Usar Elasticsearch remoto por tunel SSH

Abrir tunel en otra terminal:

```bash
ssh -i llave.pem -L 0.0.0.0:9200:localhost:9200 {user}@{host}
```

Con ese tunel, la API local puede consumir Elasticsearch via `host.docker.internal:9200`.

### 6. Detener servicios

- Detener API CRUD:

```bash
docker compose -f osiris/docker-compose.yml down
```

- Detener infraestructura local:

```bash
docker compose -f infraestructura/docker-compose.yml down
```

## Endpoints utiles

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/documentacion/swagger/`
- ReDoc: `http://localhost:8000/documentacion/redoc/`

## Scripts operativos

- API CRUD: `./run_crud.sh`
- Infraestructura local: `infraestructura/run_infra.sh`

## Troubleshooting mínimo

1. **Error: "network elastic_net not found"**  
   Ejecuta primero:
   ```bash
   ./infraestructura/run_infra.sh
   ```
   o crea la red manualmente:
   ```bash
   docker network create elastic_net
   ```

2. **La API no conecta a Elasticsearch en local**  
   Revisa en `osiris/.env`:
   - `ELASTICSEARCH_HOST=host.docker.internal`
   - `ELASTICSEARCH_PORT=9200`
   y confirma que Elasticsearch esté arriba (`docker ps`).

3. **Modos con SSM fallan en local si PARAMETER_STORE no está definido**
   Estos modos requieren parámetros en AWS SSM (`PARAMETER_STORE`, `AWS_REGION`).
   Para pruebas locales, deja `PARAMETER_STORE` vacío o sin definir.

## Licencia

Este proyecto es parte de `observatorios`.

`observatorios_crud` es software libre: puedes redistribuirlo y/o modificarlo bajo los términos de la **GNU General Public License** tal como está publicada por la **Free Software Foundation**, ya sea la versión 3 de la Licencia, o (a tu elección) cualquier versión posterior.

Este programa se distribuye con la esperanza de que sea útil, pero **SIN NINGUNA GARANTÍA**; incluso sin la garantía implícita de **COMERCIABILIDAD** o **IDONEIDAD PARA UN PROPÓSITO PARTICULAR**. Consulta la [GNU General Public License](https://www.gnu.org/licenses/) para más detalles.

[https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).
