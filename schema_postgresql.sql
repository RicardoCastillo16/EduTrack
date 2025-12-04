-- ================================================
-- EduTrack - PostgreSQL Database Schema
-- Sistema de Inscripciones con Control de Concurrencia
-- ================================================

-- Crear roles del sistema (si no existen)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_role') THEN
        CREATE ROLE admin_role;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'coordinator_role') THEN
        CREATE ROLE coordinator_role;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'teacher_role') THEN
        CREATE ROLE teacher_role;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'student_role') THEN
        CREATE ROLE student_role;
    END IF;
END
$$;

-- ================================================
-- TABLA: usuarios (control de acceso)
-- ================================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'coordinator', 'teacher', 'student')),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);

-- ================================================
-- TABLA: materias
-- ================================================
CREATE TABLE materias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    creditos INTEGER DEFAULT 3,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_materias_nombre ON materias(nombre);

-- ================================================
-- TABLA: profesores
-- ================================================
CREATE TABLE profesores (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    departamento VARCHAR(100),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profesores_nombre ON profesores(nombre);

-- ================================================
-- TABLA: alumnos
-- ================================================
CREATE TABLE alumnos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    carrera VARCHAR(100),
    semestre INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alumnos_matricula ON alumnos(matricula);
CREATE INDEX idx_alumnos_nombre ON alumnos(nombre);

-- ================================================
-- TABLA: grupos (con control de versión para concurrencia)
-- ================================================
CREATE TABLE grupos (
    id SERIAL PRIMARY KEY,
    materia_id INTEGER NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    profesor_id INTEGER REFERENCES profesores(id) ON DELETE SET NULL,
    periodo VARCHAR(20) NOT NULL,
    cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo > 0),
    inscritos_count INTEGER DEFAULT 0 CHECK (inscritos_count >= 0),
    version INTEGER DEFAULT 1,  -- Control de concurrencia optimista
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_grupos_materia ON grupos(materia_id);
CREATE INDEX idx_grupos_profesor ON grupos(profesor_id);
CREATE INDEX idx_grupos_periodo ON grupos(periodo);

-- ================================================
-- TABLA: inscripciones
-- ================================================
CREATE TABLE inscripciones (
    id SERIAL PRIMARY KEY,
    alumno_id INTEGER NOT NULL REFERENCES alumnos(id) ON DELETE CASCADE,
    grupo_id INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    fecha_inscripcion DATE DEFAULT CURRENT_DATE,
    estado VARCHAR(20) DEFAULT 'activa' CHECK (estado IN ('activa', 'baja', 'completada')),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alumno_id, grupo_id)
);

CREATE INDEX idx_inscripciones_alumno ON inscripciones(alumno_id);
CREATE INDEX idx_inscripciones_grupo ON inscripciones(grupo_id);

-- ================================================
-- TABLA: calificaciones
-- ================================================
CREATE TABLE calificaciones (
    id SERIAL PRIMARY KEY,
    inscripcion_id INTEGER UNIQUE NOT NULL REFERENCES inscripciones(id) ON DELETE CASCADE,
    parcial1 NUMERIC(5,2) CHECK (parcial1 IS NULL OR (parcial1 >= 0 AND parcial1 <= 100)),
    parcial2 NUMERIC(5,2) CHECK (parcial2 IS NULL OR (parcial2 >= 0 AND parcial2 <= 100)),
    final NUMERIC(5,2) CHECK (final IS NULL OR (final >= 0 AND final <= 100)),
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_calificaciones_inscripcion ON calificaciones(inscripcion_id);

-- ================================================
-- FUNCIÓN: Actualizar timestamp automáticamente
-- ================================================
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_modificacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_usuarios_timestamp
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trigger_grupos_timestamp
    BEFORE UPDATE ON grupos
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

-- ================================================
-- VISTA: Grupos con disponibilidad
-- ================================================
CREATE VIEW vista_grupos_disponibles AS
SELECT
    g.id AS grupo_id,
    m.nombre AS materia,
    p.nombre AS profesor,
    g.periodo,
    g.cupo_maximo,
    g.inscritos_count,
    g.cupo_maximo - g.inscritos_count AS cupos_disponibles,
    g.version,
    CASE
        WHEN g.inscritos_count >= g.cupo_maximo THEN 'lleno'
        WHEN g.cupo_maximo - g.inscritos_count <= 5 THEN 'casi_lleno'
        ELSE 'disponible'
    END AS estado_cupo
FROM grupos g
JOIN materias m ON g.materia_id = m.id
LEFT JOIN profesores p ON g.profesor_id = p.id
ORDER BY m.nombre, g.periodo;

-- ================================================
-- PRIVILEGIOS POR ROL
-- ================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_role;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO coordinator_role;
GRANT INSERT, UPDATE, DELETE ON inscripciones TO coordinator_role;
GRANT UPDATE ON grupos TO coordinator_role;
GRANT INSERT, UPDATE ON calificaciones TO coordinator_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO coordinator_role;

GRANT SELECT ON materias, grupos, alumnos, inscripciones, calificaciones TO teacher_role;
GRANT UPDATE ON calificaciones TO teacher_role;

GRANT SELECT ON materias, grupos, inscripciones, calificaciones TO student_role;

-- ================================================
-- LOGINS
-- ================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'login_admin') THEN
        CREATE ROLE login_admin WITH LOGIN PASSWORD 'Admin123';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'login_coordinator') THEN
        CREATE ROLE login_coordinator WITH LOGIN PASSWORD 'Coord123';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'login_teacher') THEN
        CREATE ROLE login_teacher WITH LOGIN PASSWORD 'Teacher123';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'login_student') THEN
        CREATE ROLE login_student WITH LOGIN PASSWORD 'Student123';
    END IF;
END
$$;

DO $$
BEGIN
    -- GRANT statements (these are idempotent, so safe to repeat)
    GRANT admin_role TO login_admin;
    GRANT coordinator_role TO login_coordinator;
    GRANT teacher_role TO login_teacher;
    GRANT student_role TO login_student;
EXCEPTION
    WHEN OTHERS THEN
        NULL; -- Ignore errors if grants already exist
END
$$;

-- Usuario admin por defecto (password: admin123)
INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol)
VALUES ('admin', '$2b$12$aOfCg/aARMj7P1yFWYuMk.qfr.TEwFlX9E4fWbebhC0/SJ8d2sr5u', 
        'Administrador', 'admin@edutrack.com', 'admin')
ON CONFLICT (username) DO NOTHING;
