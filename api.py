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


@app.route("/login_medico", methods=["POST"])
def login_medico():
    # Get the login data from the request
    data = request.json
    correo = data['email']
    contraseña = data['password']

    # Check if the credentials are valid
    g.cursor.execute(
        "SELECT *, get_especialidad_name(id_especialidad_medica), get_instalation_name(id_instalacion_medica) FROM medico WHERE correo = %s AND contraseña = %s",
        (correo, contraseña))
    medico = g.cursor.fetchone()

    if medico:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({
            'message': 'Medico logged in successfully',
            'id': medico[0],
            'nombre': medico[3], 'role': 'medico',
            'id_instalacion_medica': medico[7],
            'nombre_especialidad_medica': medico[8],
            'nombre_instalacion_medica': medico[9]
        }), 200
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
        "SELECT *, get_instalation_name(id_instalacion_medica) FROM admin WHERE correo = %s AND contraseña = %s", (correo, contraseña))
    admin = g.cursor.fetchone()

    if admin:
        # If the credentials are valid, return a success message and any relevant data
        return jsonify({'message': 'Admin logged in successfully', 'id': admin[0], 'id_instalacion_medica': admin[3], 'role': 'admin', 'correo': admin[1], 'nombre_instalacion': admin[4]}), 200
    else:
        # If the credentials are invalid, return an error message
        return jsonify({'message': 'Invalid credentials'}), 401


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


@app.route("/buscar_paciente")
def buscar_pacientes():
    search_term = request.args.get('search')
    g.cursor.execute('SELECT * FROM paciente WHERE nombres ILIKE %s OR apellidos ILIKE %s',
                     ('%'+search_term+'%', '%'+search_term+'%'))
    pacientes = g.cursor.fetchall()
    return jsonify(pacientes)


@app.route('/stock')
def get_stock():
    id_instalacion_medica = request.args.get('id_instalacion_medica')

    g.cursor.execute(
        """
        SELECT id_producto, nombre, cantidad, fecha_exp FROM stock
        JOIN producto p ON stock.id_producto = p.id
        WHERE id_instalacion_medica = %s
    """, (id_instalacion_medica, ))

    rows = g.cursor.fetchall()
    print(rows)
    columns = ('id', 'nombre', 'cantidad', 'fecha_exp')
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


@app.route('/enfermedades')
def get_enfermedades():

    g.cursor.execute(
        """
        SELECT id_enfermedad, nombre FROM enfermedades;
    """)

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


@app.route("/consulta", methods=["POST"])
def nueva_consulta():
    # Get the registration data from the request
    data = request.json
    consulta = data['consulta']
    bitacora = data['bitacora']
    pruebas = data['pruebas']
    medicamentos = data['medicamentos']
    procedimientos = data['procedimientos']
    enfermedades = data['enfermedades']

    # Insert the data into the database
    g.cursor.execute(
        "INSERT INTO consulta (id_paciente, id_instalacion, id_medico) VALUES (%s, %s, %s) RETURNING id_consulta",
        (consulta['idPaciente'], consulta['idInstalacion'],
         consulta['idMedico']))
    id_consulta = g.cursor.fetchone()[0]
    g.conn.commit()

    g.cursor.execute(
        "INSERT INTO bitacora (id_consulta, presion_arterial, peso, expediente, diagnostico, eficacia, tratamiento) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_bitacora",
        (id_consulta, bitacora['presion'], bitacora['peso'],
         bitacora['expediente'], bitacora['diagnostico'],
         bitacora['eficaciaTratamiento'], bitacora['tratamiento']))
    g.conn.commit()
    id_bitacora = g.cursor.fetchone()[0]

    for prueba in pruebas:
        g.cursor.execute(
            "INSERT INTO pruebas_diagnosticas_bitacora (id_prueba, id_bitacora) VALUES (%s, %s)",
            (prueba['idPrueba'], id_bitacora))
        g.conn.commit()

    for medicamento in medicamentos:
        g.cursor.execute(
            "CALL medicamento_consulta_resta_stock(%s, %s, %s)",
            (id_bitacora, medicamento['idMedicamento'],
             medicamento['cantidad']))
        g.conn.commit()

    for procedimiento in procedimientos:
        g.cursor.execute(
            "INSERT INTO procedimientos_bitacora (id_bitacora, id_procedimento) VALUES (%s, %s)",
            (id_bitacora, procedimiento['idProcedimiento']))
        g.conn.commit()

    for enfermedad in enfermedades:
        g.cursor.execute(
            "INSERT INTO enfermedades_bitacora (id_bitacora, id_enfermedad) VALUES (%s, %s)",
            (id_bitacora, enfermedad['idEnfermedad']))
        g.conn.commit()

    # Return a success message
    return jsonify({'message': 'Consulta agregada exitosamente'}), 201


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
    try:
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
    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error registrando el producto: {}'.format(str(e))}), 500


