# Comparación: PostgreSQL vs Redis - Funciones Helper

Este documento muestra cómo el módulo `db/postgres.py` ahora tiene funciones helper similares a `db/redisdb.py`, facilitando el uso consistente de ambas bases de datos en el proyecto.

## 🔄 Estructura Similar

Ambos módulos siguen el mismo patrón de diseño:

| Componente | PostgreSQL | Redis |
|------------|-----------|-------|
| **Pool/Cliente Global** | `_postgres_pool` | `_redis_client` |
| **Función de Conexión** | `get_client()` | `get_client()` |
| **Función de Cierre** | `close_client()` | `close_client()` |
| **Verificación** | `ping()` | ✓ (en `get_client()`) |
| **Logger** | ✓ structlog | ✓ structlog |
| **Retry Logic** | ✓ decorator | ✓ decorator |

## 📊 Comparación de Funciones

### 1. **Verificación de Conexión**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
await client.ping()  # Retorna True si está conectado
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import ping

is_connected = await ping()  # Retorna True/False
```

---

### 2. **Obtener un Valor**

#### Redis
```python
from db.redisdb import get_key

value = await get_key('user:123')
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import get_by_id

user = await get_by_id('users', 123)
# Retorna: {'id': 123, 'name': 'Juan', 'email': 'juan@example.com', ...}
```

---

### 3. **Guardar un Valor**

#### Redis
```python
from db.redisdb import set_key

await set_key('user:123', 'Juan Pérez')
await set_key('session:abc', 'data', expire=3600)  # Con expiración
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import insert_one

user_id = await insert_one('users', {
    'name': 'Juan Pérez',
    'email': 'juan@example.com',
    'city': 'Buenos Aires'
})
# Retorna: 123 (el ID generado)
```

---

### 4. **Actualizar un Valor**

#### Redis
```python
from db.redisdb import set_key

await set_key('user:123', 'Juan García')  # Sobrescribe
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import update_by_id

await update_by_id('users', 123, {
    'name': 'Juan García',
    'city': 'Córdoba'
})
```

---

### 5. **Eliminar un Valor**

#### Redis
```python
from db.redisdb import delete_key

await delete_key('user:123')
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import delete_by_id

await delete_by_id('users', 123)
```

---

### 6. **Trabajar con Hashes (Redis) vs Registros (PostgreSQL)**

#### Redis - Hashes
```python
from db.redisdb import set_hash, get_hash

# Guardar campo en hash
await set_hash('user:123', 'name', 'Juan')
await set_hash('user:123', 'city', 'Buenos Aires')

# Obtener un campo
name = await get_hash('user:123', 'name')

# Obtener todo el hash
user_data = await get_hash('user:123')
# Retorna: {'name': 'Juan', 'city': 'Buenos Aires'}
```

#### PostgreSQL - Registros (Nuevo ✅)
```python
from db.postgres import get_by_id, update_by_id

# Obtener registro completo
user = await get_by_id('users', 123)
# Retorna: {'id': 123, 'name': 'Juan', 'city': 'Buenos Aires', ...}

# Actualizar campos específicos
await update_by_id('users', 123, {
    'name': 'Juan García'
})
```

---

### 7. **Contar Elementos**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
count = await client.scard('colors')  # Contar elementos en un Set
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import count_records

# Contar todos los registros
total = await count_records('users')

# Contar con filtro
ba_users = await count_records('users', 'city = $1', 'Buenos Aires')
```

---

### 8. **Obtener Múltiples Valores**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
members = await client.smembers('colors')  # Todos los elementos de un Set
keys = await client.keys('user:*')  # Todas las claves que coinciden
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import get_all

# Obtener todos con paginación
users = await get_all('users', limit=100, offset=0)
# Retorna: [{'id': 1, 'name': '...', ...}, {'id': 2, ...}, ...]
```

---

### 9. **Consultas Personalizadas**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
# Operaciones específicas de Redis
await client.incr('counter')
await client.sadd('colors', 'red', 'blue')
exists = await client.sismember('colors', 'red')
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import execute_query, execute_query_one

# Consulta que retorna múltiples resultados
users = await execute_query(
    "SELECT * FROM users WHERE age > $1 AND city = $2",
    25, 'Buenos Aires'
)

# Consulta que retorna un solo resultado
user = await execute_query_one(
    "SELECT * FROM users WHERE email = $1",
    'juan@example.com'
)
```

---

### 10. **Transacciones / Operaciones Atómicas**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
# Redis opera con comandos atómicos individuales
await client.incr('counter')  # Atómico por defecto
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import execute_transaction

# Ejecutar múltiples queries en una transacción ACID
await execute_transaction([
    ("INSERT INTO users (name, email) VALUES ($1, $2)", 'Ana', 'ana@example.com'),
    ("UPDATE users SET active = true WHERE city = $1", 'Buenos Aires'),
    ("DELETE FROM sessions WHERE expired = true",)
])
# Todo se ejecuta o nada (ACID)
```

---

### 11. **Verificar Existencia**

#### Redis
```python
from db.redisdb import get_client

client = await get_client()
exists = await client.exists('user:123')  # Retorna 1 o 0
```

#### PostgreSQL (Nuevo ✅)
```python
from db.postgres import table_exists

exists = await table_exists('users')  # Retorna True/False
```

---

## 🎯 Ejemplos de Uso Real

### Ejemplo 1: Sistema de Caché (Redis + PostgreSQL)

```python
from db.redisdb import get_key, set_key
from db.postgres import get_by_id
import json

