"""
Servicio para gestión de reseñas.
Maneja el flujo: PostgreSQL → MongoDB → Neo4j
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from db.postgres import execute_query
from db.mongo import get_collection
from services.neo4j_reservations import Neo4jReservationService
from utils.logging import get_logger

logger = get_logger(__name__)


class ReviewService:
    """
    Servicio para gestionar reseñas siguiendo el flujo:
    1. Frontend → Enviar reseña
    2. PostgreSQL → Insertar reseña
    3. Backend → Actualizar MongoDB
    4. Backend → Actualizar Neo4j
    5. Backend → Fin
    """

    def __init__(self):
        self.neo4j_service = None  # Lazy loading
        logger.info("ReviewService inicializado")

    def _get_neo4j_service(self):
        """Obtiene el servicio Neo4j de forma lazy."""
        if self.neo4j_service is None:
            self.neo4j_service = Neo4jReservationService()
        return self.neo4j_service

    async def create_review(
        self,
        reserva_id: int,
        huesped_id: int,
        anfitrion_id: int,
        puntaje: int,
        comentario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva reseña siguiendo el flujo completo.

        Args:
            reserva_id: ID de la reserva
            huesped_id: ID del huésped que hace la reseña
            anfitrion_id: ID del anfitrión reseñado
            puntaje: Puntuación (1-5)
            comentario: Comentario opcional

        Returns:
            Dict con success, review_id, etc.
        """
        try:
            # PASO 1: Validar que existe una reserva válida entre huésped y anfitrión
            validation = await self._validate_reservation(reserva_id, huesped_id, anfitrion_id)
            if not validation['valid']:
                return {"success": False, "error": validation['error']}

            # PASO 2: SQL - Insertar reseña en PostgreSQL
            review_id = await self._insert_review_postgres(
                reserva_id, huesped_id, anfitrion_id, puntaje, comentario
            )

            if not review_id:
                return {"success": False, "error": "Error insertando reseña en PostgreSQL"}

            logger.info(f"✅ Reseña {review_id} insertada en PostgreSQL")

            # PASO 3: Backend - Actualizar estadísticas en MongoDB
            mongo_result = await self._update_mongo_stats(anfitrion_id, puntaje)
            if not mongo_result['success']:
                logger.warning(
                    f"Error actualizando MongoDB: {mongo_result['error']}")

            # PASO 4: Backend - Actualizar Neo4j con información de reseña
            neo4j_result = await self._update_neo4j_review(huesped_id, anfitrion_id, puntaje, review_id)
            if not neo4j_result['success']:
                logger.warning(
                    f"Error actualizando Neo4j: {neo4j_result['error']}")

            # PASO 5: Fin - Retornar resultado exitoso
            return {
                "success": True,
                "review_id": review_id,
                "postgres_success": True,
                "mongo_success": mongo_result['success'],
                "neo4j_success": neo4j_result['success'],
                "message": "Reseña creada exitosamente"
            }

        except Exception as e:
            logger.error(f"Error creando reseña: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _validate_reservation(self, reserva_id: int, huesped_id: int, anfitrion_id: int) -> Dict[str, Any]:
        """Valida que existe una reserva válida entre huésped y anfitrión."""
        try:
            # Verificar que la reserva existe y pertenece al huésped
            query = """
                SELECT r.id, r.estado_reserva_id, p.anfitrion_id, r.fecha_check_out
                FROM reserva r
                JOIN propiedad p ON r.propiedad_id = p.id
                WHERE r.id = $1 AND r.huesped_id = $2
            """

            result = await execute_query(query, reserva_id, huesped_id)

            if not result:
                return {"valid": False, "error": "Reserva no encontrada o no pertenece al huésped"}

            reserva = result[0]

            # Verificar que el anfitrión coincide
            if reserva['anfitrion_id'] != anfitrion_id:
                return {"valid": False, "error": "El anfitrión no coincide con la reserva"}

            # Verificar que la reserva está completada (check-out pasado)
            if reserva['fecha_check_out'] > date.today():
                return {"valid": False, "error": "La reserva aún no ha finalizado"}

            # Verificar que no existe ya una reseña para esta reserva
            existing_query = "SELECT id FROM resenia WHERE reserva_id = $1"
            existing = await execute_query(existing_query, reserva_id)

            if existing:
                return {"valid": False, "error": "Ya existe una reseña para esta reserva"}

            return {"valid": True, "reserva": reserva}

        except Exception as e:
            logger.error(f"Error validando reserva: {str(e)}")
            return {"valid": False, "error": f"Error de validación: {str(e)}"}

    async def _insert_review_postgres(
        self,
        reserva_id: int,
        huesped_id: int,
        anfitrion_id: int,
        puntaje: int,
        comentario: Optional[str]
    ) -> Optional[int]:
        """Inserta la reseña en PostgreSQL."""
        try:
            query = """
                INSERT INTO resenia (reserva_id, huesped_id, anfitrion_id, puntaje, comentario)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """

            result = await execute_query(query, reserva_id, huesped_id, anfitrion_id, puntaje, comentario)

            if result:
                return result[0]['id']
            return None

        except Exception as e:
            logger.error(f"Error insertando reseña en PostgreSQL: {str(e)}")
            return None

    async def _update_mongo_stats(self, anfitrion_id: int, puntaje: int) -> Dict[str, Any]:
        """Actualiza estadísticas del anfitrión en MongoDB."""
        try:
            collection = get_collection("host_statistics")

            # Obtener estadísticas actuales
            current_stats = collection.find_one({"host_id": anfitrion_id})

            if current_stats:
                # Actualizar estadísticas existentes
                total_reviews = current_stats.get('total_reviews', 0) + 1
                total_rating = current_stats.get('total_rating', 0) + puntaje
                avg_rating = total_rating / total_reviews

                update_doc = {
                    "$set": {
                        "total_reviews": total_reviews,
                        "total_rating": total_rating,
                        "avg_rating": round(avg_rating, 2),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "recent_ratings": {
                            "rating": puntaje,
                            "date": datetime.utcnow()
                        }
                    }
                }

                collection.update_one({"host_id": anfitrion_id}, update_doc)
            else:
                # Crear nuevas estadísticas
                new_stats = {
                    "host_id": anfitrion_id,
                    "total_reviews": 1,
                    "total_rating": puntaje,
                    "avg_rating": puntaje,
                    "recent_ratings": [{
                        "rating": puntaje,
                        "date": datetime.utcnow()
                    }],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                collection.insert_one(new_stats)

            logger.info(
                f"📊 Estadísticas MongoDB actualizadas para anfitrión {anfitrion_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Error actualizando MongoDB: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _update_neo4j_review(self, huesped_id: int, anfitrion_id: int, puntaje: int, review_id: int) -> Dict[str, Any]:
        """Actualiza la relación Neo4j con información de la reseña."""
        try:
            neo4j_service = self._get_neo4j_service()
            driver = await neo4j_service._get_driver()

            # Actualizar la relación INTERACCIONES con información de reseña
            query = """
                MATCH (guest:Usuario {user_id: $guest_id})-[rel:INTERACCIONES]->(host:Usuario {user_id: $host_id})
                SET 
                    rel.reviews_count = COALESCE(rel.reviews_count, 0) + 1,
                    rel.total_rating = COALESCE(rel.total_rating, 0) + $rating,
                    rel.avg_rating = (COALESCE(rel.total_rating, 0) + $rating) / (COALESCE(rel.reviews_count, 0) + 1),
                    rel.last_review_id = $review_id,
                    rel.last_review_rating = $rating,
                    rel.last_review_date = date(),
                    rel.updated_at = datetime()
                
                RETURN 
                    rel.reviews_count as total_reviews,
                    rel.avg_rating as avg_rating
            """

            result = driver.execute_query(
                query,
                guest_id=str(huesped_id),
                host_id=str(anfitrion_id),
                rating=puntaje,
                review_id=review_id
            )

            if result and result[0]:
                record = result[0][0]
                logger.info(
                    f"🔗 Neo4j actualizado: Huésped {huesped_id} → Host {anfitrion_id}, "
                    f"Total reseñas: {record['total_reviews']}, Promedio: {record['avg_rating']:.2f}"
                )

            return {"success": True}

        except Exception as e:
            logger.error(f"Error actualizando Neo4j: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_guest_reviews(self, huesped_id: int) -> Dict[str, Any]:
        """Obtiene todas las reseñas hechas por un huésped."""
        try:
            query = """
                SELECT 
                    r.id, 
                    r.puntaje, 
                    r.comentario,
                    res.fecha_check_in,
                    res.fecha_check_out,
                    p.nombre as propiedad_nombre,
                    a.nombre as anfitrion_nombre
                FROM resenia r
                JOIN reserva res ON r.reserva_id = res.id
                JOIN propiedad p ON res.propiedad_id = p.id
                JOIN anfitrion a ON r.anfitrion_id = a.id
                WHERE r.huesped_id = $1
                ORDER BY r.id DESC
            """

            result = await execute_query(query, huesped_id)

            return {
                "success": True,
                "reviews": result or [],
                "total_reviews": len(result) if result else 0
            }

        except Exception as e:
            logger.error(
                f"Error obteniendo reseñas del huésped {huesped_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_host_reviews(self, anfitrion_id: int) -> Dict[str, Any]:
        """Obtiene todas las reseñas recibidas por un anfitrión."""
        try:
            query = """
                SELECT 
                    r.id, 
                    r.puntaje, 
                    r.comentario,
                    res.fecha_check_in,
                    res.fecha_check_out,
                    p.nombre as propiedad_nombre,
                    h.nombre as huesped_nombre
                FROM resenia r
                JOIN reserva res ON r.reserva_id = res.id
                JOIN propiedad p ON res.propiedad_id = p.id
                JOIN huesped h ON r.huesped_id = h.id
                WHERE r.anfitrion_id = $1
                ORDER BY r.id DESC
            """

            result = await execute_query(query, anfitrion_id)

            # Calcular estadísticas
            if result:
                total_reviews = len(result)
                avg_rating = sum(review['puntaje']
                                 for review in result) / total_reviews
                rating_distribution = {}
                for i in range(1, 6):
                    rating_distribution[i] = len(
                        [r for r in result if r['puntaje'] == i])
            else:
                total_reviews = 0
                avg_rating = 0
                rating_distribution = {}

            return {
                "success": True,
                "reviews": result or [],
                "stats": {
                    "total_reviews": total_reviews,
                    "avg_rating": round(avg_rating, 2),
                    "rating_distribution": rating_distribution
                }
            }

        except Exception as e:
            logger.error(
                f"Error obteniendo reseñas del anfitrión {anfitrion_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_pending_reviews(self, huesped_id: int) -> Dict[str, Any]:
        """Obtiene reservas completadas sin reseña para un huésped."""
        try:
            query = """
                SELECT 
                    res.id as reserva_id,
                    res.fecha_check_in,
                    res.fecha_check_out,
                    p.id as propiedad_id,
                    p.nombre as propiedad_nombre,
                    a.id as anfitrion_id,
                    a.nombre as anfitrion_nombre
                FROM reserva res
                JOIN propiedad p ON res.propiedad_id = p.id
                JOIN anfitrion a ON p.anfitrion_id = a.id
                LEFT JOIN resenia r ON res.id = r.reserva_id
                WHERE res.huesped_id = $1
                AND res.fecha_check_out < CURRENT_DATE
                AND r.id IS NULL
                ORDER BY res.fecha_check_out DESC
            """

            result = await execute_query(query, huesped_id)

            return {
                "success": True,
                "pending_reviews": result or [],
                "total_pending": len(result) if result else 0
            }

        except Exception as e:
            logger.error(
                f"Error obteniendo reseñas pendientes del huésped {huesped_id}: {str(e)}")
            return {"success": False, "error": str(e)}
