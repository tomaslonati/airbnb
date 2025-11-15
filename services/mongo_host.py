"""
Servicio para gestionar anfitriones en MongoDB
Maneja documentos de ratings y estadísticas de anfitriones
"""

from typing import Optional, Dict, Any, List
from db.mongo import get_collection
from utils.logging import get_logger

logger = get_logger(__name__)


class MongoHostService:
    """Servicio para gestionar documentos de anfitriones en MongoDB"""

    def __init__(self):
        self.collection = get_collection("hosts")

    async def create_host_document(self, host_id: int) -> Dict[str, Any]:
        """
        Crea el documento inicial para un anfitrión en MongoDB

        Args:
            host_id: ID del anfitrión (del SQL)

        Returns:
            Resultado de la operación
        """
        try:
            # Verificar si ya existe
            existing = await self.get_host_document(host_id)
            if existing.get('success'):
                logger.info(f"Documento para host {host_id} ya existe")
                return {
                    'success': True,
                    'message': 'Documento ya existe',
                    'document_id': str(existing['document']['_id'])
                }

            # Crear nuevo documento
            host_document = {
                "host_id": host_id,
                "ratings": [],
                "stats": {
                    "total_ratings": 0,
                    "average_rating": 0.0,
                    "total_reviews": 0
                },
                "created_at": {
                    "$date": {"$numberLong": str(int(__import__('time').time() * 1000))}
                },
                "updated_at": {
                    "$date": {"$numberLong": str(int(__import__('time').time() * 1000))}
                }
            }

            result = self.collection.insert_one(host_document)

            logger.info(f"Documento creado para host {host_id}",
                        document_id=str(result.inserted_id))

            return {
                'success': True,
                'message': 'Documento de anfitrión creado exitosamente',
                'document_id': str(result.inserted_id),
                'host_id': host_id
            }

        except Exception as e:
            logger.error(
                f"Error creando documento para host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def get_host_document(self, host_id: int) -> Dict[str, Any]:
        """
        Obtiene el documento de un anfitrión por su ID

        Args:
            host_id: ID del anfitrión

        Returns:
            Documento del anfitrión o error
        """
        try:
            document = self.collection.find_one({"host_id": host_id})

            if document:
                return {
                    'success': True,
                    'document': document
                }
            else:
                return {
                    'success': False,
                    'error': 'Documento no encontrado'
                }

        except Exception as e:
            logger.error(
                f"Error obteniendo documento para host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def add_rating(self, host_id: int, rating: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega una calificación al anfitrión

        Args:
            host_id: ID del anfitrión
            rating: Datos de la calificación
                   {
                       "guest_id": int,
                       "rating": float (1-5),
                       "comment": str,
                       "reservation_id": int,
                       "created_at": datetime
                   }

        Returns:
            Resultado de la operación
        """
        try:
            # Agregar timestamp si no existe
            if 'created_at' not in rating:
                rating['created_at'] = {
                    "$date": {"$numberLong": str(int(__import__('time').time() * 1000))}
                }

            # Actualizar documento
            result = self.collection.update_one(
                {"host_id": host_id},
                {
                    "$push": {"ratings": rating},
                    "$set": {"updated_at": {
                        "$date": {"$numberLong": str(int(__import__('time').time() * 1000))}
                    }}
                }
            )

            if result.modified_count > 0:
                # Recalcular estadísticas
                await self._update_stats(host_id)

                logger.info(f"Rating agregado al host {host_id}")
                return {
                    'success': True,
                    'message': 'Calificación agregada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo agregar la calificación'
                }

        except Exception as e:
            logger.error(
                f"Error agregando rating al host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def get_host_ratings(self, host_id: int, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene las calificaciones de un anfitrión

        Args:
            host_id: ID del anfitrión
            limit: Límite de calificaciones a obtener

        Returns:
            Lista de calificaciones
        """
        try:
            pipeline = [
                {"$match": {"host_id": host_id}},
                {"$unwind": "$ratings"},
                {"$sort": {"ratings.created_at": -1}},
                {"$project": {"rating": "$ratings", "_id": 0}}
            ]

            if limit:
                pipeline.append({"$limit": limit})

            ratings = list(self.collection.aggregate(pipeline))

            return {
                'success': True,
                'ratings': [r['rating'] for r in ratings]
            }

        except Exception as e:
            logger.error(
                f"Error obteniendo ratings del host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def get_host_stats(self, host_id: int) -> Dict[str, Any]:
        """
        Obtiene las estadísticas calculadas de un anfitrión

        Args:
            host_id: ID del anfitrión

        Returns:
            Estadísticas del anfitrión
        """
        try:
            document = self.collection.find_one(
                {"host_id": host_id},
                {"stats": 1, "_id": 0}
            )

            if document and "stats" in document:
                return {
                    'success': True,
                    'stats': document['stats']
                }
            else:
                return {
                    'success': False,
                    'error': 'Estadísticas no encontradas'
                }

        except Exception as e:
            logger.error(
                f"Error obteniendo stats del host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def _update_stats(self, host_id: int) -> None:
        """
        Recalcula las estadísticas de un anfitrión basado en sus ratings

        Args:
            host_id: ID del anfitrión
        """
        try:
            # Obtener todas las calificaciones
            pipeline = [
                {"$match": {"host_id": host_id}},
                {"$unwind": "$ratings"},
                {"$group": {
                    "_id": None,
                    "total_ratings": {"$sum": 1},
                    "average_rating": {"$avg": "$ratings.rating"},
                    "total_reviews": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$exists": ["$ratings.comment"]},
                                    {"$ne": ["$ratings.comment", ""]}
                                ]},
                                1,
                                0
                            ]
                        }
                    }
                }}
            ]

            result = list(self.collection.aggregate(pipeline))

            if result:
                stats = result[0]
                stats.pop('_id', None)  # Remover _id del aggregation

                # Actualizar documento con nuevas estadísticas
                self.collection.update_one(
                    {"host_id": host_id},
                    {
                        "$set": {
                            "stats": stats,
                            "updated_at": {
                                "$date": {"$numberLong": str(int(__import__('time').time() * 1000))}
                            }
                        }
                    }
                )

                logger.info(
                    f"Estadísticas actualizadas para host {host_id}", stats=stats)

        except Exception as e:
            logger.error(
                f"Error actualizando estadísticas del host {host_id}", error=str(e))

    async def verify_connection(self) -> Dict[str, Any]:
        """
        Verifica la conexión con MongoDB y la colección

        Returns:
            Estado de la conexión
        """
        try:
            # Test básico
            self.collection.find_one({}, {"_id": 1})

            return {
                'success': True,
                'message': 'Conexión a MongoDB exitosa'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_all_hosts(self) -> Dict[str, Any]:
        """
        Obtiene todos los documentos de anfitriones

        Returns:
            Lista de todos los anfitriones
        """
        try:
            hosts = list(self.collection.find({}, {"_id": 0}))

            return {
                'success': True,
                'hosts': hosts,
                'count': len(hosts)
            }

        except Exception as e:
            logger.error("Error obteniendo todos los hosts", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def ensure_host_document_sync(self, host_id: int) -> Dict[str, Any]:
        """
        Asegura que el documento del anfitrión esté sincronizado
        Útil para casos donde el usuario cambió de rol

        Args:
            host_id: ID del anfitrión

        Returns:
            Resultado de la sincronización
        """
        try:
            # Verificar si existe
            existing = await self.get_host_document(host_id)

            if existing.get('success'):
                return {
                    'success': True,
                    'message': 'Documento ya existe y está sincronizado',
                    'action': 'verified'
                }
            else:
                # Crear documento
                result = await self.create_host_document(host_id)
                if result.get('success'):
                    return {
                        'success': True,
                        'message': 'Documento creado y sincronizado',
                        'action': 'created'
                    }
                else:
                    return result

        except Exception as e:
            logger.error(
                f"Error sincronizando documento del host {host_id}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
