# ================================================
# EduTrack - app.py
# ================================================

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from datetime import datetime

from database import get_db_cursor
from models_auth import Usuario, Sesion
from models_inscripciones import Materia, Grupo, Inscripcion
from models_notas import NotaEstudiante

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# ================================================
# DECORADORES
# ================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Debe iniciar sesión', 'warning')
                return redirect(url_for('login'))
            
            user = Usuario.obtener_por_id(session['user_id'])
            if not user or user['rol'] not in roles:
                flash('No tiene permisos para acceder a esta página', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ================================================
# RUTAS DE AUTENTICACIÓN
# ================================================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Usuario.autenticar(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            session['nombre_completo'] = user['nombre_completo']
            
            # Crear sesión en MongoDB
            token = Sesion.crear_sesion(user['id'])
            session['token'] = token
            
            flash(f'Bienvenido, {user["nombre_completo"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'token' in session:
        Sesion.eliminar_sesion(session['token'])
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))

# ================================================
# DASHBOARD
# ================================================
@app.route('/dashboard')
@login_required
def dashboard():
    user = Usuario.obtener_por_id(session['user_id'])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT COUNT(*) FROM materias")
        total_materias = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM grupos")
        total_grupos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alumnos")
        total_alumnos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inscripciones WHERE estado = 'activa'")
        inscripciones_activas = cursor.fetchone()[0]
    
    stats = {
        'total_materias': total_materias,
        'total_grupos': total_grupos,
        'total_alumnos': total_alumnos,
        'inscripciones_activas': inscripciones_activas
    }
    
    return render_template('dashboard.html', user=user, stats=stats)

# ================================================
# RUTAS DE GRUPOS E INSCRIPCIONES
# ================================================
@app.route('/grupos')
@login_required
def grupos():
    grupos = Grupo.listar_disponibles()
    return render_template('grupos.html', grupos=grupos)

@app.route('/inscripcion', methods=['GET', 'POST'])
@role_required('admin', 'coordinator')
def registrar_inscripcion():
    if request.method == 'POST':
        grupo_id = int(request.form.get('grupo_id'))
        alumno_id = int(request.form.get('alumno_id'))
        usar_optimista = request.form.get('metodo_concurrencia') == 'optimista'
        
        if usar_optimista:
            grupo = Grupo.obtener_por_id(grupo_id)
            if grupo:
                exito, mensaje, inscripcion_id = Inscripcion.inscribir_optimista(
                    grupo_id, alumno_id, grupo['version']
                )
            else:
                exito, mensaje, inscripcion_id = False, "Grupo no encontrado", None
        else:
            exito, mensaje, inscripcion_id = Inscripcion.inscribir_pesimista(grupo_id, alumno_id)
        
        if exito:
            flash(mensaje, 'success')
            return redirect(url_for('inscripciones'))
        else:
            flash(mensaje, 'danger')
    
    grupos = Grupo.listar_disponibles()
    # Obtener alumnos
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id, matricula, nombre FROM alumnos ORDER BY nombre")
        alumnos = [{'id': r[0], 'matricula': r[1], 'nombre': r[2]} for r in cursor.fetchall()]
    
    return render_template('registrar_inscripcion.html', grupos=grupos, alumnos=alumnos)

@app.route('/inscripciones')
@login_required
def inscripciones():
    historial = Inscripcion.listar_historial()
    return render_template('inscripciones.html', inscripciones=historial)

# ================================================
# RUTAS DE NOTAS (MongoDB)
# ================================================
@app.route('/notas')
@login_required
def notas_estudiantes():
    group_id = request.args.get('group_id')
    filtros = {}
    if group_id:
        filtros['group_id'] = int(group_id)
    
    notas = NotaEstudiante.listar(filtros)
    grupos = Grupo.listar_disponibles()
    
    return render_template('notas.html', notas=notas, grupos=grupos)

@app.route('/notas/nueva', methods=['GET', 'POST'])
@role_required('admin', 'coordinator', 'teacher')
def nueva_nota():
    if request.method == 'POST':
        nota_id = NotaEstudiante.crear(
            student_id=int(request.form.get('student_id')),
            teacher_id=session['user_id'],
            group_id=int(request.form.get('group_id')),
            tipo=request.form.get('tipo'),
            comentario=request.form.get('comentario')
        )
        flash('Nota creada exitosamente', 'success')
        return redirect(url_for('notas_estudiantes'))
    
    # Obtener datos para el formulario
    grupos = Grupo.listar_disponibles()
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id, matricula, nombre FROM alumnos ORDER BY nombre")
        alumnos = [{'id': r[0], 'matricula': r[1], 'nombre': r[2]} for r in cursor.fetchall()]
    
    return render_template('nueva_nota.html', grupos=grupos, alumnos=alumnos)

