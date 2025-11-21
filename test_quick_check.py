"""Test simple de quick check de Neo4j"""

import time
from db.neo4j import quick_check
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("quick_test")

print("🔍 Testing Neo4j Quick Check...")

start_time = time.time()
result = quick_check()
elapsed = time.time() - start_time

print(f"⏱️ Tiempo: {elapsed:.3f}s")
print(f"📊 Resultado: {'✅ DNS OK' if result else '❌ DNS Fail'}")
print(f"🎯 Optimización: {'Exitosa' if elapsed < 1.0 else 'Necesita mejora'}")