# Estructura del Proyecto

Este documento describe la organización del proyecto después de la reorganización.

## Estructura de Directorios

```
airbnb/
├── cli/                          # Comandos CLI organizados por feature
│   ├── commands.py              # CLI principal (interactivo)
│   ├── auth/
│   │   └── commands.py          # Comandos de autenticación
│   └── properties/
│       └── commands.py          # Comandos de propiedades
│
├── tests/                        # Tests organizados por tipo
│   ├── connections/             # Tests de conexión a bases de datos
│   │   ├── postgres/
│   │   ├── mongo/
│   │   ├── neo4j/
│   │   ├── redis/
│   │   └── cassandra/
│   └── domain/                  # Tests de features/dominio
│       ├── auth-system/
│       └── properties/
│
├── docs/                        # Documentación organizada
│   ├── database/               # Docs de bases de datos
│   ├── auth-system/            # Docs de autenticación
│   ├── properties/              # Docs de propiedades
│   └── general/                # Docs generales
│
├── services/                    # Servicios de negocio
├── db/                          # Conexiones a bases de datos
├── migrations/                  # Migraciones de BD
└── main.py                      # Punto de entrada principal
```

## Uso del CLI

### Autenticación
```bash
# Usando el módulo integrado
python main.py auth register --email "user@example.com" --password "pass" --role "HUESPED" --name "John Doe"
python main.py auth login --email "user@example.com" --password "pass"
python main.py auth profile --email "user@example.com"
python main.py auth status
```

### Propiedades
```bash
# Usando el módulo integrado
python main.py properties create --nombre "Casa" --descripcion "Desc" --capacidad 4 --ciudad-id 1 --anfitrion-id 1
python main.py properties get --id 1
python main.py properties list --ciudad-id 1
python main.py properties update --id 1 --nombre "Nuevo nombre"
python main.py properties delete --id 1
```

### Modo Interactivo
```bash
# Ejecutar sin comandos para modo interactivo
python main.py
```

## Tests

### Tests de Conexión
Los tests de conexión están en `tests/connections/{db}/`:
- `tests/connections/postgres/test_postgres.py`
- `tests/connections/mongo/test_mongo.py`
- `tests/connections/neo4j/test_neo4j.py`
- `tests/connections/redis/test_redis.py`
- `tests/connections/cassandra/test_astradb.py`

### Tests de Features
Los tests de features están en `tests/domain/{feature}/`:
- `tests/domain/auth-system/` - Tests del sistema de autenticación
- `tests/domain/properties/` - Tests del sistema de propiedades

## Documentación

- `docs/database/` - Documentación de bases de datos
- `docs/auth-system/` - Documentación del sistema de autenticación
- `docs/properties/` - Documentación del sistema de propiedades
- `docs/general/` - Documentación general del proyecto

