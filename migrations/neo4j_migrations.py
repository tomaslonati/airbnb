"""
Migraciones para Neo4j AuraDB.
"""

from migrations.base import BaseMigration
from db import neo4j
from utils.logging import get_logger

logger = get_logger(__name__)


class Migration001CreateUserNodes(BaseMigration):
    """Crea nodos de usuarios y restricciones."""

    def __init__(self):
        super().__init__("001", "Crear nodos User y restricciones")

    async def up(self):
        """Crear nodos User y restricciones."""
        queries = [
            # Crear restricción de unicidad para User.id
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",

            # Crear restricción de unicidad para User.email
            "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",

            # Crear índice para búsquedas por nombre
            "CREATE INDEX user_name_index IF NOT EXISTS FOR (u:User) ON (u.name)",

            # Crear índice para búsquedas por ciudad
            "CREATE INDEX user_city_index IF NOT EXISTS FOR (u:User) ON (u.city)"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Nodos User y restricciones creados")

    async def down(self):
        """Eliminar restricciones e índices de User."""
        queries = [
            "DROP CONSTRAINT user_id_unique IF EXISTS",
            "DROP CONSTRAINT user_email_unique IF EXISTS",
            "DROP INDEX user_name_index IF EXISTS",
            "DROP INDEX user_city_index IF EXISTS"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Restricciones e índices de User eliminados")


class Migration002CreatePropertyNodes(BaseMigration):
    """Crea nodos de propiedades y relaciones."""

    def __init__(self):
        super().__init__("002", "Crear nodos Property y relaciones")

    async def up(self):
        """Crear nodos Property y relaciones."""
        queries = [
            # Crear restricción de unicidad para Property.id
            "CREATE CONSTRAINT property_id_unique IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE",

            # Crear índices para búsquedas
            "CREATE INDEX property_city_index IF NOT EXISTS FOR (p:Property) ON (p.city)",
            "CREATE INDEX property_price_index IF NOT EXISTS FOR (p:Property) ON (p.price)",
            "CREATE INDEX property_rating_index IF NOT EXISTS FOR (p:Property) ON (p.rating)",

            # Crear nodos de categorías
            "MERGE (c1:Category {name: 'Apartment'})",
            "MERGE (c2:Category {name: 'House'})",
            "MERGE (c3:Category {name: 'Villa'})",
            "MERGE (c4:Category {name: 'Studio'})",

            # Crear nodos de comodidades
            "MERGE (a1:Amenity {name: 'WiFi'})",
            "MERGE (a2:Amenity {name: 'Pool'})",
            "MERGE (a3:Amenity {name: 'Parking'})",
            "MERGE (a4:Amenity {name: 'Kitchen'})",
            "MERGE (a5:Amenity {name: 'Air Conditioning'})"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Nodos Property, Category, Amenity creados")

    async def down(self):
        """Eliminar nodos y relaciones de Property."""
        queries = [
            "DROP CONSTRAINT property_id_unique IF EXISTS",
            "DROP INDEX property_city_index IF EXISTS",
            "DROP INDEX property_price_index IF EXISTS",
            "DROP INDEX property_rating_index IF EXISTS",
            "MATCH (c:Category) DELETE c",
            "MATCH (a:Amenity) DELETE a"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Nodos Property eliminados")


class Migration003CreateRelationships(BaseMigration):
    """Crea tipos de relaciones principales."""

    def __init__(self):
        super().__init__("003", "Crear tipos de relaciones")

    async def up(self):
        """Crear tipos de relaciones."""
        queries = [
            # Ejemplos de relaciones base (se crearán dinámicamente con datos reales)
            """
            // Las relaciones se crearán cuando se inserten datos reales:
            // (User)-[:OWNS]->(Property)
            // (User)-[:STAYED_AT]->(Property) 
            // (User)-[:REVIEWED]->(Property)
            // (User)-[:KNOWS]->(User)
            // (User)-[:FOLLOWS]->(User)
            // (Property)-[:LOCATED_IN]->(City)
            // (Property)-[:HAS_AMENITY]->(Amenity)
            // (Property)-[:BELONGS_TO]->(Category)
            """

            # Crear nodos de ciudades comunes
            "MERGE (city1:City {name: 'Buenos Aires', country: 'Argentina'})",
            "MERGE (city2:City {name: 'Córdoba', country: 'Argentina'})",
            "MERGE (city3:City {name: 'Mendoza', country: 'Argentina'})",
            "MERGE (city4:City {name: 'Rosario', country: 'Argentina'})",
            "MERGE (city5:City {name: 'Bariloche', country: 'Argentina'})"
        ]

        for query in queries:
            if query.strip() and not query.strip().startswith("//"):
                await neo4j.execute_write_transaction(query)

        logger.info("Tipos de relaciones y ciudades creados")

    async def down(self):
        """Eliminar nodos de ciudades."""
        query = "MATCH (c:City) DELETE c"
        await neo4j.execute_write_transaction(query)
        logger.info("Nodos de ciudades eliminados")


class Migration004CreateRecommendationGraph(BaseMigration):
    """Crea estructura para sistema de recomendaciones."""

    def __init__(self):
        super().__init__("004", "Crear grafo de recomendaciones")

    async def up(self):
        """Crear estructura de recomendaciones."""
        queries = [
            # Crear nodos de preferencias
            "MERGE (pref1:Preference {type: 'budget', value: 'low'})",
            "MERGE (pref2:Preference {type: 'budget', value: 'medium'})",
            "MERGE (pref3:Preference {type: 'budget', value: 'high'})",
            "MERGE (pref4:Preference {type: 'location', value: 'city_center'})",
            "MERGE (pref5:Preference {type: 'location', value: 'beach'})",
            "MERGE (pref6:Preference {type: 'location', value: 'mountain'})",

            # Índices para algoritmos de recomendación
            "CREATE INDEX preference_type_index IF NOT EXISTS FOR (p:Preference) ON (p.type)",
            "CREATE INDEX city_name_index IF NOT EXISTS FOR (c:City) ON (c.name)"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Estructura de recomendaciones creada")

    async def down(self):
        """Eliminar estructura de recomendaciones."""
        queries = [
            "MATCH (p:Preference) DELETE p",
            "DROP INDEX preference_type_index IF EXISTS",
            "DROP INDEX city_name_index IF EXISTS"
        ]

        for query in queries:
            await neo4j.execute_write_transaction(query)

        logger.info("Estructura de recomendaciones eliminada")

class Migration005CreateRecurrentBookings(BaseMigration):
    """
    Crea el índice para optimizar la consulta de usuarios que regresan.
    Se basa en la relación User-[:BOOKED_IN]->City, que tendrá una propiedad 'count'.
    """

    def __init__(self):
        super().__init__("005", "Crear índice de conteo para usuarios recurrentes")

    async def up(self):
        """Crear el índice de conteo de reservas (r.count)."""
        
        # El índice se crea sobre la propiedad 'count' de la relación BOOKED_IN,
        # lo que permite consultas rápidas como WHERE r.count >= 2.
        query = """
            CREATE INDEX booked_in_count_idx IF NOT EXISTS 
            FOR ()-[r:BOOKED_IN]-() ON (r.count)
        """
        
        await neo4j.execute_write_transaction(query)
        logger.info("Índice 'booked_in_count_idx' creado.")

    async def down(self):
        """Eliminar índice."""
        await neo4j.execute_write_transaction("DROP INDEX booked_in_count_idx IF EXISTS")
        logger.info("Índice de conteo de reservas eliminado.")