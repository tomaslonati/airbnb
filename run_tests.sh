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
    python tests/test_postgres.py
    echo ""
}

# Función para ejecutar test de helpers de PostgreSQL
run_postgres_helpers_test() {
    echo -e "${GREEN}Ejecutando test de helpers de PostgreSQL...${NC}"
    python tests/test_postgres_helpers.py
    echo ""
}

# Función para ejecutar test de Redis
run_redis_test() {
    echo -e "${GREEN}Ejecutando test de Redis...${NC}"
    python tests/test_redis.py
    echo ""
}

# Función para ejecutar test de MongoDB
run_mongo_test() {
    echo -e "${GREEN}Ejecutando test de MongoDB...${NC}"
    python tests/test_mongo.py
    echo ""
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
    all)
        run_postgres_test
        run_postgres_helpers_test
        run_redis_test
        run_mongo_test
        ;;
    *)
        echo "Uso: $0 [postgres|postgres-helpers|redis|mongo|all]"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Tests completados${NC}"