@app.route("/doctor/pacientes")
def doctor_pacientes():
    search_term = request.args.get('doctor_id')
    g.cursor.execute('''
                    SELECT *
                        FROM paciente
                        WHERE id IN (SELECT consulta.id_paciente
                                    FROM consulta
                                    WHERE consulta.id_medico = %s
                                    GROUP BY consulta.id_paciente)
                     ''',  (str(search_term)))
    pacientes = g.cursor.fetchall()
    return jsonify(pacientes)


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


@app.route("/notificaciones/<int:instalation_id>")
def get_notificaciones(instalation_id):
    try:
        g.cursor.execute("SELECT * FROM get_notifications(%s)",
                         str(instalation_id))
        rows = g.cursor.fetchall()
        columns = ('tipo_notificacion', 'nombre_producto', 'porcentaje',
                   'cantidad_actual', 'cantidad_inicial', 'fecha_expiracion', 'dias_para_expirar')
        notificaciones = [dict(zip(columns, row)) for row in rows]
        return jsonify(notificaciones), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo ntificaciones: {}'.format(str(e))}), 500


@app.route("/notificaciones/all")
def get_all_notificaciones():
    try:
        g.cursor.execute("SELECT * FROM get_all_notifications()")
        rows = g.cursor.fetchall()
        columns = ('tipo_notificacion', 'nombre_producto', 'porcentaje',
                   'cantidad_actual', 'cantidad_inicial', 'fecha_expiracion', 'dias_para_expirar', 'instalacion_medica')
        notificaciones = [dict(zip(columns, row)) for row in rows]
        return jsonify(notificaciones), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo ntificaciones: {}'.format(str(e))}), 500


@ app.route('/paciente/<int:patient_id>')
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


@ app.route("/paciente/ultima_consulta/<int:patient_id>")
def get_paciente_ultima_bitacora(patient_id):
    try:
        g.cursor.execute('''
                            SELECT b.peso, b.presion_arterial, b.eficacia, b.created_at
                                FROM consulta c
                                JOIN bitacora b on c.id_consulta = b.id_consulta
                            WHERE c.id_paciente = %s
                            ORDER BY c.created_at DESC
                            LIMIT 1;
                        ''', str(patient_id))
        data = g.cursor.fetchone()
        return jsonify({'message': 'Ultima consulta encontrada', 'peso': data[0], 'presion_arterial': data[1], 'eficacia': data[2], 'fecha': data[3]}), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo ultima consulta: {}'.format(str(e))}), 500


@ app.route("/paciente/consulta/<int:consulta_id>")
def get_specific_consulta(consulta_id):
    try:
        g.cursor.execute('''
                            SELECT p.nombres || ' ' || p.apellidos as entire, im.nombre, m.nombre, c.created_at
                            FROM consulta c
                                    JOIN instalacion_medica im ON c.id_instalacion = im.id_instalacion_medica
                                    JOIN medico m on c.id_medico = m.id
                                    JOIN paciente p on c.id_paciente = p.id
                            WHERE c.id_consulta = %s;
                        ''', str(consulta_id))
        data = g.cursor.fetchone()
        return jsonify({'message': 'Consulta encontrada', 'paciente': data[0], 'instalacion': data[1], 'medico': data[2], 'fecha': data[3]}), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo consulta: {}'.format(str(e))}), 500


