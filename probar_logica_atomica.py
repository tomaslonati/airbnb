"""
Script para probar la nueva lógica de UPDATE atómico en ocupacion_por_ciudad.
Crea una propiedad simple con pocos días para verificar el comportamiento.
"""

import asyncio
from datetime import datetime, date, timedelta
from services.properties import PropertyService
from db.cassandra import find_documents
from utils.logging import get_logger

logger = get_logger(__name__)


async def probar_nueva_logica():
    """Prueba la nueva lógica de UPDATE atómico."""
    try:
        logger.info("🚀 Probando nueva lógica de UPDATE atómico...")

        # Crear servicio de propiedades
        property_service = PropertyService()

        # Datos de propiedad de prueba
        propiedad_data = {
            'name': 'Test Atomico',
            'description': 'Propiedad de prueba para UPDATE atomico',
            'capacity': 2,
            'location_id': 1,  # Buenos Aires
            'property_type_id': 1,  # Departamento
            'amenities': [1],  # Pileta
            'services': [1],   # Wifi
            'rules': [1]       # No fumar
        }

        # Fechas de prueba (solo 7 días)
        today = date.today()
        availability_dates = [today + timedelta(days=i) for i in range(7)]

        logger.info(
            f"📅 Creando propiedad con {len(availability_dates)} días...")

        # Crear propiedad
        result = await property_service.create_property(
            anfitrion_id=6,  # tomaslonati@gmail.com
            nombre=propiedad_data['name'],
            descripcion=propiedad_data['description'],
            capacidad=propiedad_data['capacity'],
            ciudad_id=propiedad_data['location_id'],
            tipo_propiedad_id=propiedad_data['property_type_id'],
            amenities=propiedad_data['amenities'],
            servicios=propiedad_data['services'],
            reglas=propiedad_data['rules'],
            generar_calendario=True,  # Generar calendario automático
            dias_calendario=7
        )

        if result['success']:
            property_id = result['property_id']
            logger.info(f"✅ Propiedad {property_id} creada exitosamente")

            # Esperar un momento para que se procese
            await asyncio.sleep(2)

            # Consultar ocupacion_por_ciudad para ver los UPDATEs atómicos
            logger.info("🔍 Verificando tabla ocupacion_por_ciudad...")

            docs = await find_documents(
                'ocupacion_por_ciudad',
                {'ciudad_id': 1},
                limit=10
            )

            logger.info(f"📊 Documentos encontrados: {len(docs)}")

            for doc in docs[:5]:
                fecha = doc.get('fecha')
                ocupadas = doc.get('noches_ocupadas', 0)
                disponibles = doc.get('noches_disponibles', 0)
                logger.info(
                    f"  📅 {fecha}: {ocupadas} ocupadas, {disponibles} disponibles")

        else:
            logger.error(f"❌ Error creando propiedad: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error en prueba: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(probar_nueva_logica())
