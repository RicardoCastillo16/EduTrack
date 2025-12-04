# ================================================
# EduTrack - models_auth.py
# Modelo de usuario con autenticación
# ================================================

import bcrypt
from database import get_db_cursor, get_sesiones_collection
from datetime import datetime, timedelta
import secrets

class Usuario:
    """Modelo de usuario con autenticación"""
    
    @staticmethod
    def crear_usuario(username, password, nombre_completo, email, rol):
        """Crear nuevo usuario con hash de password"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        with get_db_cursor() as cursor:
            cursor.execute(
                """INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (username, password_hash, nombre_completo, email, rol)
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def autenticar(username, password):
        """Autenticar usuario y retornar sus datos si es válido"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, username, password_hash, nombre_completo, email, rol, activo
                   FROM usuarios WHERE username = %s""",
                (username,)
            )
            result = cursor.fetchone()
            
            if result and result[6]:  # Usuario existe y está activo
                user_id, username, password_hash, nombre, email, rol, activo = result
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    return {
                        'id': user_id,
                        'username': username,
                        'nombre_completo': nombre,
                        'email': email,
                        'rol': rol
                    }
            return None
    
    @staticmethod
    def obtener_por_id(user_id):
        """Obtener usuario por ID"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, username, nombre_completo, email, rol, activo
                   FROM usuarios WHERE id = %s""",
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'nombre_completo': result[2],
                    'email': result[3],
                    'rol': result[4],
                    'activo': result[5]
                }
            return None
    
    @staticmethod
    def listar_usuarios():
        """Listar todos los usuarios"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT id, username, nombre_completo, email, rol, activo, fecha_creacion
                   FROM usuarios ORDER BY id"""
            )
            usuarios = []
            for row in cursor.fetchall():
                usuarios.append({
                    'id': row[0],
                    'username': row[1],
                    'nombre_completo': row[2],
                    'email': row[3],
                    'rol': row[4],
                    'activo': row[5],
                    'fecha_creacion': row[6]
                })
            return usuarios


class Sesion:
    """Manejo de sesiones en MongoDB (clave-valor para acceso rápido)"""
    
    @staticmethod
    def crear_sesion(usuario_id, duracion_horas=24):
        """Crear token de sesión en MongoDB"""
        token = secrets.token_urlsafe(32)
        sesiones = get_sesiones_collection()
        
        sesion_data = {
            'token': token,
            'usuario_id': usuario_id,
            'fecha_creacion': datetime.utcnow(),
            'fecha_expiracion': datetime.utcnow() + timedelta(hours=duracion_horas)
        }
        
        sesiones.insert_one(sesion_data)
        return token
    
    @staticmethod
    def validar_sesion(token):
        """Validar token de sesión y retornar usuario_id si es válido"""
        sesiones = get_sesiones_collection()
        sesion = sesiones.find_one({
            'token': token,
            'fecha_expiracion': {'$gt': datetime.utcnow()}
        })
        
        if sesion:
            return sesion['usuario_id']
        return None
    
    @staticmethod
    def eliminar_sesion(token):
        """Eliminar sesión (logout)"""
        sesiones = get_sesiones_collection()
        sesiones.delete_one({'token': token})
    
    @staticmethod
    def limpiar_sesiones_expiradas():
        """Eliminar sesiones expiradas"""
        sesiones = get_sesiones_collection()
        result = sesiones.delete_many({'fecha_expiracion': {'$lt': datetime.utcnow()}})
        return result.deleted_count
