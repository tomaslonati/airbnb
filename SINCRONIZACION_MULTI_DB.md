# 🔄 Sincronización Multi-Base de Datos

## Arquitectura General

```
                    ┌─────────────────────────┐
                    │   PostgreSQL (ACID)     │
                    │   Source of Truth       │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴───────────┐
                    │  COMMIT EXITOSO       │
                    └───────────┬───────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐  ┌──────────────┐
    │   Cassandra   │   │    MongoDB    │  │    Neo4j     │
    │  (Analytics)  │   │ (Agregaciones)│  │   (Grafos)   │
    └───────────────┘   └───────────────┘  └──────────────┘
         ASYNC               ASYNC              ASYNC
    (No bloquea)        (No bloquea)       (No bloquea)

    ❌ Si falla: Se loggea, pero NO revierte PostgreSQL
```

---

## 📊 Patrón 1: PostgreSQL → Cassandra

### **Objetivo**: Desnormalizar datos para queries analíticas rápidas

### **Implementación**: Write-Behind Pattern

```python
# services/reservations.py - create_reservation()

async def create_reservation(...):
    # ═══════════════════════════════════════════════════
    # FASE 1: ACID TRANSACTION EN POSTGRESQL
    # ═══════════════════════════════════════════════════
    pool = await get_client()
    async with pool.acquire() as conn:
        async with conn.transaction():  # ✅ Transacción ACID
            # Validar disponibilidad
            is_available = await self._check_availability(...)

            # Calcular precio
            total_price = await self._calculate_total_price(...)

            # Insertar reserva
            query = """
                INSERT INTO reserva (
                    propiedad_id, huesped_id, fecha_check_in,
                    fecha_check_out, monto_final, estado_reserva_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            result = await conn.fetchrow(query, ...)
            reserva_id = result['id']

            # Marcar fechas como no disponibles
            await self._mark_dates_unavailable(...)

            # ✅ COMMIT implícito al salir del bloque
            logger.info(f"✅ Reserva {reserva_id} creada en PostgreSQL")

    # ═══════════════════════════════════════════════════
    # FASE 2: SINCRONIZACIÓN ASYNC (FUERA DE TRANSACCIÓN)
    # ═══════════════════════════════════════════════════

    # ⚡ Sincronizar a Cassandra (no bloquea)
    await self._sync_reservation_to_cassandra(
        reserva_id=str(reserva_id),
        event_type="CREATED",
        propiedad_id=propiedad_id,
        huesped_id=str(huesped_id),
        check_in=check_in,
        check_out=check_out,
        monto_total=total_price
    )
    # ❌ Si falla: Solo se loggea, NO se revierte PostgreSQL

    # ⚡ Invalidar cache Redis
    from services.search import invalidate_search_cache_for_city
    await invalidate_search_cache_for_city(ciudad_id)

    # ⚡ Actualizar Neo4j (comunidades y usuarios recurrentes)
    await self._update_neo4j_recurrent_booking(huesped_id, city_name)

    return {"success": True, "reservation": {...}}
```

### **Manejo de Errores en Cassandra**

```python
async def _sync_reservation_to_cassandra(...):
    try:
        repo = await self.cassandra_repo
        if not repo:
            logger.warning("Cassandra no disponible, saltando sincronización")
            return  # ✅ Continúa sin fallar

        # Sincronizar datos
        await repo.sync_reservation_creation(...)
        logger.info("✅ Sincronizado con Cassandra")

    except Exception as e:
        # ❌ Error en Cassandra NO revierte PostgreSQL
        logger.error(f"❌ Error sincronizando Cassandra: {e}")
        logger.info(f"📝 Evento registrado para reintento futuro")
        # Sistema continúa funcionando
```

### **Garantías**

- ✅ **PostgreSQL**: ACID - Datos consistentes siempre
- ⚠️  **Cassandra**: Eventual Consistency - Puede tener latencia
- 🔄 **Reconciliación**: Posible implementar job de reconciliación periódica

