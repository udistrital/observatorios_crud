#PRODUCCIÓN

#FROM python:3.11
#ENV PYTHONUNBUFFERED=1
#WORKDIR /app
#COPY osiris/requirements.txt /app/requirements.txt
#RUN pip install --no-cache-dir --upgrade pip && \
#    pip install --no-cache-dir -r requirements.txt
#COPY . /app/
#CMD ["sh", "-c", "python osiris/manage.py migrate && gunicorn --workers 2 --bind 0.0.0.0:8000 osiris.osiris.wsgi:application"]


FROM python:3.11
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        libreoffice-calc \
        libreoffice-writer && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    useradd --system --no-create-home --shell /usr/sbin/nologin documentconverter

COPY . /app/

CMD ["sh", "-c", "python manage.py migrate && \
    gunicorn --workers 2 --timeout 40 --graceful-timeout 10 --bind 0.0.0.0:8000 osiris.wsgi:application"]



#LOCAL PARA DESARROLLO

#FROM python:3.11
#ENV PYTHONUNBUFFERED=1
#WORKDIR /app
#COPY requirements.txt /app/requirements.txt
#RUN pip install --no-cache-dir --upgrade pip && \
#    pip install --no-cache-dir -r requirements.txt
#COPY . /app/
#CMD ["sh", "-c", "python manage.py migrate && gunicorn --workers 2 --bind 0.0.0.0:8000 osiris.wsgi:application"]
