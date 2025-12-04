# Inicio Rápido - EduTrack

## Instalación en 5 Minutos

### 1. Pre-requisitos
```bash
python3 --version  # 3.8+
psql --version     # PostgreSQL 12+
mongod --version   # MongoDB 4.4+
```

### 2. Configurar BD
```bash
sudo -u postgres psql
CREATE DATABASE edutrack;
CREATE USER edutrack_admin WITH PASSWORD 'edutrack2024';
GRANT ALL PRIVILEGES ON DATABASE edutrack TO edutrack_admin;
\q

psql -U edutrack_admin -d edutrack -h localhost -f schema_postgresql.sql
```

### 3. Instalar y Ejecutar
```bash
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start mongod
python app.py
```

### 4. Acceder
- URL: **http://localhost:5000**
- Usuario: `admin`
- Contraseña: `admin123`

### 5. Datos de Prueba
```bash
python crear_datos_prueba.py
```

## Credenciales

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Administrador |
| coordinador1 | coord123 | Coordinador |
| profesor1 | prof123 | Profesor |
| alumno1 | alumno123 | Estudiante |

## Checklist

- [ ] PostgreSQL corriendo
- [ ] MongoDB corriendo
- [ ] BD `edutrack` creada
- [ ] Schema SQL aplicado
- [ ] Entorno virtual activado
- [ ] App en puerto 5000