---

## 📈 Patrón 2: PostgreSQL → MongoDB

### **Objetivo**: Mantener agregaciones y estadísticas precalculadas

### **Implementación**: Event-Driven Updates

```python
# services/reviews.py - create_review()

async def create_review(reserva_id, huesped_id, anfitrion_id, puntaje, comentario):
    # ═══════════════════════════════════════════════════
    # PASO 1: VALIDAR EN POSTGRESQL
    # ═══════════════════════════════════════════════════
    validation = await self._validate_reservation(...)
    if not validation['valid']:
        return {"success": False, "error": "..."}

    # ═══════════════════════════════════════════════════
    # PASO 2: INSERTAR EN POSTGRESQL (SOURCE OF TRUTH)
    # ═══════════════════════════════════════════════════
    review_id = await self._insert_review_postgres(...)
    logger.info(f"✅ Reseña {review_id} insertada en PostgreSQL")

    # ═══════════════════════════════════════════════════
    # PASO 3: ACTUALIZAR ESTADÍSTICAS EN MONGODB
    # ═══════════════════════════════════════════════════
    mongo_result = await self._update_mongo_stats(anfitrion_id, puntaje)
    if not mongo_result['success']:
        logger.warning(f"⚠️  MongoDB falló: {mongo_result['error']}")
        # ✅ Reseña existe en PostgreSQL, continúa el flujo

    # ═══════════════════════════════════════════════════
    # PASO 4: ENRIQUECER GRAFO EN NEO4J
    # ═══════════════════════════════════════════════════
    neo4j_result = await self._update_neo4j_review(...)
    if not neo4j_result['success']:
        logger.warning(f"⚠️  Neo4j falló: {neo4j_result['error']}")

    # ═══════════════════════════════════════════════════
    # PASO 5: RETORNAR RESULTADO PARCIAL
    # ═══════════════════════════════════════════════════
    return {
        "success": True,
        "review_id": review_id,
        "postgres_success": True,      # ✅ Crítico
        "mongo_success": mongo_result['success'],    # ⚠️  Opcional
        "neo4j_success": neo4j_result['success'],    # ⚠️  Opcional
        "message": "Reseña creada exitosamente"
    }
```

### **Actualización de Estadísticas en MongoDB**

```python
async def _update_mongo_stats(anfitrion_id: int, puntaje: int):
    try:
        collection = get_collection("host_statistics")

        # Obtener estadísticas actuales
        current_stats = collection.find_one({"host_id": anfitrion_id})

        if current_stats:
            # Actualizar estadísticas existentes (agregaciones)
            total_reviews = current_stats.get('total_reviews', 0) + 1
            total_rating = current_stats.get('total_rating', 0) + puntaje
            avg_rating = total_rating / total_reviews

            collection.update_one(
                {"host_id": anfitrion_id},
                {
                    "$set": {
                        "total_reviews": total_reviews,
                        "avg_rating": round(avg_rating, 2),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "recent_ratings": {"rating": puntaje, "date": datetime.utcnow()}
                    }
                }
            )
        else:
            # Crear documento inicial
            collection.insert_one({
                "host_id": anfitrion_id,
                "total_reviews": 1,
                "avg_rating": puntaje,
                "recent_ratings": [{"rating": puntaje, "date": datetime.utcnow()}]
            })

        return {"success": True}

    except Exception as e:
        logger.error(f"Error en MongoDB: {e}")
        return {"success": False, "error": str(e)}
```

### **Garantías**

- ✅ **PostgreSQL**: Todas las reseñas están guardadas
- ⚠️  **MongoDB**: Puede tener estadísticas desactualizadas temporalmente
- 🔄 **Reconciliación**: Job nocturno recalcula estadísticas desde PostgreSQL

---

## 🕸️ Patrón 3: PostgreSQL → Neo4j

