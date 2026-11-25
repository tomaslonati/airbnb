# Airbnb Backend - Sistema Multi-Base de Datos

> **English summary.** Airbnb-style backend CLI (university project) that uses five cloud databases, each for what it does best: PostgreSQL (Supabase) for transactional data, Redis for cache and sessions, Cassandra (AstraDB) for event logs, MongoDB Atlas for analytics and Neo4j (AuraDB) for user-relationship graphs. Built with Python 3.10+, Typer, Pydantic and asyncio.

Backend CLI para un sistema tipo Airbnb que utiliza múltiples bases de datos en la nube para diferentes casos de uso.

## 🏗️ Arquitectura

El proyecto implementa una arquitectura modular que conecta con 5 bases de datos cloud:

- **PostgreSQL (Supabase)**: Datos transaccionales (reservas, usuarios, propiedades)
- **Cassandra (AstraDB)**: Logs y eventos históricos
- **MongoDB Atlas**: Datos analíticos y métricas agregadas
- **Neo4j AuraDB**: Grafos de relaciones entre usuarios
- **Redis Cloud**: Cache y sesiones

## 📁 Estructura del Proyecto

```
project/
├── main.py                      # Entry point (Typer CLI)
├── config.py                    # Configuración Pydantic BaseSettings
├── .env.example                 # Plantilla de variables de entorno
├── cli/
│   └── commands.py              # Comandos registrados de Typer
├── db/
│   ├── postgres.py              # Conexión Supabase/Postgres
│   ├── cassandra.py             # Conexión AstraDB
│   ├── mongo.py                 # Conexión Mongo Atlas
│   ├── neo4j.py                 # Conexión Neo4j Aura
│   └── redisdb.py               # Conexión Redis Cloud
├── services/
│   ├── search.py                # Búsquedas con cache (Postgres + Redis)
│   ├── reservations.py          # Gestión de reservas (Postgres + Cassandra)
│   └── analytics.py             # Analíticas (MongoDB + Neo4j)
├── migrations/
│   ├── base.py                  # Base para todas las migraciones
│   ├── manager.py               # Gestor principal de migraciones
│   ├── postgres_migrations.py   # Migraciones PostgreSQL
│   ├── cassandra_migrations.py  # Migraciones Cassandra
│   ├── mongo_migrations.py      # Migraciones MongoDB
│   └── neo4j_migrations.py      # Migraciones Neo4j
├── routes/
│   ├── base.py                  # Base para todas las rutas
│   ├── registry.py              # Registro centralizado de rutas
│   ├── search_routes.py         # Rutas de búsqueda
│   ├── reservation_routes.py    # Rutas de reservas
│   ├── analytics_routes.py      # Rutas de analíticas
│   └── admin_routes.py          # Rutas administrativas
├── utils/
│   ├── logging.py               # Logging estructurado
│   └── retry.py                 # Funciones de retry con tenacity
├── requirements.txt             # Dependencias Python
└── README.md                    # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y completa con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales de cada servicio cloud.

### 3. Ejecutar migraciones

```bash
# Ver estado de migraciones
python main.py migrate status

# Ejecutar todas las migraciones
python main.py migrate run
```

### 4. Verificar configuración

```bash
python main.py status
```

## 💻 Uso del CLI

### Gestión de migraciones

```bash
# Ver estado de migraciones
python main.py migrate status

# Ejecutar todas las migraciones pendientes
python main.py migrate run

# Ejecutar sin confirmación
python main.py migrate run --force

# Revertir una migración específica
python main.py migrate rollback --version 003 --force
```

### Verificación del sistema

```bash
# Estado general del sistema y bases de datos
python main.py status

# Diagnóstico completo de salud
python main.py admin health

# Listar todas las rutas disponibles
python main.py routes
```

### Administración del sistema

```bash
# Limpiar todos los caches
python main.py admin clear-cache

# Limpiar caches sin confirmación
python main.py admin clear-cache --force
```

### Búsqueda de propiedades (PostgreSQL + Redis)

```bash
# Buscar propiedades en Buenos Aires
python main.py search "Buenos Aires"

# Buscar con precio máximo
python main.py search "Córdoba" --max-price 200

# Buscar limpiando cache primero
python main.py search "Mendoza" --clear-cache
```

### Gestión de reservas (PostgreSQL + Cassandra)

```bash
# Crear una nueva reserva
python main.py reservation create \
  --user user-123 \
  --property prop-456 \
  --check-in 2024-12-15 \
  --check-out 2024-12-20

# Listar reservas de un usuario
python main.py reservation list --user user-123
```

### Analíticas y reportes (MongoDB + Neo4j)

```bash
# Métricas de reservas de los últimos 30 días
python main.py analytics bookings --days 30

