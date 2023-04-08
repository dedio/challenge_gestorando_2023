#  app.py
#  
#  Copyright 2023 Juan Manuel Dedionigis <jmdedio@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import requests
from flask import Flask, jsonify, make_response
import psycopg2
from celery import Celery
import celeryconfig


CONEXION = {
    'user':'postgres',
    'password':'password',
    'host':'127.0.0.1',
    'port':'5432',
    'database':'gestorando'
}


# Actualiza las estadísticas
def set_stats():
    conn = psycopg2.connect(
        user=CONEXION['user'],
        password=CONEXION['password'],
        host=CONEXION['host'],
        port=CONEXION['port'],
        database=CONEXION['database'],
    )
    cur = conn.cursor()

    # Levanta los datos de la tabla films
    # calculando el promedio de votos y sumando la cantidad de films por año
    cur.execute("""SELECT year, AVG(vote_average), SUM(id)  FROM films GROUP BY year""")
    datos = cur.fetchall()

    # Recorre y actualiza o inserta los registros según sea el caso
    for d in datos:
        check = """SELECT year FROM stats WHERE year = {}""".format(d[0])
        cur.execute(check)
        if cur.fetchone():
            update = """UPDATE stats SET year={}, vote_average={}, quantity={} WHERE year={}""".format(
                d[0],
                d[1],
                d[2],
                d[0]
            )
            cur.execute(update)
        else:
            insert = """INSERT INTO stats(year, vote_average, quantity) VALUES ({}, {}, {})""".format(
                d[0],
                d[1],
                d[2]
            )
            cur.execute(insert)
    conn.commit()
    conn.close()


app = Flask(__name__)
app.config.from_object('config')

# Crea el contexto de tareas en Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['BROKER_URL']
    )
    celery.conf.update(app.config)
    celery.config_from_object(celeryconfig)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery

celery = make_celery(app)


# Consulta la API y persiste los datos
@app.route("/", methods=['GET'])
def index():
    # Consulta la API y guarda los datos
    datos = {}
    for i in range(1, 11, 1):
        pag = requests.get('https://api.themoviedb.org/3/movie/top_rated?api_key=01c4f26878d83efffed275d3d3eebc02&page=' + str(1))
        datos[str(i)] = pag.json()

    # Actualiza la base
    for d in datos:
        for f in datos[d]['results']:
            conn = psycopg2.connect(
                user=CONEXION['user'],
                password=CONEXION['password'],
                host=CONEXION['host'],
                port=CONEXION['port'],
                database=CONEXION['database'],
            )
            cur = conn.cursor()

            # Si la película no está en la base, la inserta
            cur.execute("""SELECT id FROM films WHERE id = {}""".format(f['id']))
            if not cur.fetchone():
                insert = """INSERT INTO films(id, vote_average, year) VALUES ({}, {}, {})""".format(
                    f['id'],
                    f['vote_average'],
                    int(f['release_date'][:4])
                )
                cur.execute(insert)

            # Si el promedio de votos cambió, actualiza el registro
            cur.execute("""SELECT vote_average FROM films WHERE id = {} AND vote_average = {}""".format(
                f['id'], 
                f['vote_average']
            ))
            if not cur.fetchone():
                update = """UPDATE films SET id={}, vote_average={}, year={} WHERE id={}""".format(
                    f['id'],
                    f['vote_average'],
                    int(f['release_date'][:4]),
                    f['id']
                )
                cur.execute(update)
            conn.commit()
            conn.close()

    # Ejecuta la actualización de estadísticas
    set_stats()

    return datos

# Muestra las estadísticas
@app.route("/stats", methods=['GET'])
def stats():
    conn = psycopg2.connect(
        user=CONEXION['user'],
        password=CONEXION['password'],
        host=CONEXION['host'],
        port=CONEXION['port'],
        database=CONEXION['database'],
    )
    cur = conn.cursor()
    cur.execute("""SELECT ROW_TO_JSON(c) FROM (SELECT * FROM stats) c""")
    datos = cur.fetchall()
    conn.commit()
    conn.close()

    return make_response(jsonify(datos))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