@ app.route("/bitacora/listas/<int:consulta_id>")
def get_bitacora_listas(consulta_id):
    # Enfermedades
    g.cursor.execute(
        """
            SELECT eb.id_enfermedad, e.nombre
            FROM enfermedades_bitacora eb
                    JOIN enfermedades e ON eb.id_enfermedad = e.id_enfermedad
            WHERE id_bitacora = %s
        """, (str(consulta_id)))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre')
    enfermedades = [dict(zip(columns, row)) for row in rows]

    # Medicamentos
    g.cursor.execute(
        """
            SELECT mb.id_medicamento, p.nombre, mb.cantidad
            FROM medicamento_bitacora mb
                    JOIN producto p ON p.id = mb.id_medicamento
            WHERE id_bitacora = %s
        """, (str(consulta_id)))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre', 'cantidad')
    medicamentos = [dict(zip(columns, row)) for row in rows]

    # Pruebas Diagnósticas
    g.cursor.execute(
        """
            SELECT pdb.id_prueba, pd.nombre
            FROM pruebas_diagnosticas_bitacora pdb
                    JOIN pruebas_diagnosticas pd ON pdb.id_prueba = pd.id_prueba
            WHERE id_bitacora = %s
        """, (str(consulta_id)))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre')
    pruebas = [dict(zip(columns, row)) for row in rows]

    # Procedimientos
    g.cursor.execute(
        """
            SELECT pb.id_procedimento, p.nombre
                FROM procedimientos_bitacora pb
            JOIN procedimientos p ON pb.id_procedimento = p.id_procedimiento
            WHERE id_bitacora = %s
        """, (str(consulta_id)))

    rows = g.cursor.fetchall()
    columns = ('id', 'nombre')
    procedimientos = [dict(zip(columns, row)) for row in rows]

    return jsonify({'message': 'Listas encontradas', 'enfermedades': enfermedades, 'medicamentos': medicamentos, 'pruebas': pruebas, 'procedimientos': procedimientos}), 201


@ app.route("/paciente/consulta/bitacora/<int:consulta_id>")
def get_specific_bitacora(consulta_id):
    try:
        g.cursor.execute('''
                            SELECT presion_arterial, peso, expediente, diagnostico, created_at, eficacia, id_bitacora, tratamiento
                                FROM bitacora WHERE id_consulta = %s;
                        ''', str(consulta_id))
        data = g.cursor.fetchone()
        return jsonify({'message': 'Bitacora encontrada', 'presion': data[0], 'peso': data[1], 'expediente': data[2], 'diagnostico': data[3], 'fecha': data[4], 'eficacia': data[5], 'id_bitacora': data[6], 'tratamiento': data[7]}), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()
        # Return an error message
        return jsonify({'message': 'Error obteniendo bitacora: {}'.format(str(e))}), 500


@ app.route("/bitacora/modificar", methods=["POST"])
def modificar_bitacora():
    try:
        data = request.json

        medico = data['medico_id']
        bitacora = data['bitacora_id']
        eficacia = data['eficacia']
        expediente = data['expediente']
        diagnostico = data['diagnostico']

        # Insert the data into the database
        g.cursor.execute("CALL modificar_bitacora(%s, %s, %s, %s, %s)",
                         (medico, bitacora, eficacia, expediente, diagnostico))
        g.conn.commit()

        # Return a success message
        return jsonify({'message': 'Se ha realizado la actualización'}), 201
    except Exception as e:
        # Rollback the transaction in case of an error
        g.conn.rollback()

        # Return an error message
        return jsonify({'message': 'Error transferring medico: {}'.format(str(e))}), 500


