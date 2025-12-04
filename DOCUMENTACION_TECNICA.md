# 📚 Documentación Técnica - EduTrack

## 🎯 Resumen

Sistema académico con PostgreSQL y MongoDB, implementando control de concurrencia.

## ✅ Control de Concurrencia (4.1)

### Optimista
```python
def actualizar_cupo_optimista(grupo_id, nueva_cantidad, version_esperada):
    cursor.execute("""
        UPDATE grupos
        SET inscritos_count = %s, version = version + 1
        WHERE id = %s AND version = %s
    """, (nueva_cantidad, grupo_id, version_esperada))
    return cursor.rowcount > 0
```

### Pesimista
```python
def inscribir_pesimista(grupo_id, alumno_id):
    cursor.execute("""
        SELECT cupo_maximo, inscritos_count
        FROM grupos WHERE id = %s
        FOR UPDATE
    """, (grupo_id,))
```

## ✅ BD NoSQL - Documentos (4.2)

```python
documento = {
    'student_id': student_id,
    'teacher_id': teacher_id,
    'type': tipo,
    'comment': comentario,
    'datos_adicionales': {},  # Flexible
    'seguimientos': []        # Array
}
```

## ✅ BD NoSQL - Clave-Valor (4.3)

```python
sesion = {
    'token': token,
    'usuario_id': usuario_id,
    'fecha_expiracion': datetime
}
```

## ✅ Roles y Privilegios (5.3)

| Rol | SELECT | INSERT | UPDATE | DELETE |
|-----|--------|--------|--------|--------|
| admin | ✓ | ✓ | ✓ | ✓ |
| coordinator | ✓ | ✓ | ✓ | - |
| teacher | ✓ | - | calificaciones | - |
| student | propios | - | - | - |