# Análisis de red social de un usuario
python main.py analytics network --user user-123
```

## 🛠️ Tecnologías

### Core

- **Python 3.10+**
- **Typer**: Framework para CLI
- **Pydantic**: Validación y configuración
- **asyncio**: Programación asíncrona

### Bases de Datos

- **asyncpg**: Driver async para PostgreSQL
- **cassandra-driver**: Driver para AstraDB/Cassandra
- **motor**: Driver async para MongoDB
- **neo4j-driver**: Driver async para Neo4j
- **redis-py**: Cliente async para Redis

### Utilidades

- **tenacity**: Reintentos automáticos
- **structlog**: Logging estructurado
- **python-dotenv**: Gestión de variables de entorno

## 📊 Casos de Uso por Base de Datos

### PostgreSQL (Supabase)

- ✅ Datos de usuarios, propiedades y reservas
- ✅ Consultas transaccionales ACID
- ✅ Búsquedas con filtros complejos

### Redis Cloud

- ✅ Cache de resultados de búsquedas
- ✅ Sesiones de usuario
- ✅ Contadores en tiempo real

### Cassandra (AstraDB)

- ✅ Logs de eventos de reservas
- ✅ Histórico de acciones de usuario
- ✅ Datos de series temporales

### MongoDB Atlas

- ✅ Métricas agregadas de negocio
- ✅ Datos analíticos procesados
- ✅ Reportes de performance

### Neo4j AuraDB

- ✅ Grafos de relaciones usuario-usuario
- ✅ Recomendaciones basadas en red social
- ✅ Análisis de centralidad y conectividad

## 🔧 Desarrollo

### Sistema de Migraciones

El proyecto incluye un sistema robusto de migraciones para todas las bases de datos:

#### Estructura de Migraciones

- **Base abstracta**: `migrations/base.py` define la interfaz común
- **Gestor centralizado**: `migrations/manager.py` coordina todas las DBs
- **Migraciones específicas**: Un archivo por base de datos con todas sus tablas/colecciones

#### Creación de Esquemas

- **PostgreSQL**: Tablas relacionales con restricciones e índices
- **Cassandra**: Tablas optimizadas para series temporales
- **MongoDB**: Colecciones con índices para agregaciones
- **Neo4j**: Nodos, relaciones y restricciones de unicidad

#### Ejecución

```bash
python main.py migrate run    # Ejecutar todas las pendientes
python main.py migrate status # Ver estado actual
```

### Sistema de Rutas

Arquitectura modular para endpoints/funcionalidades:

#### Estructura de Rutas

- **Base abstracta**: `routes/base.py` define interfaz común
- **Registro centralizado**: `routes/registry.py` gestiona todas las rutas
- **Rutas específicas**: Agrupadas por funcionalidad (search, reservations, etc.)

#### Características

- Validación automática de parámetros
- Manejo consistente de errores
- Logging estructurado
- Ejecución asíncrona

#### Uso Programático

```python
from routes.registry import execute_route

result = await execute_route("search_properties", {
    "city": "Buenos Aires",
    "max_price": 200
})
```

### Estructura de módulos

Cada módulo de base de datos (`db/*.py`) expone una función principal:

- `get_client()`: Retorna cliente/pool de conexiones
- Funciones auxiliares para operaciones comunes

### Servicios

Los servicios en `services/` implementan la lógica de negocio:

- **SearchService**: Búsquedas con cache inteligente
- **ReservationService**: Gestión de reservas multi-DB
- **AnalyticsService**: Generación de reportes y métricas

### Logging

El sistema usa logging estructurado con `structlog`:

- Logs en formato JSON para análisis
- Contexto automático por operación
- Niveles configurables por variable de entorno

### Reintentos

Todas las operaciones de DB incluyen reintentos automáticos:

- Backoff exponencial configurable
- Reintentos solo en errores de conexión
- Logging detallado de fallos

## 🔐 Seguridad

- ✅ Credenciales solo por variables de entorno
- ✅ Conexiones TLS/SSL a todos los servicios
- ✅ Timeouts configurables para prevenir cuelgues
- ✅ Validación de entrada con Pydantic

## 📈 Escalabilidad

- ✅ Pools de conexiones configurables
- ✅ Operaciones asíncronas para I/O concurrente
- ✅ Cache inteligente para reducir carga en DB primaria
- ✅ Separación de responsabilidades por tipo de dato

## 🧪 Testing

### Tests de Conexión a Bases de Datos

El proyecto incluye scripts de prueba para verificar las conexiones a las bases de datos:

#### Ejecutar todos los tests

```bash
./run_tests.sh
```

#### Ejecutar test específico

```bash
# Test PostgreSQL/Supabase
./run_tests.sh postgres

# Test Redis
./run_tests.sh redis
```

#### Ejecutar tests manualmente

```bash
# Test PostgreSQL
PYTHONPATH=. python tests/test_postgres.py

# Test Redis
PYTHONPATH=. python tests/test_redis.py
```

### Tests Disponibles

- **`tests/test_postgres.py`**: Verifica conexión a Supabase PostgreSQL
  - Conexión y ping
  - Versión de PostgreSQL
  - Extensiones disponibles
  - Creación de tablas
  - CRUD operations
  - Estado del pool de conexiones

- **`tests/test_redis.py`**: Verifica conexión a Redis Cloud
  - Conexión y ping
  - Operaciones SET/GET
  - Expiración de claves
  - Contadores
  - Operaciones con Sets

### Tests de Integración

Para agregar más tests, crear en el directorio `tests/`:

- Tests unitarios por servicio
- Tests de integración con bases de datos
- Tests de CLI con datos simulados

## 🚀 Despliegue

El proyecto está diseñado para ejecutarse como CLI, ideal para:

- Tareas de mantenimiento
- Scripts de migración de datos
- Herramientas administrativas
- Reportes automatizados

## 📝 Notas

- La configuración actual incluye datos mock para testing sin conexiones reales
- Cada servicio implementa fallbacks en caso de errores de conexión
- El diseño permite agregar nuevas bases de datos sin cambios arquitecturales
- Los comandos incluyen validación de parámetros y mensajes de error claros