# ================================================
# RUTAS DE MATERIAS
# ================================================
@app.route('/materias')
@login_required
def materias():
    materias_list = Materia.listar_todas()
    return render_template('materias.html', materias=materias_list)

@app.route('/materias/nueva', methods=['GET', 'POST'])
@role_required('admin', 'coordinator')
def nueva_materia():
    if request.method == 'POST':
        materia_id = Materia.crear(
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            creditos=int(request.form.get('creditos', 3))
        )
        flash('Materia creada exitosamente', 'success')
        return redirect(url_for('materias'))

    return render_template('nueva_materia.html')

# ================================================
# RUTAS DE ALUMNOS
# ================================================
@app.route('/alumnos')
@login_required
def alumnos():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, matricula, nombre, email, carrera, semestre, fecha_creacion
            FROM alumnos ORDER BY nombre
        """)
        alumnos_list = []
        for row in cursor.fetchall():
            alumnos_list.append({
                'id': row[0],
                'matricula': row[1],
                'nombre': row[2],
                'email': row[3],
                'carrera': row[4],
                'semestre': row[5],
                'fecha_creacion': row[6]
            })

    return render_template('alumnos.html', alumnos=alumnos_list)

@app.route('/alumnos/nuevo', methods=['GET', 'POST'])
@role_required('admin', 'coordinator')
def nuevo_alumno():
    if request.method == 'POST':
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO alumnos (matricula, nombre, email, carrera, semestre)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (
                request.form.get('matricula'),
                request.form.get('nombre'),
                request.form.get('email'),
                request.form.get('carrera'),
                int(request.form.get('semestre', 1))
            ))

        flash('Alumno creado exitosamente', 'success')
        return redirect(url_for('alumnos'))

    return render_template('nuevo_alumno.html')

# ================================================
# RUTAS DE USUARIOS
# ================================================
@app.route('/usuarios')
@role_required('admin')
def usuarios():
    usuarios_list = Usuario.listar_todos()
    return render_template('usuarios.html', usuarios=usuarios_list)

@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@role_required('admin')
def nuevo_usuario():
    if request.method == 'POST':
        user_id = Usuario.crear_usuario(
            username=request.form.get('username'),
            password=request.form.get('password'),
            nombre_completo=request.form.get('nombre_completo'),
            email=request.form.get('email'),
            rol=request.form.get('rol')
        )
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('usuarios'))

    return render_template('nuevo_usuario.html')

@app.route('/grupos/nuevo', methods=['GET', 'POST'])
@role_required('admin', 'coordinator')
def nuevo_grupo():
    if request.method == 'POST':
        grupo_id = Grupo.crear(
            materia_id=int(request.form.get('materia_id')),
            profesor_id=int(request.form.get('profesor_id')) if request.form.get('profesor_id') else None,
            periodo=request.form.get('periodo'),
            cupo_maximo=int(request.form.get('cupo_maximo'))
        )
        flash('Grupo creado exitosamente', 'success')
        return redirect(url_for('grupos'))

    # Obtener materias y profesores para el formulario
    materias_list = Materia.listar_todas()
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id, nombre FROM profesores ORDER BY nombre")
        profesores = [{'id': r[0], 'nombre': r[1]} for r in cursor.fetchall()]

    return render_template('nuevo_grupo.html', materias=materias_list, profesores=profesores)

# ================================================
# RUTAS DE CALIFICACIONES
# ================================================
@app.route('/calificaciones')
@login_required
def calificaciones():
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT c.id, a.nombre, a.matricula, m.nombre as materia, 
                   c.parcial1, c.parcial2, c.final, c.fecha_modificacion
            FROM calificaciones c
            JOIN inscripciones i ON c.inscripcion_id = i.id
            JOIN alumnos a ON i.alumno_id = a.id
            JOIN grupos g ON i.grupo_id = g.id
            JOIN materias m ON g.materia_id = m.id
            ORDER BY a.nombre
        """)
        calificaciones_list = []
        for row in cursor.fetchall():
            calificaciones_list.append({
                'id': row[0],
                'alumno': row[1],
                'matricula': row[2],
                'materia': row[3],
                'parcial1': row[4],
                'parcial2': row[5],
                'final': row[6],
                'fecha_modificacion': row[7]
            })

    return render_template('calificaciones.html', calificaciones=calificaciones_list)

# ================================================
# INICIO
# ================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
