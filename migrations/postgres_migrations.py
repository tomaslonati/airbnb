"""
Migraciones para PostgreSQL/Supabase.
"""

from migrations.base import BaseMigration
from db import postgres
from utils.logging import get_logger

logger = get_logger(__name__)


class Migration001CreateUsers(BaseMigration):
    """Crea tabla de usuarios."""

    def __init__(self):
        super().__init__("001", "Crear tabla users")

    async def up(self):
        """Crear tabla users."""
        query = """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                profile_picture_url TEXT,
                is_host BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """

        await postgres.execute_command(query)
        logger.info("Tabla users creada")

    async def down(self):
        """Eliminar tabla users."""
        await postgres.execute_command("DROP TABLE IF EXISTS users;")
        logger.info("Tabla users eliminada")


class Migration002CreateProperties(BaseMigration):
    """Crea tabla de propiedades."""

    def __init__(self):
        super().__init__("002", "Crear tabla properties")

    async def up(self):
        """Crear tabla properties."""
        query = """
            CREATE TABLE IF NOT EXISTS properties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                city VARCHAR(100) NOT NULL,
                country VARCHAR(100) NOT NULL,
                address TEXT NOT NULL,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                price DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'USD',
                max_guests INTEGER NOT NULL,
                bedrooms INTEGER DEFAULT 1,
                bathrooms INTEGER DEFAULT 1,
                rating DECIMAL(3, 2) DEFAULT NULL,
                total_reviews INTEGER DEFAULT 0,
                availability BOOLEAN DEFAULT TRUE,
                host_id UUID NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """

        await postgres.execute_command(query)

        # Crear índices
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);",
            "CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price);",
            "CREATE INDEX IF NOT EXISTS idx_properties_rating ON properties(rating);",
            "CREATE INDEX IF NOT EXISTS idx_properties_host ON properties(host_id);",
            "CREATE INDEX IF NOT EXISTS idx_properties_availability ON properties(availability);"
        ]

        for index_query in indices:
            await postgres.execute_command(index_query)

        logger.info("Tabla properties e índices creados")

    async def down(self):
        """Eliminar tabla properties."""
        await postgres.execute_command("DROP TABLE IF EXISTS properties;")
        logger.info("Tabla properties eliminada")


class Migration003CreateReservations(BaseMigration):
    """Crea tabla de reservas."""

    def __init__(self):
        super().__init__("003", "Crear tabla reservations")

    async def up(self):
        """Crear tabla reservations."""
        query = """
            CREATE TABLE IF NOT EXISTS reservations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL,
                user_id UUID NOT NULL,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                guests INTEGER NOT NULL DEFAULT 1,
                total_price DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'CONFIRMED' CHECK (status IN ('PENDING', 'CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED')),
                special_requests TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT check_dates CHECK (check_out > check_in)
            );
        """

        await postgres.execute_command(query)

        # Crear índices
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_reservations_property ON reservations(property_id);",
            "CREATE INDEX IF NOT EXISTS idx_reservations_user ON reservations(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_reservations_dates ON reservations(check_in, check_out);",
            "CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);",
            "CREATE INDEX IF NOT EXISTS idx_reservations_created ON reservations(created_at);"
        ]

        for index_query in indices:
            await postgres.execute_command(index_query)

        logger.info("Tabla reservations e índices creados")

    async def down(self):
        """Eliminar tabla reservations."""
        await postgres.execute_command("DROP TABLE IF EXISTS reservations;")
        logger.info("Tabla reservations eliminada")


class Migration004CreateReviews(BaseMigration):
    """Crea tabla de reseñas."""

    def __init__(self):
        super().__init__("004", "Crear tabla reviews")

    async def up(self):
        """Crear tabla reviews."""
        query = """
            CREATE TABLE IF NOT EXISTS reviews (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                reservation_id UUID NOT NULL,
                reviewer_id UUID NOT NULL,
                property_id UUID NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
                location_rating INTEGER CHECK (location_rating >= 1 AND location_rating <= 5),
                value_rating INTEGER CHECK (value_rating >= 1 AND value_rating <= 5),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                UNIQUE(reservation_id, reviewer_id)
            );
        """

        await postgres.execute_command(query)

        # Crear índices
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_reviews_property ON reviews(property_id);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);"
        ]

        for index_query in indices:
            await postgres.execute_command(index_query)

        logger.info("Tabla reviews e índices creados")

    async def down(self):
        """Eliminar tabla reviews."""
        await postgres.execute_command("DROP TABLE IF EXISTS reviews;")
        logger.info("Tabla reviews eliminada")
