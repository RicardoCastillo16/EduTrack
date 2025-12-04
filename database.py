# ================================================
# EduTrack - database.py
# Configuración de conexiones a PostgreSQL y MongoDB
# ================================================

import os
from dotenv import load_dotenv
from psycopg2 import pool
from pymongo import MongoClient
from contextlib import contextmanager

load_dotenv()

# ================================================
# CONFIGURACIÓN DE POSTGRESQL
# ================================================
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'edutrack'),
    'user': os.getenv('POSTGRES_USER', 'edutrack_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'your_password_here')
}

# Pool de conexiones PostgreSQL
try:
    postgres_pool = pool.SimpleConnectionPool(1, 20, **POSTGRES_CONFIG)
    print("✓ PostgreSQL connection pool created successfully")
except Exception as e:
    print(f"✗ Error creating PostgreSQL pool: {e}")
    postgres_pool = None

# ================================================
# CONFIGURACIÓN DE MONGODB
# ================================================
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'edutrack')

try:
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client[MONGODB_DB]
    print("✓ MongoDB connected successfully")
except Exception as e:
    print(f"✗ Error connecting to MongoDB: {e}")
    mongo_client = None
    mongo_db = None

# ================================================
# COLECCIONES DE MONGODB
# ================================================
def get_notas_collection():
    """Colección para notas de estudiantes (documentos flexibles)"""
    return mongo_db.student_notes if mongo_db is not None else None

def get_sesiones_collection():
    """Colección para tokens de sesión (clave-valor)"""
    return mongo_db.sesiones if mongo_db is not None else None

# ================================================
# CONTEXT MANAGERS PARA POSTGRESQL
# ================================================
@contextmanager
def get_db_connection():
    """Context manager para conexiones con manejo de transacciones"""
    conn = None
    try:
        conn = postgres_pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            postgres_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=True):
    """Context manager para cursor PostgreSQL"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

# ================================================
# INICIALIZACIÓN DE ÍNDICES MONGODB
# ================================================
def init_mongodb_indexes():
    """Crear índices en MongoDB para optimizar consultas"""
    if mongo_db is not None:
        try:
            # Índices para notas de estudiantes
            notas = get_notas_collection()
            notas.create_index("student_id")
            notas.create_index("teacher_id")
            notas.create_index("group_id")
            notas.create_index("date")
            
            # Índices para sesiones
            sesiones = get_sesiones_collection()
            sesiones.create_index("token", unique=True)
            sesiones.create_index("usuario_id")
            sesiones.create_index("fecha_expiracion")
            
            print("✓ MongoDB indexes created successfully")
        except Exception as e:
            print(f"✗ Error creating MongoDB indexes: {e}")

# Inicializar al importar
if mongo_db is not None:
    init_mongodb_indexes()

