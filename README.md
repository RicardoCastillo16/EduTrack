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

## 📦 Instalación

### 1. Requisitos
- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+

### 2. Configurar Base de Datos
```bash
sudo -u postgres psql
CREATE DATABASE edutrack;
CREATE USER edutrack_admin WITH PASSWORD 'tu_contraseña';
GRANT ALL PRIVILEGES ON DATABASE edutrack TO edutrack_admin;
\q

psql -U edutrack_admin -d edutrack -f schema_postgresql.sql
```

### 3. Instalar y Ejecutar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 4. Acceder
- URL: http://localhost:5000
- Usuario: admin / admin123

### 5. Datos de Prueba
```bash
python crear_datos_prueba.py
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
