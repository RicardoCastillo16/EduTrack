# ================================================
# EduTrack - crear_datos_prueba.py
# Script para insertar datos de prueba
# ================================================

from datetime import datetime, timedelta
from models_auth import Usuario
from models_inscripciones import Materia, Grupo, Inscripcion
from models_notas import NotaEstudiante
from database import get_db_cursor

def crear_datos_prueba():
    """Crear datos de prueba para el sistema"""
    
    print("🔧 Creando datos de prueba...")
    
    # 1. Crear usuarios adicionales
    print("\n1. Creando usuarios...")
    try:
        Usuario.crear_usuario(
            username="coordinador1",
            password="coord123",
            nombre_completo="María García",
            email="maria.garcia@edutrack.com",
            rol="coordinator"
        )
        print("✓ Usuario coordinador creado")
    except:
        print("ℹ Usuario coordinador ya existe")
    
    try:
        Usuario.crear_usuario(
            username="profesor1",
            password="prof123",
            nombre_completo="Dr. Carlos Pérez",
            email="carlos.perez@edutrack.com",
            rol="teacher"
        )
        print("✓ Usuario profesor creado")
    except:
        print("ℹ Usuario profesor ya existe")
    
    try:
        Usuario.crear_usuario(
            username="alumno1",
            password="alumno123",
            nombre_completo="Juan Rodríguez",
            email="juan.rodriguez@edutrack.com",
            rol="student"
        )
        print("✓ Usuario alumno creado")
    except:
        print("ℹ Usuario alumno ya existe")
    
    # 2. Crear materias
    print("\n2. Creando materias...")
    materias_data = [
        {'nombre': 'Cálculo I', 'descripcion': 'Introducción al cálculo diferencial', 'creditos': 5},
        {'nombre': 'Programación Básica', 'descripcion': 'Fundamentos de programación', 'creditos': 4},
        {'nombre': 'Bases de Datos', 'descripcion': 'Diseño y gestión de bases de datos', 'creditos': 4},
        {'nombre': 'Redes de Computadoras', 'descripcion': 'Fundamentos de redes', 'creditos': 4},
        {'nombre': 'Estadística', 'descripcion': 'Estadística descriptiva e inferencial', 'creditos': 3}
    ]
    
    for mat in materias_data:
        try:
            Materia.crear(**mat)
            print(f"✓ Materia creada: {mat['nombre']}")
        except Exception as e:
            print(f"ℹ {mat['nombre']}: {str(e)}")
    
    # 3. Crear profesores
    print("\n3. Creando profesores...")
    with get_db_cursor() as cursor:
        profesores = [
            ('Dr. Juan García', 'jgarcia@edutrack.com', 'Matemáticas'),
            ('Mtra. Ana López', 'alopez@edutrack.com', 'Computación'),
            ('Dr. Pedro Martínez', 'pmartinez@edutrack.com', 'Sistemas')
        ]
        for prof in profesores:
            try:
                cursor.execute(
                    """INSERT INTO profesores (nombre, email, departamento)
                       VALUES (%s, %s, %s)""",
                    prof
                )
                print(f"✓ Profesor creado: {prof[0]}")
            except:
                print(f"ℹ {prof[0]}: ya existe")
    
    # 4. Crear alumnos
    print("\n4. Creando alumnos...")
    with get_db_cursor() as cursor:
        alumnos = [
            ('A001', 'Carlos Pérez', 'cperez@alumnos.edu', 'Ing. Sistemas', 3),
            ('A002', 'Ana Martínez', 'amartinez@alumnos.edu', 'Ing. Sistemas', 2),
            ('A003', 'Luis Rodríguez', 'lrodriguez@alumnos.edu', 'Ing. Software', 4),
            ('A004', 'María Sánchez', 'msanchez@alumnos.edu', 'Ing. Sistemas', 1),
            ('A005', 'Pedro González', 'pgonzalez@alumnos.edu', 'Ing. Software', 3)
        ]
        for alum in alumnos:
            try:
                cursor.execute(
                    """INSERT INTO alumnos (matricula, nombre, email, carrera, semestre)
                       VALUES (%s, %s, %s, %s, %s)""",
                    alum
                )
                print(f"✓ Alumno creado: {alum[1]}")
            except:
                print(f"ℹ {alum[1]}: ya existe")
    
    # 5. Crear grupos
    print("\n5. Creando grupos...")
    with get_db_cursor() as cursor:
        # Obtener IDs
        cursor.execute("SELECT id FROM materias LIMIT 5")
        materias_ids = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM profesores LIMIT 3")
        profesores_ids = [r[0] for r in cursor.fetchall()]
        
        if materias_ids and profesores_ids:
            grupos_data = [
                (materias_ids[0], profesores_ids[0], '2025-1', 30),
                (materias_ids[1], profesores_ids[1], '2025-1', 25),
                (materias_ids[2], profesores_ids[0], '2025-1', 20),
            ]
            
            for grupo in grupos_data:
                try:
                    cursor.execute(
                        """INSERT INTO grupos (materia_id, profesor_id, periodo, cupo_maximo)
                           VALUES (%s, %s, %s, %s)""",
                        grupo
                    )
                    print(f"✓ Grupo creado para periodo {grupo[2]}")
                except:
                    print(f"ℹ Grupo ya existe")
    
    # 6. Crear notas de ejemplo en MongoDB
    print("\n6. Creando notas en MongoDB...")
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id FROM alumnos LIMIT 2")
        alumnos_ids = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM grupos LIMIT 1")
        grupo_result = cursor.fetchone()
        grupo_id = grupo_result[0] if grupo_result else 1
    
    if alumnos_ids:
        notas_data = [
            {
                'student_id': alumnos_ids[0],
                'teacher_id': 1,
                'group_id': grupo_id,
                'tipo': 'performance',
                'comentario': 'Excelente participación en clase. Muestra buen dominio del tema.'
            },
            {
                'student_id': alumnos_ids[0],
                'teacher_id': 1,
                'group_id': grupo_id,
                'tipo': 'attendance',
                'comentario': 'Llegó 15 minutos tarde a la clase.'
            }
        ]
        
        for nota in notas_data:
            try:
                NotaEstudiante.crear(**nota)
                print(f"✓ Nota creada: {nota['tipo']}")
            except Exception as e:
                print(f"ℹ Error creando nota: {str(e)}")
    
    print("\n" + "="*50)
    print("Datos de prueba creados exitosamente!")
    print("="*50)
    print("\nCredenciales:")
    print("  - admin / admin123 (Administrador)")
    print("  - coordinador1 / coord123 (Coordinador)")
    print("  - profesor1 / prof123 (Profesor)")
    print("  - alumno1 / alumno123 (Estudiante)")

if __name__ == "__main__":
    crear_datos_prueba()
