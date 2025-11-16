#!/usr/bin/env python3
"""
Script para configurar disponibilidad de todas las propiedades
"""

import asyncio
from datetime import date, timedelta
from db.postgres import execute_command
from utils.logging import get_logger

logger = get_logger(__name__)


async def setup_property_availability():
    """Configura disponibilidad para todas las propiedades desde hoy hasta 31/12/2026"""

    try:
        logger.info("Configurando disponibilidad para todas las propiedades...")

        # SQL para generar disponibilidad
        sql = """
        INSERT INTO propiedad_disponibilidad (propiedad_id, dia, disponible, price_per_night, created_at, updated_at)
        SELECT 
            p.id as propiedad_id,
            generate_series('2025-11-16'::date, '2026-12-31'::date, '1 day'::interval)::date as dia,
            true as disponible,
            100.00 as price_per_night,
            NOW() as created_at,
            NOW() as updated_at
        FROM propiedad p
        ON CONFLICT (propiedad_id, dia) 
        DO UPDATE SET 
            disponible = EXCLUDED.disponible,
            price_per_night = COALESCE(propiedad_disponibilidad.price_per_night, EXCLUDED.price_per_night),
            updated_at = NOW();
        """

        await execute_command(sql)

        # Calcular estadísticas
        start_date = date(2025, 11, 16)
        end_date = date(2026, 12, 31)
        total_days = (end_date - start_date).days + 1

        logger.info(f"✅ Disponibilidad configurada exitosamente")
        logger.info(
            f"📅 Período: {start_date} a {end_date} ({total_days} días)")
        logger.info(f"💰 Precio base: $100.00 por noche")

        print("✅ Disponibilidad configurada para todas las propiedades")
        print(f"📅 Desde: {start_date}")
        print(f"📅 Hasta: {end_date}")
        print(f"📊 Total días: {total_days}")
        print(f"💰 Precio base: $100.00/noche")

    except Exception as e:
        logger.error(f"Error configurando disponibilidad: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_property_availability())
