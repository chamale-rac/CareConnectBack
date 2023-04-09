from flask import Flask, jsonify, g, request
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)


def connect_to_db():
    conn = psycopg2.connect(host='localhost', port=5432,
                            dbname='care_connect', user='postgres', password='admin')
    return conn


@app.before_request
def before_request():
    g.conn = connect_to_db()
    g.cursor = g.conn.cursor()


@app.teardown_request
def teardown_request(exception):
    g.cursor.close()
    g.conn.close()


@app.route("/")
def hello():
    return "This is the test api"


@app.route("/especialidad_medica")
def get_especialidad_medica():
    g.cursor.execute('SELECT * FROM especialidad_medica')
    users = g.cursor.fetchall()
    return jsonify(users)


@app.route("/instalacion_medica")
def get_instalacion_medica():
    g.cursor.execute('SELECT * FROM instalacion_medica')
    users = g.cursor.fetchall()
    return jsonify(users)


@app.route("/registrar_medico", methods=["POST"])
def registrar_medico():
    # Get the registration data from the request
    data = request.json
    correo = data['correo']
    contraseña = data['contraseña']
    nombre = data['nombre']
    direccion = data['direccion']
    numTelefono = data['numTelefono']
    idEspecialidadMedica = data['idEspecialidadMedica']
    idInstalacionMedica = data['idInstalacionMedica']

    # Insert the data into the database
    g.cursor.execute("INSERT INTO medico (correo, contraseña, nombre, direccion, num_telefono, id_especialidad_medica, id_instalacion_medica) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                     (correo, contraseña, nombre, direccion, numTelefono, idEspecialidadMedica, idInstalacionMedica))
    g.conn.commit()

    # Return a success message
    return jsonify({'message': 'User registered successfully'}), 201


if __name__ == "__main__":
    app.run()
