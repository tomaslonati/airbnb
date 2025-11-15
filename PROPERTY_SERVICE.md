# Property Service - Documentación

## Descripción General

El `PropertyService` es un servicio production-ready para gestionar propiedades en el sistema Airbnb. Implementa operaciones CRUD completas con transacciones ACID, validación de datos y autenticación integrada.

## Características Principales

✅ **Transacciones Atómicas (ACID)**
- Todas las operaciones se ejecutan dentro de transacciones PostgreSQL
- Si falla cualquier parte, todo se revierte automáticamente
- Garantiza consistencia de datos

✅ **Validación de Foreign Keys**
- Valida ciudad_id, anfitrion_id, tipo_propiedad_id antes de crear
- Valida IDs de amenities, servicios y reglas
- Errores claros y descriptivos

✅ **Autenticación Integrada**
- Soporta auth_user_id de Supabase
- Resuelve automáticamente anfitrion_id desde el auth_user_id
- Fallback a anfitrion_id directo si es proporcionado

✅ **Generación Automática de Calendario**
- Crea 365 registros de disponibilidad en la tabla `fecha`
- Configurable: número de días customizable
- Tarifa por defecto: $100/día

## API - Métodos Disponibles

### 1. Crear Propiedad

```python
result = await service.create_property(
    nombre="Depto Palermo",
    descripcion="Hermoso departamento en el corazón de Palermo",
    capacidad=4,
    ciudad_id=1,
    anfitrion_id=1,                    # O usar auth_user_id
    tipo_propiedad_id=1,
    amenities=[1, 2],                  # IDs de amenities
    servicios=[1, 2],                  # IDs de servicios
    reglas=[1],                        # IDs de reglas
    generar_calendario=True,
    dias_calendario=365
)

# Respuesta exitosa:
{
    "success": True,
    "message": "Propiedad 'Depto Palermo' creada exitosamente",
    "property_id": 5,
    "property": {
        "id": 5,
        "nombre": "Depto Palermo",
        "descripcion": "...",
        "capacidad": 4
    }
}

# Respuesta con error:
{
    "success": False,
    "error": "Ciudad con ID 99999 no existe"
}
```

### 2. Obtener Detalles de Propiedad

```python
result = await service.get_property(propiedad_id=5)

# Respuesta:
{
    "success": True,
    "property": {
        "id": 5,
        "nombre": "Depto Palermo",
        "descripcion": "...",
        "capacidad": 4,
        "ciudad": "Buenos Aires",
        "tipo_propiedad": "Departamento",
        "amenities": [
            {"id": 1, "nombre": "Pileta"},
            {"id": 2, "nombre": "Terraza"}
        ],
        "servicios": [
            {"id": 1, "nombre": "Wifi"}
        ],
        "reglas": [
            {"id": 1, "nombre": "No fumar"}
        ]
    }
}
```

### 3. Listar Propiedades por Ciudad

```python
result = await service.list_properties_by_city(ciudad_id=1)

# Respuesta:
{
    "success": True,
    "total": 3,
    "properties": [
        {
            "id": 1,
            "nombre": "Depto Palermo",
            "capacidad": 3,
            "ciudad": "Buenos Aires",
            "tipo_propiedad": "Departamento"
        },
        ...
    ]
}
```

### 4. Listar Propiedades por Anfitrión

```python
result = await service.list_properties_by_host(anfitrion_id=1)

# Respuesta: mismo formato que list_properties_by_city()
```

### 5. Actualizar Propiedad

```python
result = await service.update_property(
    property_id=5,
    nombre="Depto Palermo Premium",
    capacidad=6,
    descripcion="Actualizado con nueva descripción"
    # tipo_propiedad_id, imagenes también soportados
)

# Respuesta:
{
    "success": True,
    "message": "Propiedad actualizada",
    "property": {
        "id": 5,
        "nombre": "Depto Palermo Premium",
        "capacidad": 6,
        "tipo_propiedad_id": 1
    }
}
```

### 6. Eliminar Propiedad

```python
result = await service.delete_property(property_id=5)

# Respuesta:
{
    "success": True,
    "message": "Propiedad 5 eliminada con todas sus relaciones"
}

# Elimina automáticamente:
# - Amenities de la propiedad
# - Servicios de la propiedad
# - Reglas de la propiedad
# - Disponibilidad (fecha)
# - Reservas de la propiedad
# - La propiedad misma
```

## Comandos CLI

### Crear Propiedad

