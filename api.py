from flask import Flask, jsonify, g, request
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

# For test dump the RDS database care connect and use the local database.
# local (example)
# conn = psycopg2.connect(host='localhost', port=5432, dbname='care_connect', user='postgres', password='admin')
# external (real)
# conn = psycopg2.connect(host='care-connect.ciqo0cjvjfaa.us-west-1.rds.amazonaws.com', port=5432, dbname='care_connect', user='postgres', password='Samuel1234')


def connect_to_db():
    conn = psycopg2.connect(host='care-connect.ciqo0cjvjfaa.us-west-1.rds.amazonaws.com', port=5432,
                            dbname='care_connect', user='postgres', password='Samuel1234')
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

@app.route("/registrar_paciente", methods=["POST"])
def registrar_paciente():
    # Get the registration data from the request
    data = request.json
    nombres = data['nombres']
    apellidos = data['apellidos']
    correo = data['correo']
    telefono = data['telefono']
    direccion = data['direccion']

    # Insert the data into the database
    g.cursor.execute("INSERT INTO paciente (nombres, apellidos, correo, telefono, direccion) VALUES (%s, %s, %s, %s, %s)",
                     (nombres, apellidos, correo, telefono, direccion))
    g.conn.commit()

    # Return a success message
    return jsonify({'message': 'User registered successfully'}), 201


@app.route("/login_medico", methods=["POST"])
def login_medico():
    # Get the login data from the request
    data = request.json
    correo = data['email']
    contraseña = data['password']

    # Check if the credentials are valid
    g.cursor.execute(
        "SELECT * FROM medico WHERE correo = %s AND contraseña = %s", (correo, contraseña))
    medico = g.cursor.fetchone()

    if medico:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({'message': 'Medico logged in successfully', 'id': medico[0], 'nombre': medico[3]}), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Invalid credentials'}), 401


if __name__ == "__main__":
    app.run()
