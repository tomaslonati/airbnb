#!/bin/bash

# Script para ejecutar tests de bases de datos
# Uso: ./run_tests.sh [postgres|redis|all]

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activar entorno virtual
source venv/bin/activate

# Establecer PYTHONPATH
export PYTHONPATH=/Users/tadeomaddonni/Developer/UADE/ingenieria-datos-2/airbnb

echo -e "${BLUE}=== Test Runner para Airbnb Backend ===${NC}\n"

# Función para ejecutar test de PostgreSQL
run_postgres_test() {
    echo -e "${GREEN}Ejecutando test de PostgreSQL/Supabase...${NC}"
    python tests/connections/postgres/test_postgres.py
    echo ""
}

# Función para ejecutar test de helpers de PostgreSQL
run_postgres_helpers_test() {
    echo -e "${GREEN}Ejecutando test de helpers de PostgreSQL...${NC}"
    python tests/connections/postgres/test_postgres_helpers.py
    echo ""
}

# Función para ejecutar test de Redis
run_redis_test() {
    echo -e "${GREEN}Ejecutando test de Redis...${NC}"
    python tests/connections/redis/test_redis.py
    echo ""
}

# Función para ejecutar test de MongoDB
run_mongo_test() {
    echo -e "${GREEN}Ejecutando test de MongoDB...${NC}"
    python tests/connections/mongo/test_mongo.py
    echo ""
}

# Función para ejecutar test de Neo4j
run_neo4j_test() {
    echo -e "${GREEN}Ejecutando test de Neo4j...${NC}"
    python tests/connections/neo4j/test_neo4j.py
    echo ""
}

# Función para ejecutar test de Cassandra/AstraDB
run_cassandra_test() {
    echo -e "${GREEN}Ejecutando test de Cassandra/AstraDB...${NC}"
    python tests/connections/cassandra/test_astradb.py
    echo ""
}

# Función para ejecutar tests de dominio de auth
run_auth_tests() {
    echo -e "${GREEN}Ejecutando tests de autenticación...${NC}"
    python tests/domain/auth-system/test_cli.py
    echo ""
}

# Función para ejecutar tests de dominio de properties
run_properties_tests() {
    echo -e "${GREEN}Ejecutando tests de propiedades...${NC}"
    python tests/domain/properties/test_properties.py
    echo ""
}

# Función para ejecutar todos los tests de conexiones
run_all_connections() {
    echo -e "${BLUE}>>> Tests de Conexiones${NC}\n"
    run_postgres_test
    run_postgres_helpers_test
    run_redis_test
    run_mongo_test
    run_neo4j_test
    run_cassandra_test
}

# Función para ejecutar todos los tests de dominio
run_all_domain() {
    echo -e "${BLUE}>>> Tests de Dominio${NC}\n"
    run_auth_tests
    run_properties_tests
}

# Determinar qué tests ejecutar
case "${1:-all}" in
    postgres)
        run_postgres_test
        ;;
    postgres-helpers)
        run_postgres_helpers_test
        ;;
    redis)
        run_redis_test
        ;;
    mongo)
        run_mongo_test
        ;;
    neo4j)
        run_neo4j_test
        ;;
    cassandra)
        run_cassandra_test
        ;;
    auth)
        run_auth_tests
        ;;
    properties)
        run_properties_tests
        ;;
    connections)
        run_all_connections
        ;;
    domain)
        run_all_domain
        ;;
    all)
        run_all_connections
        run_all_domain
        ;;
    *)
        echo "Uso: $0 [postgres|postgres-helpers|redis|mongo|neo4j|cassandra|auth|properties|connections|domain|all]"
        echo ""
        echo "Opciones:"
        echo "  postgres          - Test de PostgreSQL/Supabase"
        echo "  postgres-helpers  - Test de helpers de PostgreSQL"
        echo "  redis             - Test de Redis"
        echo "  mongo             - Test de MongoDB"
        echo "  neo4j             - Test de Neo4j"
        echo "  cassandra         - Test de Cassandra/AstraDB"
        echo "  auth              - Tests de autenticación"
        echo "  properties        - Tests de propiedades"
        echo "  connections       - Todos los tests de conexiones"
        echo "  domain            - Todos los tests de dominio"
        echo "  all               - Todos los tests (default)"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Tests completados${NC}"