### **Objetivo**: Mantener grafo de relaciones sociales

### **Implementación**: Dual-Write Pattern

```python
# services/reservations.py - create_reservation()

# Después de crear reserva en PostgreSQL...

# ═══════════════════════════════════════════════════
# ACTUALIZACIÓN 1: USUARIOS RECURRENTES (CU 9)
# ═══════════════════════════════════════════════════
try:
    await self._update_neo4j_recurrent_booking(huesped_id, city_name)
    # Crea/actualiza: (User)-[BOOKED_IN {count}]->(City)
except Exception as e:
    logger.error(f"❌ Neo4j (recurrentes) falló: {e}")
    # Fallback al simulador
    result = neo4j_simulator.simulate_recurrent_booking_analysis(...)

# ═══════════════════════════════════════════════════
# ACTUALIZACIÓN 2: COMUNIDADES HOST-HUÉSPED (CU 10)
# ═══════════════════════════════════════════════════
try:
    neo4j_result = await self.neo4j_service.create_host_guest_interaction(
        host_user_id=anfitrion_id,
        guest_user_id=huesped_id,
        reservation_id=reserva_id,
        reservation_date=check_in,
        property_id=propiedad_id
    )
    # Crea/actualiza: (Guest)-[INTERACCIONES {count, reservas[], propiedades[]}]->(Host)

    if neo4j_result.get('is_community'):
        logger.info(f"🏘️ ¡Nueva comunidad! {total_interactions} interacciones")

except Exception as e:
    logger.warning(f"❌ Neo4j (comunidades) falló: {e}")
    # Fallback al simulador
    neo4j_simulator.simulate_user_interaction(...)
```

### **Query Neo4j - Usuarios Recurrentes**

```cypher
// Crear/actualizar relación User-City
MERGE (u:User {id: $user_id})
MERGE (c:City {name: $city_name})
MERGE (u)-[r:BOOKED_IN]->(c)
ON CREATE SET r.count = 1
ON MATCH SET r.count = r.count + 1
RETURN r.count as count
```

### **Query Neo4j - Comunidades Host-Huésped**

```cypher
// Crear/actualizar relación Guest-Host
MERGE (host:Usuario {user_id: $host_id})
MERGE (guest:Usuario {user_id: $guest_id})
MERGE (guest)-[rel:INTERACCIONES]->(host)
ON CREATE SET
    rel.count = 1,
    rel.reservas = [$reservation_id],
    rel.propiedades = [$property_id],
    rel.primera_interaccion = date($fecha),
    rel.created_at = datetime()
ON MATCH SET
    rel.count = rel.count + 1,
    rel.reservas = rel.reservas + $reservation_id,
    rel.propiedades = CASE
        WHEN $property_id IN rel.propiedades
        THEN rel.propiedades
        ELSE rel.propiedades + $property_id
    END,
    rel.ultima_interaccion = date($fecha)
RETURN
    rel.count as total_interacciones,
    size(rel.propiedades) as propiedades_distintas
```

### **Garantías**

- ✅ **PostgreSQL**: Reservas siempre almacenadas
- ⚠️  **Neo4j**: Grafo puede tener relaciones faltantes
- 🔄 **Fallback**: Simulador para demostración si Neo4j falla
- 🔄 **Reconciliación**: Script de rebuild del grafo desde PostgreSQL

---

## 💾 Patrón 4: PostgreSQL → Redis

### **Objetivo**: Cache de lectura con invalidación inteligente

### **Implementación**: Cache-Aside + Write-Invalidate

