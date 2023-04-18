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
    conn = psycopg2.connect(
        host='care-connect.ciqo0cjvjfaa.us-west-1.rds.amazonaws.com',
        port=5432,
        dbname='care_connect',
        user='postgres',
        password='Samuel1234')
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


@app.route("/productos")
def get_productos():
    g.cursor.execute('SELECT * FROM producto')
    products = g.cursor.fetchall()
    return jsonify(products)


@app.route("/pacientes")
def get_pacientes():
    g.cursor.execute('SELECT * FROM paciente')
    products = g.cursor.fetchall()
    return jsonify(products)


@app.route('/medicos/<int:medico_id>', methods=['GET'])
def get_medico(medico_id):
    g.cursor.execute('SELECT * FROM medico WHERE id = %s', (medico_id, ))
    medico = g.cursor.fetchone()
    return jsonify(medico)


@app.route('/stock')
def get_stock():
    id_instalacion_medica = request.args.get('id_instalacion_medica')

    g.cursor.execute(
        """
        SELECT id_producto, nombre, cantidad FROM stock
        JOIN producto p ON stock.id_producto = p.id
        WHERE id_instalacion_medica = %s
    """, (id_instalacion_medica, ))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre', 'cantidad')
    result = [dict(zip(columns, row)) for row in rows]

    return jsonify(result)


@app.route('/procedimientos')
def get_procedimientos():
    id_instalacion_medica = request.args.get('id_instalacion_medica')

    g.cursor.execute(
        """
        SELECT id_procedimiento, nombre FROM procedimientos
        WHERE id_instalacion_medica = %s
      
    """, (id_instalacion_medica, ))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre')
    result = [dict(zip(columns, row)) for row in rows]

    return jsonify(result)


@app.route('/pruebas-diagnosticas')
def get_pruebas_diagnosticas():
    id_instalacion_medica = request.args.get('id_instalacion_medica')

    g.cursor.execute(
        """
        SELECT id_prueba, nombre FROM pruebas_diagnosticas
        WHERE id_instalacion_medica = %s
      
    """, (id_instalacion_medica, ))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre')
    result = [dict(zip(columns, row)) for row in rows]

    return jsonify(result)


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
    g.cursor.execute(
        "INSERT INTO medico (correo, contraseña, nombre, direccion, num_telefono, id_especialidad_medica, id_instalacion_medica) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (correo, contraseña, nombre, direccion, numTelefono,
         idEspecialidadMedica, idInstalacionMedica))
    g.conn.commit()

    # Return a success message
    return jsonify({'message': 'User registered successfully'}), 201


@app.route("/consulta", methods=["POST"])
def nueva_consulta():
    # Get the registration data from the request
    data = request.json
    consulta = data['consulta']
    bitacora = data['bitacora']
    pruebas = data['pruebas']
    medicamentos = data['medicamentos']
    procedimientos = data['procedimientos']

    # Insert the data into the database
    g.cursor.execute(
        "INSERT INTO consulta (id_paciente, id_instalacion, id_medico) VALUES (%s, %s, %s) RETURNING id_consulta",
        (consulta['idPaciente'], consulta['idInstalacion'],
         consulta['idMedico']))
    id_consulta = g.cursor.fetchone()[0]
    g.conn.commit()

    g.cursor.execute(
        "INSERT INTO bitacora (id_consulta, presion_arterial, peso, expediente, diagnostico, eficacia) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_bitacora",
        (id_consulta, bitacora['presion'], bitacora['peso'],
         bitacora['expediente'], bitacora['diagnostico'],
         bitacora['eficaciaTratamiento']))
    g.conn.commit()
    id_bitacora = g.cursor.fetchone()[0]

    for prueba in pruebas:
        g.cursor.execute(
            "INSERT INTO pruebas_diagnosticas_bitacora (id_prueba, id_bitacora) VALUES (%s, %s)",
            (prueba['idPrueba'], id_bitacora))
        g.conn.commit()

    for medicamento in medicamentos:
        g.cursor.execute(
            "INSERT INTO medicamento_bitacora (id_bitacora, id_medicamento, cantidad) VALUES (%s, %s, %s)",
            (id_bitacora, medicamento['idMedicamento'],
             medicamento['cantidad']))
        g.conn.commit()

    for procedimiento in procedimientos:
        g.cursor.execute(
            "INSERT INTO procedimientos_bitacora (id_bitacora, id_procedimiento) VALUES (%s, %s)",
            (id_bitacora, procedimiento['idProcedimiento']))
        g.conn.commit()

    # Return a success message
    return jsonify({'message': 'Consulta agregada exitosamente'}), 201


@app.route("/login_medico", methods=["POST"])
def login_medico():
    # Get the login data from the request
    data = request.json
    correo = data['email']
    contraseña = data['password']

    # Check if the credentials are valid
    g.cursor.execute(
        "SELECT * FROM medico WHERE correo = %s AND contraseña = %s",
        (correo, contraseña))
    medico = g.cursor.fetchone()

    if medico:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({
            'message': 'Medico logged in successfully',
            'id': medico[0],
            'nombre': medico[3]
        }), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route("/registrar_producto", methods=["POST"])
def registrar_producto():
    # Get the product data from the request
    data = request.json
    nombre = data['nombre']
    descripcion = data['descripcion']

    # Insert the data into the database
    g.cursor.execute(
        "INSERT INTO producto (nombre, descripcion) VALUES (%s, %s)",
        (nombre, descripcion))
    g.conn.commit()

    # Return a success message
    return jsonify({'message': 'Producto registrado exitosamente'}), 201


@app.route("/agregar_inventario", methods=["POST"])
def agregar_inventario():
    # Get the product data from the request
    data = request.json
    id_producto = data['id_producto']
    id_instalacion = data['id_instalacion']
    cantidad = data['cantidad']
    fecha = data['fecha']

    # Insert the data into the database
    g.cursor.execute(
        "INSERT INTO stock (id_producto, id_instalacion_medica, cantidad, fecha_exp) VALUES (%s, %s, %s,%s)",
        (id_producto, id_instalacion, cantidad, fecha))
    g.conn.commit()

    # Return a success message
    return jsonify(
        {'message': 'Producto registrado al inventario exitosamente'}), 201


if __name__ == "__main__":
    app.run()
