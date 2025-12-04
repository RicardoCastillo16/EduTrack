# ================================================
# EduTrack - models_inscripciones.py
# Modelos con Control de Concurrencia
# ================================================

from database import get_db_cursor
import psycopg2

class Materia:
    """Modelo para materias"""
    
    @staticmethod
    def crear(nombre, descripcion=None, creditos=3):
        """Crear nueva materia"""
        with get_db_cursor() as cursor:
            cursor.execute(
                """INSERT INTO materias (nombre, descripcion, creditos)
                   VALUES (%s, %s, %s) RETURNING id""",
                (nombre, descripcion, creditos)
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def listar():
        """Listar todas las materias"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, nombre, descripcion, creditos
                   FROM materias ORDER BY nombre"""
            )
            materias = []
            for row in cursor.fetchall():
                materias.append({
                    'id': row[0],
                    'nombre': row[1],
                    'descripcion': row[2],
                    'creditos': row[3]
                })
            return materias

    @staticmethod
    def listar_todas():
        """Alias de listar() para compatibilidad"""
        return Materia.listar()


class Grupo:
    """Modelo para grupos con control de concurrencia"""
    
    @staticmethod
    def crear(materia_id, profesor_id, periodo, cupo_maximo):
        """Crear nuevo grupo"""
        with get_db_cursor() as cursor:
            cursor.execute(
                """INSERT INTO grupos (materia_id, profesor_id, periodo, cupo_maximo)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (materia_id, profesor_id, periodo, cupo_maximo)
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def listar_disponibles():
        """Listar grupos usando la vista optimizada"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT grupo_id, materia, profesor, periodo,
                          cupo_maximo, inscritos_count, cupos_disponibles,
                          version, estado_cupo
                   FROM vista_grupos_disponibles"""
            )
            grupos = []
            for row in cursor.fetchall():
                grupos.append({
                    'id': row[0],
                    'materia': row[1],
                    'profesor': row[2],
                    'periodo': row[3],
                    'cupo_maximo': row[4],
                    'inscritos': row[5],
                    'disponibles': row[6],
                    'version': row[7],
                    'estado': row[8]
                })
            return grupos
    
    @staticmethod
    def obtener_por_id(grupo_id):
        """Obtener grupo con su versión actual"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT g.id, m.nombre, p.nombre, g.periodo,
                          g.cupo_maximo, g.inscritos_count, g.version
                   FROM grupos g
                   JOIN materias m ON g.materia_id = m.id
                   LEFT JOIN profesores p ON g.profesor_id = p.id
                   WHERE g.id = %s""",
                (grupo_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'materia': row[1],
                    'profesor': row[2],
                    'periodo': row[3],
                    'cupo_maximo': row[4],
                    'inscritos': row[5],
                    'version': row[6]
                }
            return None
    
    @staticmethod
    def actualizar_cupo_optimista(grupo_id, nueva_cantidad, version_esperada):
        """
        Actualizar cantidad con CONCURRENCIA OPTIMISTA.
        Retorna True si tuvo éxito, False si hubo conflicto.
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """UPDATE grupos
                   SET inscritos_count = %s, version = version + 1
                   WHERE id = %s AND version = %s""",
                (nueva_cantidad, grupo_id, version_esperada)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def actualizar_cupo_pesimista(grupo_id, nueva_cantidad):
        """
        Actualizar cantidad con CONCURRENCIA PESIMISTA.
        Usa SELECT FOR UPDATE para bloquear la fila.
        """
        with get_db_cursor() as cursor:
            # Bloquear la fila
            cursor.execute(
                """SELECT inscritos_count, version FROM grupos
                   WHERE id = %s FOR UPDATE""",
                (grupo_id,)
            )
            result = cursor.fetchone()
            
            if result:
                cursor.execute(
                    """UPDATE grupos
                       SET inscritos_count = %s, version = version + 1
                       WHERE id = %s""",
                    (nueva_cantidad, grupo_id)
                )
                return True
            return False


class Inscripcion:
    """Modelo para inscripciones con control de concurrencia"""
    
    @staticmethod
    def inscribir_optimista(grupo_id, alumno_id, version_esperada):
        """
        Inscribir con concurrencia OPTIMISTA.
        Retorna (exito, mensaje, inscripcion_id)
        """
        try:
            with get_db_cursor() as cursor:
                # Obtener datos del grupo
                cursor.execute(
                    """SELECT cupo_maximo, inscritos_count, version
                       FROM grupos WHERE id = %s""",
                    (grupo_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return (False, "Grupo no encontrado", None)
                
                cupo_maximo, inscritos, version = result
                
                # Verificar versión
                if version != version_esperada:
                    return (False, "Conflicto: el grupo fue modificado. Intente nuevamente.", None)
                
                # Verificar si ya está inscrito
                cursor.execute(
                    """SELECT COUNT(*) FROM inscripciones
                       WHERE alumno_id = %s AND grupo_id = %s""",
                    (alumno_id, grupo_id)
                )
                if cursor.fetchone()[0] > 0:
                    return (False, "El alumno ya está inscrito en este grupo", None)
                
                # Verificar cupo
                if inscritos >= cupo_maximo:
                    return (False, f"Cupo lleno ({inscritos}/{cupo_maximo})", None)
                
                # Actualizar con verificación de versión
                exito = Grupo.actualizar_cupo_optimista(grupo_id, inscritos + 1, version_esperada)
                
                if not exito:
                    return (False, "Conflicto al actualizar. Intente nuevamente.", None)
                
                # Insertar inscripción
                cursor.execute(
                    """INSERT INTO inscripciones (alumno_id, grupo_id)
                       VALUES (%s, %s) RETURNING id""",
                    (alumno_id, grupo_id)
                )
                inscripcion_id = cursor.fetchone()[0]
                
                # Crear calificaciones
                cursor.execute(
                    "INSERT INTO calificaciones (inscripcion_id) VALUES (%s)",
                    (inscripcion_id,)
                )
                
                return (True, "Inscripción exitosa (método optimista)", inscripcion_id)
                
        except psycopg2.Error as e:
            return (False, f"Error: {str(e)}", None)
    
    @staticmethod
    def inscribir_pesimista(grupo_id, alumno_id):
        """
        Inscribir con concurrencia PESIMISTA.
        Retorna (exito, mensaje, inscripcion_id)
        """
        try:
            with get_db_cursor() as cursor:
                # BLOQUEAR la fila del grupo
                cursor.execute(
                    """SELECT cupo_maximo, inscritos_count
                       FROM grupos WHERE id = %s
                       FOR UPDATE""",
                    (grupo_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return (False, "Grupo no encontrado", None)
                
                cupo_maximo, inscritos = result
                
                # Verificar si ya está inscrito
                cursor.execute(
                    """SELECT COUNT(*) FROM inscripciones
                       WHERE alumno_id = %s AND grupo_id = %s""",
                    (alumno_id, grupo_id)
                )
                if cursor.fetchone()[0] > 0:
                    return (False, "El alumno ya está inscrito en este grupo", None)
                
                # Verificar cupo
                if inscritos >= cupo_maximo:
                    return (False, f"Cupo lleno ({inscritos}/{cupo_maximo})", None)
                
                # Actualizar contador
                cursor.execute(
                    """UPDATE grupos
                       SET inscritos_count = inscritos_count + 1, version = version + 1
                       WHERE id = %s""",
                    (grupo_id,)
                )
                
                # Insertar inscripción
                cursor.execute(
                    """INSERT INTO inscripciones (alumno_id, grupo_id)
                       VALUES (%s, %s) RETURNING id""",
                    (alumno_id, grupo_id)
                )
                inscripcion_id = cursor.fetchone()[0]
                
                # Crear calificaciones
                cursor.execute(
                    "INSERT INTO calificaciones (inscripcion_id) VALUES (%s)",
                    (inscripcion_id,)
                )
                
                return (True, "Inscripción exitosa (método pesimista)", inscripcion_id)
                
        except psycopg2.Error as e:
            return (False, f"Error: {str(e)}", None)
    
    @staticmethod
    def listar_por_alumno(alumno_id):
        """Listar inscripciones de un alumno"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT i.id, m.nombre, p.nombre, g.periodo, i.fecha_inscripcion
                   FROM inscripciones i
                   JOIN grupos g ON i.grupo_id = g.id
                   JOIN materias m ON g.materia_id = m.id
                   LEFT JOIN profesores p ON g.profesor_id = p.id
                   WHERE i.alumno_id = %s AND i.estado = 'activa'
                   ORDER BY i.fecha_inscripcion DESC""",
                (alumno_id,)
            )
            inscripciones = []
            for row in cursor.fetchall():
                inscripciones.append({
                    'id': row[0],
                    'materia': row[1],
                    'profesor': row[2],
                    'periodo': row[3],
                    'fecha': row[4]
                })
            return inscripciones
    
    @staticmethod
    def listar_historial():
        """Listar todas las inscripciones"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT i.id, a.matricula, a.nombre, m.nombre, g.periodo, 
                          i.fecha_inscripcion, i.estado
                   FROM inscripciones i
                   JOIN alumnos a ON i.alumno_id = a.id
                   JOIN grupos g ON i.grupo_id = g.id
                   JOIN materias m ON g.materia_id = m.id
                   ORDER BY i.fecha_inscripcion DESC"""
            )
            inscripciones = []
            for row in cursor.fetchall():
                inscripciones.append({
                    'id': row[0],
                    'matricula': row[1],
                    'alumno': row[2],
                    'materia': row[3],
                    'periodo': row[4],
                    'fecha': row[5],
                    'estado': row[6]
                })
            return inscripciones
