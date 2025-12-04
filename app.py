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
# INICIO
# ================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
