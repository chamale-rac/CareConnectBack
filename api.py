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
    especialiades = g.cursor.fetchall()
    return jsonify(especialiades)


@app.route("/instalacion_medica")
def get_instalacion_medica():
    g.cursor.execute('SELECT * FROM instalacion_medica')
    instalaciones = g.cursor.fetchall()
    return jsonify(instalaciones)


@app.route("/get/medico/transferencia")
def get_medicos():
    g.cursor.execute('SELECT id, nombre, id_instalacion_medica FROM medico')
    medicos = g.cursor.fetchall()
    return jsonify(medicos)


@app.route("/medico/transferir", methods=["POST"])
def transferir_medico():
    try:
        # Get the registration data from the request
        data = request.json
        admin = data['admin_id']
        medico = data['medico_id']
        de = data['de']
        hacia = data['hacia']

        # Insert the data into the database
        g.cursor.execute("CALL transferir_medico(%s, %s, %s, %s)",
                         (admin, medico, de, hacia))
        g.conn.commit()

        # Return a success message
        return jsonify({'message': 'Medico transferido successfully'}), 201
    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()

        # Return an error message
        return jsonify({'message': 'Error transferring medico: {}'.format(str(e))}), 500


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


@app.route("/registrar_admin", methods=["POST"])
def registrar_admin():
    # Get the registration data from the request
    data = request.json
    correo = data['correo']
    contraseña = data['contraseña']
    idInstalacionMedica = data['idInstalacionMedica']

    # Insert the data into the database
    g.cursor.execute("INSERT INTO admin (correo, contraseña, id_instalacion_medica) VALUES (%s, %s, %s)",
                     (correo, contraseña, idInstalacionMedica))
    g.conn.commit()

    # Return a success message
    return jsonify({'message': 'Admin registered successfully'}), 201


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
        return jsonify({'message': 'Medico logged in successfully', 'id': medico[0], 'nombre': medico[3], 'role': 'medico'}), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route("/login_admin", methods=["POST"])
def login_admin():
    # Get the login data from the request
    data = request.json
    correo = data['email']
    contraseña = data['password']

    # Check if the credentials are valid
    g.cursor.execute(
        "SELECT * FROM admin WHERE correo = %s AND contraseña = %s", (correo, contraseña))
    admin = g.cursor.fetchone()

    if admin:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({'message': 'Admin logged in successfully', 'id': admin[0], 'id_instalacion_medica': admin[3], 'role': 'admin'}), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/paciente/<int:patient_id>')
def get_paciente(patient_id):
    g.cursor.execute(
        "SELECT * FROM paciente WHERE id = %s", str(patient_id))
    paciente = g.cursor.fetchone()

    if paciente:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({'message': 'Paciente encontrado', 'id': paciente[0], 'nombres': paciente[1], 'apellidos': paciente[2], 'correo': paciente[3], 'telefono': paciente[4], 'direccion': paciente[5]}), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Error, no se encontró el paciente'}), 401


@app.route("/paciente/consultas/<int:patient_id>")
def get_paciente_consultas(patient_id):
    try:
        g.cursor.execute('''
                            SELECT c.id_consulta, im.nombre, m.nombre, c.created_at, bit.diagnostico
                            FROM consulta c
                                JOIN instalacion_medica im ON c.id_instalacion = im.id_instalacion_medica
                                JOIN medico m on c.id_medico = m.id
                                JOIN bitacora bit ON bit.id_consulta = c.id_consulta
                            WHERE c.id_paciente = %s
                        ''', str(patient_id))
        rows = g.cursor.fetchall()
        consultas = []
        for row in rows:
            consulta = {}
            consulta['id'] = row[0]
            consulta['instalacion'] = row[1]
            consulta['author'] = row[2]
            consulta['date'] = row[3]
            consulta['details'] = row[4]
            consultas.append(consulta)
        return jsonify(consultas), 201
    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo consultas: {}'.format(str(e))}), 500


if __name__ == "__main__":
    app.run()
