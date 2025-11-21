"""
Test del nuevo formato de logging legible.
"""

from utils.logging import configure_logging, get_logger
import time

# Configurar logging legible
configure_logging()
logger = get_logger("test_logging")

print("🧪 TESTING NUEVO FORMATO DE LOGGING")
print("=" * 50)

# Diferentes niveles de log
logger.info("✅ Sistema inicializado correctamente")
logger.info("🔗 Conectando a PostgreSQL", database="supabase",
            host="aws-1-sa-east-1.pooler.supabase.com")
logger.info("🔗 Conectando a Redis", host="redis-cloud", status="conectado")
logger.warning("⚠️ Neo4j no disponible, usando simulador", reason="DNS error")
logger.error("❌ Error de conexión", database="test", error="timeout")
logger.info("🎉 Login exitoso", user="tomaslonati@gmail.com", user_id=25)
logger.info("📊 Reserva creada", reserva_id=26, precio=200.0, propiedad=8)
logger.info("💾 Datos sincronizados", target="Cassandra",
            collection="reservas_por_ciudad_fecha")

print("\n" + "=" * 50)
print("✅ Test de logging completado")
print("📊 Nuevo formato: ✅ Más legible ✅ Con colores ✅ Timestamps simples")
