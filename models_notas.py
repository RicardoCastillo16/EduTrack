# ================================================
# EduTrack - models_notas.py
# Modelo MongoDB para Notas de Estudiantes
# ================================================

from database import get_notas_collection
from datetime import datetime
from bson import ObjectId

class NotaEstudiante:
    """
    Modelo para notas de estudiantes en MongoDB.
    Aprovecha la flexibilidad de documentos.
    """
    
    @staticmethod
    def crear(student_id, teacher_id, group_id, tipo, comentario, datos_adicionales=None):
        """
        Crear nueva nota de estudiante.
        datos_adicionales es un dict flexible.
        """
        notas = get_notas_collection()
        
        documento = {
            'student_id': student_id,
            'teacher_id': teacher_id,
            'group_id': group_id,
            'date': datetime.utcnow(),
            'type': tipo,  # 'performance', 'attendance', 'behavior'
            'comment': comentario,
            'datos_adicionales': datos_adicionales or {},
            'seguimientos': [],
            'fecha_creacion': datetime.utcnow(),
            'ultima_modificacion': datetime.utcnow()
        }
        
        result = notas.insert_one(documento)
        return str(result.inserted_id)
    
    @staticmethod
    def listar(filtros=None):
        """Listar notas con filtros opcionales"""
        notas = get_notas_collection()
        
        query = {}
        if filtros:
            if 'student_id' in filtros:
                query['student_id'] = filtros['student_id']
            if 'group_id' in filtros:
                query['group_id'] = filtros['group_id']
            if 'type' in filtros:
                query['type'] = filtros['type']
        
        resultados = []
        for doc in notas.find(query).sort('date', -1):
            doc['_id'] = str(doc['_id'])
            resultados.append(doc)
        
        return resultados
    
    @staticmethod
    def obtener_por_id(nota_id):
        """Obtener nota por ID"""
        notas = get_notas_collection()
        
        try:
            doc = notas.find_one({'_id': ObjectId(nota_id)})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def actualizar(nota_id, datos_actualizacion):
        """Actualizar nota"""
        notas = get_notas_collection()
        
        datos_actualizacion['ultima_modificacion'] = datetime.utcnow()
        
        try:
            result = notas.update_one(
                {'_id': ObjectId(nota_id)},
                {'$set': datos_actualizacion}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def agregar_seguimiento(nota_id, texto, autor):
        """Agregar seguimiento a una nota existente"""
        notas = get_notas_collection()
        
        seguimiento = {
            'texto': texto,
            'autor': autor,
            'fecha': datetime.utcnow()
        }
        
        try:
            result = notas.update_one(
                {'_id': ObjectId(nota_id)},
                {
                    '$push': {'seguimientos': seguimiento},
                    '$set': {'ultima_modificacion': datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @staticmethod
    def buscar_por_texto(texto_busqueda):
        """Búsqueda de texto en notas"""
        notas = get_notas_collection()
        
        query = {
            '$or': [
                {'comment': {'$regex': texto_busqueda, '$options': 'i'}},
                {'type': {'$regex': texto_busqueda, '$options': 'i'}}
            ]
        }
        
        resultados = []
        for doc in notas.find(query):
            doc['_id'] = str(doc['_id'])
            resultados.append(doc)
        
        return resultados
    
    @staticmethod
    def eliminar(nota_id):
        """Eliminar nota"""
        notas = get_notas_collection()
        
        try:
            result = notas.delete_one({'_id': ObjectId(nota_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    @staticmethod
    def contar_por_tipo(group_id):
        """Agregación: contar notas por tipo en un grupo"""
        notas = get_notas_collection()
        
        pipeline = [
            {'$match': {'group_id': group_id}},
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}}
        ]
        
        return list(notas.aggregate(pipeline))
