"""
Script de prueba para verificar la conexión con Neo4j AuraDB.
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Obtener credenciales desde variables de entorno
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    print("❌ Error: NEO4J_URI, NEO4J_USER y NEO4J_PASSWORD deben estar configurados")
    print("💡 Tip: Verifica tu archivo .env")
    exit(1)


def test_neo4j_connection():
    """Prueba la conexión con Neo4j AuraDB."""
    try:
        print("🚀 Conectando a Neo4j AuraDB...")
        
        # Crear conexión
        driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        
        # Verificar conectividad
        driver.verify_connectivity()
        print("✅ ¡Conexión exitosa!")
        
        # Limpiar datos de prueba anteriores
        print("\n🧹 Limpiando datos de prueba anteriores...")
        driver.execute_query("""
            MATCH (p:Person {test: true})
            DETACH DELETE p
        """)
        
        # Crear nodos de ejemplo
        print("📝 Creando grafo de ejemplo...")
        summary = driver.execute_query("""
            CREATE (alice:Person {name: $alice_name, age: $alice_age, test: true})
            CREATE (bob:Person {name: $bob_name, age: $bob_age, test: true})
            CREATE (carol:Person {name: $carol_name, age: $carol_age, test: true})
            CREATE (alice)-[:KNOWS {since: $since1}]->(bob)
            CREATE (alice)-[:KNOWS {since: $since2}]->(carol)
            CREATE (bob)-[:WORKS_WITH]->(carol)
            """,
            alice_name="Alice", alice_age=30,
            bob_name="Bob", bob_age=25, 
            carol_name="Carol", carol_age=28,
            since1="2020-01-15", since2="2021-03-10",
            database_="neo4j"
        ).summary
        
        print(f"✅ Creados {summary.counters.nodes_created} nodos y {summary.counters.relationships_created} relaciones")
        
        # Consultar el grafo
        print("\n🔍 Consultando el grafo...")
        
        # Buscar todas las personas
        records, summary, keys = driver.execute_query("""
            MATCH (p:Person {test: true})
            RETURN p.name AS name, p.age AS age
            ORDER BY p.name
            """,
            database_="neo4j"
        )
        
        print("👥 Personas en el grafo:")
        for record in records:
            data = record.data()
            print(f"   - {data['name']} (edad: {data['age']})")
        
        # Buscar relaciones KNOWS
        records, summary, keys = driver.execute_query("""
            MATCH (p1:Person {test: true})-[r:KNOWS]->(p2:Person {test: true})
            RETURN p1.name AS person1, p2.name AS person2, r.since AS since
            """,
            database_="neo4j"
        )
        
        print("\n🤝 Relaciones de conocidos:")
        for record in records:
            data = record.data()
            print(f"   - {data['person1']} conoce a {data['person2']} desde {data['since']}")
        
        # Buscar caminos entre nodos
        records, summary, keys = driver.execute_query("""
            MATCH path = (alice:Person {name: 'Alice', test: true})-[*1..2]-(others:Person {test: true})
            WHERE others.name <> 'Alice'
            RETURN others.name AS connected_person, length(path) AS distance
            ORDER BY distance, connected_person
            """,
            database_="neo4j"
        )
        
        print("\n🌐 Conexiones desde Alice:")
        for record in records:
            data = record.data()
            distance = "directa" if data['distance'] == 1 else f"a {data['distance']} pasos"
            print(f"   - {data['connected_person']} (conexión {distance})")
        
        # Estadísticas del grafo
        records, summary, keys = driver.execute_query("""
            MATCH (p:Person {test: true})
            RETURN count(p) AS total_persons
            """,
            database_="neo4j"
        )
        
        total_persons = records[0].data()['total_persons']
        
        records, summary, keys = driver.execute_query("""
            MATCH ()-[r {test: true}]-()
            RETURN count(r) AS total_relationships
            """,
            database_="neo4j"
        )
        
        # Cerrar conexión
        driver.close()
        
        print(f"\n📊 Estadísticas del grafo de prueba:")
        print(f"   - Total de personas: {total_persons}")
        print(f"   - Total de relaciones: {summary.counters.relationships_created}")
        
        print("\n🎉 ¡Prueba de Neo4j completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🌟 PRUEBA DE CONEXIÓN NEO4J AURADB")
    print("=" * 60)
    print(f"URI: {NEO4J_URI}")
    print(f"Usuario: {NEO4J_USER}")
    print("=" * 60)
    
    test_neo4j_connection()
    
    print("\n" + "=" * 60)
    print("✅ Prueba completada!")
    print("=" * 60)