```python
# services/search.py

async def search_properties(ciudad, capacidad_minima=None, precio_maximo=None):
    # ═══════════════════════════════════════════════════
    # PASO 1: INTENTAR LEER DESDE CACHE
    # ═══════════════════════════════════════════════════
    cache_key = self._generate_cache_key(ciudad, capacidad_minima, precio_maximo)
    cached_data = await get_key(cache_key)

    if cached_data:
        logger.info(f"🟢 CACHE HIT: {cache_key}")
        result = json.loads(cached_data)
        result['cached'] = True
        return result

    # ═══════════════════════════════════════════════════
    # PASO 2: CACHE MISS - CONSULTAR POSTGRESQL
    # ═══════════════════════════════════════════════════
    logger.info(f"🔴 CACHE MISS: Consultando PostgreSQL")

    pool = await postgres.get_client()
    rows = await pool.fetch("""
        SELECT p.id, p.nombre, p.capacidad, AVG(pd.price_per_night) as precio
        FROM propiedad p
        JOIN ciudad c ON p.ciudad_id = c.id
        JOIN propiedad_servicio ps ON p.id = ps.propiedad_id
        WHERE c.nombre = $1
        AND p.capacidad >= $2
        ...
    """, ciudad, capacidad_minima)

    result = {
        "success": True,
        "properties": [dict(row) for row in rows],
        "count": len(rows),
        "cached": False
    }

    # ═══════════════════════════════════════════════════
    # PASO 3: GUARDAR EN CACHE CON TTL
    # ═══════════════════════════════════════════════════
    await set_key(cache_key, json.dumps(result), expire=300)  # 5 minutos

    # Trackear clave para invalidación posterior
    tracking_key = f"search_keys:ciudad:{ciudad_id}"
    await add_to_set(tracking_key, cache_key)

    logger.info(f"💾 Guardado en cache: {cache_key} (TTL: 5 min)")

    return result
```

### **Invalidación del Cache**

```python
# services/reservations.py - create_reservation()

# Después de crear reserva en PostgreSQL...

# ═══════════════════════════════════════════════════
# INVALIDAR CACHE DE BÚSQUEDAS PARA LA CIUDAD
# ═══════════════════════════════════════════════════
try:
    from services.search import invalidate_search_cache_for_city
    await invalidate_search_cache_for_city(propiedad['ciudad_id'])
    logger.info(f"🗑️  Cache invalidado para ciudad_id {propiedad['ciudad_id']}")
except Exception as cache_error:
    logger.warning(f"⚠️  Error invalidando cache: {cache_error}")
    # No fallar la reserva por esto


# services/search.py
async def invalidate_search_cache_for_city(ciudad_id: int):
    """Invalida todas las búsquedas en cache para una ciudad."""
    tracking_key = f"search_keys:ciudad:{ciudad_id}"
    deleted_count = await delete_keys_in_set(tracking_key)
    logger.info(f"🗑️  {deleted_count} claves eliminadas del cache")
```

### **Garantías**

- ✅ **PostgreSQL**: Source of truth siempre actualizado
- ✅ **Redis**: Cache se invalida automáticamente al crear/cancelar reservas
- ⚡ **Performance**: Primera búsqueda lenta, subsiguientes < 1ms
- 🕐 **TTL**: Cache expira a los 5 minutos automáticamente

---

## 🛠️ Estrategias de Reconciliación

### **1. Job Nocturno de Reconciliación**

```python
# jobs/reconciliation_job.py

async def reconcile_cassandra_reservations():
    """
    Job nocturno que compara PostgreSQL vs Cassandra
    y sincroniza diferencias.
    """
    # Obtener todas las reservas de PostgreSQL
    pg_reservations = await postgres.fetch("""
        SELECT id, propiedad_id, huesped_id, fecha_check_in, fecha_check_out
        FROM reserva
        WHERE created_at > NOW() - INTERVAL '7 days'
    """)

    # Para cada reserva, verificar si existe en Cassandra
    for reservation in pg_reservations:
        exists_in_cassandra = await check_cassandra_reservation(reservation.id)

        if not exists_in_cassandra:
            # Resincronizar
            await sync_reservation_to_cassandra(reservation)
            logger.info(f"🔄 Resincronizada reserva {reservation.id}")
```

### **2. Event Sourcing (Futuro)**

