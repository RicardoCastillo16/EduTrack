# EduTrack - Sistema de Inscripciones Académicas

Sistema de gestión académica implementado con Flask, PostgreSQL y MongoDB.

## 📋 Descripción

EduTrack gestiona:
- **Inscripciones** con control de concurrencia (PostgreSQL)
- **Notas de Estudiantes** con documentos flexibles (MongoDB)
- **Calificaciones** parciales y finales
- **Gestión de Usuarios** con roles

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **BD Relacional**: PostgreSQL
- **BD NoSQL**: MongoDB
- **Frontend**: HTML5, Bootstrap 5
- **Control de Concurrencia**: Optimista y Pesimista

## 🚀 Inicio Rápido

### Prerequisitos
- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+

### Instalación y Ejecución

**Opción 1: Script automático (recomendado)**
```bash
./start.sh
```

**Opción 2: Manual**
```bash
# 1. Activar entorno virtual
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows

# 2. Instalar dependencias (solo primera vez)
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de base de datos

# 4. Inicializar base de datos (solo primera vez)
python init_db.py

# 5. Iniciar aplicación
python app.py
```

### Acceso a la Aplicación
- URL: http://127.0.0.1:5000
- Usuario por defecto: `admin`
- Contraseña: `admin123`

## 📁 Estructura del Proyecto
```
EduTrack/
├── app.py                    # Aplicación Flask principal
├── database.py               # Configuración de BD
├── models_auth.py            # Modelos de autenticación
├── models_inscripciones.py   # Modelos de inscripciones
├── models_notas.py           # Modelos de notas
├── init_db.py               # Script de inicialización de BD
├── schema_postgresql.sql     # Schema de PostgreSQL
├── requirements.txt          # Dependencias
├── .env                      # Variables de entorno
├── templates/               # Plantillas HTML
└── static/                  # CSS y JavaScript
```


## 👤 Roles

| Rol | Permisos |
|-----|----------|
| admin | Acceso total |
| coordinator | Inscripciones, calificaciones |
| teacher | Calificaciones, notas |
| student | Consulta sus datos |

## 🔄 Control de Concurrencia

### Optimista
- Usa campo `version` en grupos
- Verifica conflictos al guardar

### Pesimista
- Usa `SELECT FOR UPDATE`
- Bloquea fila durante transacción

## 📁 Estructura

```
edutrack/
├── app.py
├── database.py
├── models_auth.py
├── models_inscripciones.py
├── models_notas.py
├── schema_postgresql.sql
├── crear_datos_prueba.py
├── requirements.txt
├── .env.example
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    └── ...
```