```bash
python main.py create-property \
  "Depto Palermo" \
  "Hermoso departamento en Palermo" \
  4 \
  --ciudad-id 1 \
  --anfitrion-id 1 \
  --tipo-id 1 \
  --amenities "1,2" \
  --servicios "1,2" \
  --reglas "1"
```

### Obtener Detalles

```bash
python main.py get-property 5
```

### Listar Propiedades

```bash
python main.py list-properties --ciudad-id 1
# O
python main.py list-properties --anfitrion-id 1
```

### Actualizar Propiedad

```bash
python main.py update-property 5 \
  --nombre "Depto Actualizado" \
  --capacidad 6
```

### Eliminar Propiedad

```bash
python main.py delete-property 5
# Pide confirmación. Para saltarla:
python main.py delete-property 5 --confirm
```

## Validaciones Implementadas

| Campo | Validación | Error |
|-------|-----------|-------|
| ciudad_id | Existe en tabla `ciudad` | "Ciudad con ID X no existe" |
| anfitrion_id | Existe en tabla `anfitrion` | "Anfitrión con ID X no existe" |
| tipo_propiedad_id | Existe en tabla `tipo_propiedad` | "Tipo propiedad con ID X no existe" |
| amenity_ids | Existen en tabla `amenity` | "Amenity con ID X no existe" |
| servicio_ids | Existen en tabla `servicio` | "Servicio con ID X no existe" |
| regla_ids | Existen en tabla `regla` | "Regla con ID X no existe" |
| auth_user_id → anfitrion_id | Resuelve de tabla `anfitrion` | "Usuario no está registrado como anfitrión" |

## Estructura de Transacciones

Ejemplo: `create_property()` con transacción ACID

```
BEGIN TRANSACTION
  ├─ Validar todos los IDs externos
  ├─ INSERT INTO propiedad (...)
  ├─ INSERT INTO propiedad_amenity (...) x N
  ├─ INSERT INTO propiedad_servicio (...) x N
  ├─ INSERT INTO propiedad_regla (...) x N
  └─ INSERT INTO fecha (...) x 365 días
END TRANSACTION

Si cualquier INSERT falla → ROLLBACK automático
Si todo OK → COMMIT automático
```

## Manejo de Errores

Todos los métodos devuelven un dict con estructura:

**Caso Éxito:**
```python
{
    "success": True,
    "message": "...",
    "property_id": 5,  # en create
    "property": {...}   # detalles
}
```

**Caso Error:**
```python
{
    "success": False,
    "error": "Descripción del error"
}
```

Los errores se loguean automáticamente en structlog con contexto completo.

## Pruebas

Ejecutar suite completa:
```bash
python test_properties.py
```

Tests incluidos (8/8):
1. ✅ Crear propiedad con amenities/servicios/reglas
2. ✅ Obtener detalles con relaciones
3. ✅ Listar propiedades por ciudad
4. ✅ Listar propiedades por anfitrión
5. ✅ Validar ciudad inválida
6. ✅ Validar amenity inválido
7. ✅ Actualizar propiedad
8. ✅ Eliminar propiedad (transacción)

## Logging

El servicio usa `structlog` para logging estructurado:

```json
{"event": "Validando datos para propiedad: Depto", "logger": "services.properties", "level": "info"}
{"event": "Propiedad creada con ID: 5", "logger": "services.properties", "level": "info"}
{"event": "Agregados 2 amenities a propiedad 5", "logger": "services.properties", "level": "info"}
```

## Rendimiento

- **Transacciones**: Uso de asyncpg con connection pooling (sin cache de statements para PgBouncer)
- **Validaciones**: Queries paralelas en BD (una por cada FK)
- **Calendario**: 365 inserts en 2-3 segundos (mediante ON CONFLICT)

## Seguridad

✅ **SQL Injection Prevention**: Parámetros posicionales ($1, $2, ...)
✅ **Auth Integration**: Suporte para Supabase auth_user_id
✅ **Transacción Rollback**: Error en cualquier paso revierte todo
✅ **Logging Completo**: Todos los errores y operaciones registradas

## Próximas Mejoras

- [ ] Soporte para imagenes (relacionar tabla propiedad_imagen)
- [ ] Búsqueda full-text en descripción
- [ ] Cache Redis para propiedades frecuentes
- [ ] Webhooks para eventos de propiedad
- [ ] Bulk operations (crear múltiples propiedades)

## Contacto

Desarrollo: PropertyService v1.0
Framework: Python 3.11 + asyncio + asyncpg