```python
# Para sistemas críticos, guardar todos los eventos

# events/reservation_created.py
async def handle_reservation_created(event):
    """
    Evento: Reserva creada en PostgreSQL

    Subscriptores:
    - Cassandra Sync Handler
    - MongoDB Stats Handler
    - Neo4j Graph Handler
    - Redis Cache Invalidator
    """
    await asyncio.gather(
        sync_to_cassandra(event),
        update_mongo_stats(event),
        update_neo4j_graph(event),
        invalidate_redis_cache(event)
    )
```

### **3. Monitoring y Alertas**

```python
# Monitorear inconsistencias

async def check_sync_health():
    """Verifica que las bases estén sincronizadas."""

    # Contar reservas en cada DB
    pg_count = await postgres.fetchval("SELECT COUNT(*) FROM reserva")
    cassandra_count = await cassandra.count_reservations()

    diff = abs(pg_count - cassandra_count)

    if diff > 100:
        # Alerta: Diferencia > 100 registros
        logger.error(f"⚠️  INCONSISTENCIA: PG={pg_count}, Cassandra={cassandra_count}")
        send_alert("Bases desincronizadas")
```

---

## 📋 Resumen de Garantías

| Base de Datos | Rol | Consistencia | Manejo de Fallo |
|---------------|-----|--------------|-----------------|
| **PostgreSQL** | Source of Truth | ACID (Strong) | ❌ Falla = Rollback completo |
| **Cassandra** | Analytics denormalized | Eventual | ⚠️  Falla = Se loggea, continúa |
| **MongoDB** | Agregaciones | Eventual | ⚠️  Falla = Se loggea, continúa |
| **Neo4j** | Grafos de relaciones | Eventual | ⚠️  Falla = Fallback a simulador |
| **Redis** | Cache con TTL | Cache-Aside | ⚠️  Falla = Sin cache, continúa |

---

## 🎯 Decisiones de Diseño

### **¿Por qué NO revertir PostgreSQL si falla NoSQL?**

1. **Disponibilidad > Consistencia**: Sistema sigue funcionando
2. **PostgreSQL es la verdad**: Podemos reconstruir NoSQL desde ahí
3. **Fallos temporales**: Red puede fallar momentáneamente
4. **Reconciliación posterior**: Jobs nocturnos corrigen inconsistencias

### **¿Cuándo SÍ revertir?**

Solo si falla una operación **crítica** en PostgreSQL:
- Validación de disponibilidad
- Cálculo de precio
- Inserción de reserva
- Marcar fechas como no disponibles

### **Trade-offs**

✅ **Ventajas**:
- Alta disponibilidad
- Performance (operaciones async)
- Escalabilidad independiente de cada DB

⚠️ **Desventajas**:
- Eventual consistency
- Posibles inconsistencias temporales
- Complejidad de reconciliación

---

## 🔍 Debugging de Sincronización

### **Script de Verificación**

```bash
# Verificar que una reserva esté sincronizada
python scripts/verify_sync.py --reservation-id 123

# Output:
✅ PostgreSQL: Reserva 123 existe
✅ Cassandra: Reserva 123 encontrada en 3 tablas
⚠️  MongoDB: Stats del host desactualizadas
✅ Neo4j: Relación User-City actualizada
✅ Redis: Cache invalidado correctamente
```

### **Logs Estructurados**

```python
logger.info("Reserva creada",
    reserva_id=reserva_id,
    postgres_success=True,
    cassandra_success=cassandra_ok,
    neo4j_success=neo4j_ok,
    redis_invalidated=cache_cleared
)
```

---

## 📚 Referencias

- **CAP Theorem**: Elegimos Availability + Partition Tolerance
- **BASE**: Basically Available, Soft state, Eventual consistency
- **Write-Behind Pattern**: Cassandra sync
- **Cache-Aside Pattern**: Redis cache
- **Event Sourcing**: Futuro para audit trail completo
