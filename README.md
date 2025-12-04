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
