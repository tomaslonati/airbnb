#!/usr/bin/env python
"""Test directo del PropertyService sin Typer CLI"""
import asyncio
from services.properties import PropertyService

async def main():
    service = PropertyService()
    
    result = await service.create_property(
        nombre="Depto Test CLI",
        descripcion="Propiedad de prueba desde script",
        capacidad=4,
        ciudad_id=1,
        anfitrion_id=1,
        tipo_propiedad_id=1,
        amenities=[1, 2],
        servicios=[1],
        reglas=[1],
        generar_calendario=True,
        dias_calendario=30
    )
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   ID: {result['property_id']}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