@ app.route("/tipos_estado_paciente")
def get_tipos_estado_paciente():
    g.cursor.execute('SELECT * FROM tipos_estado_paciente')
    rows = g.cursor.fetchall()
    types = []
    for row in rows:
        _type = {}
        _type['value'] = row[0]
        _type['definition'] = row[1]
        types.append(_type)
    return jsonify(types), 201


@ app.route("/get/medico/transferencia")
def get_medicos():
    g.cursor.execute('SELECT id, nombre, id_instalacion_medica FROM medico')
    medicos = g.cursor.fetchall()
    return jsonify(medicos)


@ app.route("/medico/transferir", methods=["POST"])
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

# Statistics


@app.route("/estadisticas/<int:query>", methods=['GET'])
def get_estadisticas(query):
    print(query)

    if query == 0:
        g.cursor.execute("""
        WITH enfermedad_mortalidad AS (
                WITH eficacia_enfermedad AS (
                    SELECT *
                    FROM bitacora
                    JOIN enfermedades_bitacora eb ON bitacora.id_bitacora = eb.id_bitacora
                    JOIN consulta ON bitacora.id_consulta = consulta.id_consulta
                    JOIN enfermedades e ON eb.id_enfermedad = e.id_enfermedad
                )
                SELECT
                    nombre,
                    CASE eficacia
                        WHEN 0 THEN 1
                        ELSE 0
                    END AS fue_mortal
                FROM eficacia_enfermedad
                GROUP BY nombre, eficacia, id_paciente
            )
            SELECT 
                nombre, 
                count(*) as casos_totales, 
                SUM(fue_mortal) as muertes, 
                SUM(fue_mortal)::float / COUNT(*) * 100 AS tasa_mortalidad
            FROM enfermedad_mortalidad
            GROUP BY nombre
            ORDER BY tasa_mortalidad DESC
            LIMIT 10
        """)
        result = g.cursor.fetchall()
        formatted_result = []
        for row in result:
            formatted_result.append({
                'nombre': row[0],
                'casos_totales': row[1],
                'muertes': row[2],
                'tasa_mortalidad': row[3]
            })
        return jsonify(formatted_result)

    if query == 1:

        g.cursor.execute('SELECT id_medico, nombre, COUNT(id_paciente) as pacientes_atendidos FROM consulta JOIN medico m ON consulta.id_medico = m.id GROUP BY id_medico, nombre ORDER BY pacientes_atendidos DESC LIMIT 10;')
        result = g.cursor.fetchall()
        formatted_result = []
        for row in result:
            formatted_result.append({
                'id_medico': row[0],
                'nombre': row[1],
                'pacientes_atendidos': row[2]
            })
        return jsonify(formatted_result)

    if query == 2:
        g.cursor.execute('SELECT RANK() OVER ( ORDER BY COUNT(id_instalacion) DESC) puesto, id_paciente, nombres, apellidos, COUNT(id_instalacion) AS num_visitas FROM consulta JOIN paciente p ON consulta.id_paciente = p.id GROUP BY id_paciente, nombres,apellidos ORDER BY num_visitas DESC LIMIT 5;')
        result = g.cursor.fetchall()
        formatted_result = []
        for row in result:
            formatted_result.append({
                'puesto': row[0],
                'id_paciente': row[1],
                'nombres': row[2],
                'apellidos': row[3],
                'num_visitas': row[4]
            })

        return jsonify(formatted_result)

    if query == 4:

        g.cursor.execute('SELECT nombre , count(nombre) as pacientes_atendidos FROM instalacion_medica JOIN consulta c ON instalacion_medica.id_instalacion_medica = c.id_instalacion GROUP BY nombre ORDER BY pacientes_atendidos DESC LIMIT 3;')
        result = g.cursor.fetchall()
        formatted_result = []
        for row in result:
            formatted_result.append({
                'nombre': row[0],
                'pacientes_atendidos': row[1]
            })
        return jsonify(formatted_result)

    return jsonify({'message': 'Query Not Found'}), 404


# End Statistics

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
