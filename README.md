
# Proyecto Observatorios

Este proyecto es un sistema de gestión para el manejo de datos de observatorios, implementando operaciones CRUD y la integración con Elasticsearch para la búsqueda avanzada y eficiente de datos. Además, se incluye la implementación de medidas de seguridad para proteger los recursos del sistema.

## Especificaciones Técnicas

### Tecnologías Implementadas

- [Django](https://www.djangoproject.com/): Framework principal para el desarrollo web.
- [Django Rest Framework](https://www.django-rest-framework.org/): Para la creación de la API RESTful.
- [Elasticsearch](https://www.elastic.co/es/elasticsearch): Motor de búsqueda utilizado para indexar y realizar consultas avanzadas sobre los datos.
- [Docker](https://www.docker.com/): Para contenerizar la aplicación.
- [Docker Compose](https://docs.docker.com/compose/): Para orquestar contenedores y facilitar la configuración de la base de datos y otros servicios.

### Variables de Entorno

El proyecto utiliza las siguientes variables de entorno, que deben ser configuradas en el archivo `settings.py` o en un archivo `.env`:

```
DJANGO_SECRET_KEY=[clave secreta de Django]
ELASTICSEARCH_HOST=[host de Elasticsearch]
ELASTICSEARCH_PORT=[puerto de Elasticsearch]
DEBUG=[True o False, habilitar/deshabilitar depuración]
```

### Requisitos

- **Python 3.x**
- **Django 3.x+**
- **Django Rest Framework 3.x+**
- **Elasticsearch 7.x+**
- **Docker (opcional, para contenedores)**

## Instalación

### 1. Clonar el repositorio

Clona el repositorio del proyecto:

```bash
https://github.com/udistrital/observatorios_crud.git
cd observatorios
```

### 2. Crear un entorno virtual

Es recomendable crear un entorno virtual para gestionar las dependencias del proyecto.

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows usa venv\Scripts\ctivate
```

### 3. Instalar dependencias

Instalar las dependencias necesarias utilizando `pip`:

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Crea un archivo `.env` en la raíz del proyecto y agrega las variables de entorno necesarias. También puedes configurarlas directamente en el archivo `settings.py` si prefieres no usar un archivo `.env`.


### 5. Iniciar el servidor

Inicia el servidor de desarrollo de Django:

```bash
python manage.py runserver
```

El servidor estará disponible en `http://127.0.0.1:8000/`.