"""
Servicio de reservas que utiliza PostgreSQL y Cassandra.
Este es un ejemplo básico de la estructura del servicio.
"""

import uuid
from datetime import datetime, date
from typing import Dict, Any
from utils.logging import get_logger

# Importamos el módulo de Neo4j para el modelado de grafos
from db import neo4j 

logger = get_logger(__name__)


class ReservationService:
    """Servicio para gestionar reservas de propiedades - EJEMPLO."""

    def __init__(self):
        pass

    async def _update_neo4j_recurrent_booking(self, user_id: str, city_name: str):
        """
        Crea/Actualiza la relación User-[:BOOKED_IN]->City, incrementando el contador.
        Esto cumple con el HU: Usuarios que regresaron a la misma ciudad (>=2 reservas).
        """
        query = """
            // Asegura que el nodo User exista (aunque la app ya debería crearlo)
            MERGE (u:User {id: $user_id}) 
            
            // Asegura que el nodo City exista (creado en la migración M003)
            MERGE (c:City {name: $city_name})
            
            // Crea la relación o la actualiza
            MERGE (u)-[r:BOOKED_IN]->(c)
            ON CREATE SET r.count = 1
            ON MATCH SET r.count = r.count + 1
        """
        
        # Asumimos que el módulo de Neo4j ya tiene un cliente funcional
        await neo4j.execute_write_transaction(
            query,
            {"user_id": user_id, "city_name": city_name}
        )
        logger.info("Relación de reserva recurrente actualizada en Neo4j.")


    async def create_reservation(
        self,
        property_id: str,
        user_id: str,
        check_in: date,
        check_out: date
    ) -> Dict[str, Any]:
        """
        FUNCIÓN DE EJEMPLO: Crea una nueva reserva.
        
        Añadida la lógica de doble escritura a Neo4j.
        """
        reservation_id = str(uuid.uuid4())

        logger.info(
            "Creando reserva de ejemplo",
            reservation_id=reservation_id,
            property_id=property_id,
            user_id=user_id
        )

        # 1. Simulación de creación en PostgreSQL (esto debería ser la transacción real)
        # La implementación real debería obtener el nombre de la ciudad desde el property_id.
        # Por ahora, usaremos una ciudad de ejemplo para el grafo.
        city_name = "Buenos Aires" 
        
        # 2. Registra el evento en Cassandra para histórico (se haría con el módulo de Cassandra)
        # 3. Lógica de DOBLE ESCRITURA a Neo4j (el caso de uso 9)
        try:
            await self._update_neo4j_recurrent_booking(user_id, city_name)
        except Exception as e:
            # En un sistema real, esto es un warning. La reserva debe continuar.
            logger.error(f"Fallo en la escritura a Neo4j (reservas recurrentes): {e}")


        # Datos simulados de respuesta
        reservation_data = {
            'id': reservation_id,
            'property_id': property_id,
            'user_id': user_id,
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'status': 'CONFIRMED',
            'created_at': datetime.utcnow().isoformat()
        }

        logger.info("Reserva de ejemplo creada", reservation_id=reservation_id)
        return reservation_data

    async def get_user_reservations(self, user_id: str) -> list:
        """FUNCIÓN DE EJEMPLO: Obtiene las reservas de un usuario."""
        logger.info("Obteniendo reservas de ejemplo", user_id=user_id)

        # Datos simulados
        return [
            {
                'id': f'mock-reservation-1-{user_id}',
                'property_id': 'mock-property-1',
                'user_id': user_id,
                'check_in': '2024-12-01',
                'check_out': '2024-12-05',
                'status': 'CONFIRMED',
                'created_at': '2024-11-15T10:00:00'
            }
        ]