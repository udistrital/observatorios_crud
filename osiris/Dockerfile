# Usa una imagen oficial de Python como base
FROM python:3.11

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de la aplicación al contenedor
COPY . .

# Copia el archivo .env desde la carpeta padre
#COPY .env .env

ENV PYTHONUNBUFFERED=1

# Instala las dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Ejecutamos el servidor
CMD ["sh", "-c", "python manage.py migrate && gunicorn --workers 2 --bind 0.0.0.0:8000 osiris.wsgi:application"]