async def get_user_cached(user_id: int):
    """Obtiene usuario desde cache o DB."""
    
    # Intentar desde cache
    cache_key = f'user:{user_id}'
    cached = await get_key(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Si no está en cache, buscar en DB
    user = await get_by_id('users', user_id)
    
    if user:
        # Guardar en cache por 1 hora
        await set_key(cache_key, json.dumps(dict(user)), expire=3600)
    
    return user
```

### Ejemplo 2: Búsqueda con Filtros

```python
from db.postgres import execute_query

async def search_properties(city: str, max_price: float):
    """Busca propiedades con filtros."""
    
    return await execute_query("""
        SELECT 
            p.id,
            p.title,
            p.description,
            p.price_per_night,
            p.city,
            COUNT(r.id) as total_reviews,
            AVG(r.rating) as avg_rating
        FROM properties p
        LEFT JOIN reviews r ON r.property_id = p.id
        WHERE p.city = $1 
          AND p.price_per_night <= $2
          AND p.active = true
        GROUP BY p.id
        ORDER BY avg_rating DESC, total_reviews DESC
        LIMIT 20
    """, city, max_price)
```

### Ejemplo 3: Estadísticas con Agregación

```python
from db.postgres import execute_query

async def get_booking_stats(days: int = 30):
    """Obtiene estadísticas de reservas."""
    
    return await execute_query("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_bookings,
            SUM(total_price) as revenue,
            AVG(total_price) as avg_booking_value,
            COUNT(DISTINCT user_id) as unique_users
        FROM bookings
        WHERE created_at >= NOW() - INTERVAL '$1 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, days)
```

### Ejemplo 4: Contadores en Tiempo Real (Redis)

```python
from db.redisdb import get_client

async def track_page_view(page: str):
    """Rastrea vistas de página en tiempo real."""
    
    client = await get_client()
    
    # Incrementar contador global
    await client.incr(f'views:{page}')
    
    # Agregar a set de páginas vistas hoy
    today = datetime.now().strftime('%Y-%m-%d')
    await client.sadd(f'pages:{today}', page)
    
    # TTL de 24 horas
    await client.expire(f'pages:{today}', 86400)
```

## 📈 Ventajas del Diseño Similar

### 1. **Consistencia**
Ambos módulos usan el mismo patrón, facilitando el aprendizaje y uso.

### 2. **Type Hints**
Funciones bien documentadas con tipos de retorno claros.

### 3. **Error Handling**
Ambos usan retry logic y logging estructurado.

### 4. **Connection Pooling**
- PostgreSQL: Pool de conexiones (5-20)
- Redis: Pool de conexiones (max 20)

### 5. **Async/Await**
Todas las operaciones son asíncronas para máximo rendimiento.

## 🆚 Cuándo Usar Cada Uno

### Usar **Redis** para:
- ✅ Cache temporal
- ✅ Sesiones de usuario
- ✅ Contadores en tiempo real
- ✅ Rate limiting
- ✅ Pub/Sub
- ✅ Datos que expiran
- ✅ Sets y estructuras simples

### Usar **PostgreSQL** para:
- ✅ Datos persistentes
- ✅ Relaciones complejas
- ✅ Transacciones ACID
- ✅ Búsquedas con JOIN
- ✅ Agregaciones y reportes
- ✅ Datos estructurados
- ✅ Integridad referencial

## 🧪 Tests Disponibles

```bash
# Test básico de PostgreSQL
./run_tests.sh postgres

# Test de helpers de PostgreSQL (nuevo)
./run_tests.sh postgres-helpers

# Test de Redis
./run_tests.sh redis

# Todos los tests
./run_tests.sh all
```

## 📚 Funciones Disponibles

### `db/postgres.py`

| Función | Descripción |
|---------|-------------|
| `get_client()` | Obtiene pool de conexiones |
| `close_client()` | Cierra pool de conexiones |
| `ping()` | Verifica conexión |
| `execute_query()` | Ejecuta SELECT (múltiples resultados) |
| `execute_query_one()` | Ejecuta SELECT (un resultado) |
| `execute_command()` | Ejecuta INSERT/UPDATE/DELETE |
| `insert_one()` | Inserta y retorna ID |
| `update_by_id()` | Actualiza por ID |
| `delete_by_id()` | Elimina por ID |
| `get_by_id()` | Obtiene por ID |
| `get_all()` | Obtiene todos (con paginación) |
| `count_records()` | Cuenta registros |
| `execute_transaction()` | Transacción ACID |
| `table_exists()` | Verifica si tabla existe |

### `db/redisdb.py`

| Función | Descripción |
|---------|-------------|
| `get_client()` | Obtiene cliente Redis |
| `close_client()` | Cierra cliente |
| `get_key()` | Obtiene valor de clave |
| `set_key()` | Establece valor (con TTL) |
| `delete_key()` | Elimina clave |
| `set_hash()` | Establece campo en hash |
| `get_hash()` | Obtiene hash completo o campo |

## ✨ Resumen

Ahora ambos módulos (`postgres.py` y `redisdb.py`) ofrecen:

- ✅ APIs consistentes y fáciles de usar
- ✅ Funciones helper para operaciones comunes
- ✅ Connection pooling optimizado
- ✅ Manejo robusto de errores
- ✅ Logging estructurado
- ✅ Operaciones asíncronas
- ✅ Tests completos

**El módulo PostgreSQL ahora es tan fácil de usar como Redis, manteniendo toda la potencia de SQL cuando se necesita!** 🚀

---

**Actualizado:** 2025-11-14  
**Versión PostgreSQL:** 17.6 (Supabase)  
**Versión Redis:** 5.0.1 (Redis Cloud)

