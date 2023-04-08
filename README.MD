Challenge Gestorando 2023
===================

Requisitos
----------
+ Python 3.6
+ Flask 2.0.3
+ Psycopg2 2.7.7
+ Requests 2.27.1
+ Celery 5.1.2
+ PostgreSQL 9.5.25

Ejecución
---------
En la consola de comandos:
+ Crear el entorno virtual
$ virtualenv venv
+ Activar el entorno virtual
$ source venv/bin/activate
+ Instalar las librerías
$ pip install -r requiriments.txt
+ Descargar, compilar y arrancar el servidor Redis
$ bash install_redis.sh
+ Correr celerybeat
$ venv/bin/celery beat -A app.celery --schedule=/tmp/celerybeat-schedule --loglevel=INFO --pidfile=/tmp/celerybeat.pid
+ Correr celery worker
$ venv/bin/celery worker -A app.celery --loglevel=INFO

Comentario
----------
Este proyecto fue desarrollado y probado de manera local, requiere la verificación de archivos de configuración.
