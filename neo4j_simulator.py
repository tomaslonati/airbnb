"""
Simulador de Neo4j para casos cuando la base de datos no esté disponible.
Permite que el sistema funcione completamente para demostración del TP.
"""

from utils.logging import get_logger
import json
import asyncio

logger = get_logger(__name__)


class Neo4jSimulator:
    """Simulador de funcionalidad Neo4j para demostración."""

    def __init__(self):
        self.logger = logger
        self.simulated_data = {
            "user_communities": {},
            "property_recommendations": {},
            "user_interactions": []
        }

    def simulate_community_analysis(self, user_id: int, location: str):
        """Simula análisis de comunidades en Neo4j."""
        try:
            # Simular datos de comunidad
            community_data = {
                "user_id": user_id,
                "location": location,
                "community_score": 0.85,
                "similar_users": [user_id + 1, user_id + 2, user_id + 3],
                "recommendations": [
                    {"property_id": 10, "score": 0.92},
                    {"property_id": 15, "score": 0.87},
                    {"property_id": 23, "score": 0.83}
                ]
            }

            self.simulated_data["user_communities"][user_id] = community_data
            self.logger.info(
                f"✅ Neo4j SIMULADO: Análisis de comunidad para usuario {user_id} en {location}")

            return {
                "success": True,
                "community_score": community_data["community_score"],
                "recommendations_count": len(community_data["recommendations"]),
                "similar_users": len(community_data["similar_users"])
            }

        except Exception as e:
            self.logger.error(f"Error en simulación Neo4j: {e}")
            return {"success": False, "error": str(e)}

    def simulate_user_interaction(self, guest_id: int, host_id: int, interaction_type: str):
        """Simula creación de interacciones usuario-host."""
        try:
            interaction = {
                "guest_id": guest_id,
                "host_id": host_id,
                "interaction_type": interaction_type,
                "timestamp": asyncio.get_event_loop().time(),
                "relationship_strength": 0.75
            }

            self.simulated_data["user_interactions"].append(interaction)
            self.logger.info(
                f"✅ Neo4j SIMULADO: Interacción {interaction_type} entre guest {guest_id} y host {host_id}")

            return {
                "success": True,
                "interaction_id": len(self.simulated_data["user_interactions"]),
                "relationship_strength": interaction["relationship_strength"]
            }

        except Exception as e:
            self.logger.error(f"Error en simulación de interacción: {e}")
            return {"success": False, "error": str(e)}

    def simulate_recurrent_booking_analysis(self, user_id: int, property_id: int):
        """Simula análisis de reservas recurrentes."""
        try:
            # Simular análisis de patrones
            pattern_analysis = {
                "user_id": user_id,
                "property_id": property_id,
                "booking_frequency": "monthly",
                "loyalty_score": 0.78,
                "predicted_next_booking": "2025-01-15",
                "recommended_properties": [property_id, property_id + 1, property_id + 2]
            }

            self.logger.info(
                f"✅ Neo4j SIMULADO: Análisis de reservas recurrentes para usuario {user_id}")

            return {
                "success": True,
                "loyalty_score": pattern_analysis["loyalty_score"],
                "frequency": pattern_analysis["booking_frequency"],
                "next_predicted": pattern_analysis["predicted_next_booking"]
            }

        except Exception as e:
            self.logger.error(
                f"Error en simulación de análisis recurrente: {e}")
            return {"success": False, "error": str(e)}

    def get_simulation_summary(self):
        """Retorna resumen de la simulación."""
        return {
            "total_communities": len(self.simulated_data["user_communities"]),
            "total_interactions": len(self.simulated_data["user_interactions"]),
            "simulation_status": "active",
            "simulated_operations": [
                "Community Analysis",
                "User Interactions",
                "Recurrent Booking Patterns",
                "Property Recommendations"
            ]
        }


# Instancia global del simulador
neo4j_simulator = Neo4jSimulator()
