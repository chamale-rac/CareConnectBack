CREATE TABLE especialidad_medica (
    id_especialidad_medica SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE instalacion_medica (
    id_instalacion_medica SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE medico (
    id SERIAL PRIMARY KEY,
    correo VARCHAR(255) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    num_telefono VARCHAR(20) NOT NULL,
    id_especialidad_medica INTEGER REFERENCES especialidad_medica(id_especialidad_medica),
    id_instalacion_medica INTEGER REFERENCES instalacion_medica(id_instalacion_medica)
);

INSERT INTO especialidad_medica (nombre)
VALUES ('Cardiologo'), ('Neurologo');

INSERT INTO instalacion_medica (nombre)
VALUES ('Hospital Roosevelt'), ('Hospital San Juan de Dios');

