"""
CLI simplificado solo para propiedades - workaround para issue de Typer/Click
"""

import typer
import asyncio
from typing import Optional
from services.properties import PropertyService

app = typer.Typer(help="Gestión de propiedades")

@app.command("create")
def create_property(
    nombre: Optional[str] = typer.Option(None, "--nombre", "-n"),
    descripcion: Optional[str] = typer.Option(None, "--descripcion", "-d"),
    capacidad: Optional[int] = typer.Option(None, "--capacidad", "-c"),
    ciudad_id: int = typer.Option(..., "--ciudad-id"),
    anfitrion_id: int = typer.Option(..., "--anfitrion-id"),
    tipo_propiedad_id: int = typer.Option(1, "--tipo-id"),
    amenities: Optional[str] = typer.Option(None, "--amenities"),
    servicios: Optional[str] = typer.Option(None, "--servicios"),
    reglas: Optional[str] = typer.Option(None, "--reglas"),
):
    """Crea una nueva propiedad. Ej: create --nombre "Depto" --descripcion "desc" --capacidad 3 --ciudad-id 1 --anfitrion-id 1"""
    if not nombre or not descripcion or capacidad is None:
        typer.echo("❌ Requiere: --nombre, --descripcion, --capacidad")
        raise typer.Exit(1)
    
    async def _create():
        service = PropertyService()
        
        amenity_ids = None
        if amenities:
            try:
                amenity_ids = [int(x.strip()) for x in amenities.split(",")]
            except ValueError:
                typer.echo("❌ Amenities: 1,2,3")
                raise typer.Exit(1)
        
        servicio_ids = None
        if servicios:
            try:
                servicio_ids = [int(x.strip()) for x in servicios.split(",")]
            except ValueError:
                typer.echo("❌ Servicios: 1,2")
                raise typer.Exit(1)
        
        regla_ids = None
        if reglas:
            try:
                regla_ids = [int(x.strip()) for x in reglas.split(",")]
            except ValueError:
                typer.echo("❌ Reglas: 1,2")
                raise typer.Exit(1)
        
        result = await service.create_property(
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            ciudad_id=ciudad_id,
            anfitrion_id=anfitrion_id,
            tipo_propiedad_id=tipo_propiedad_id,
            amenities=amenity_ids,
            servicios=servicio_ids,
            reglas=regla_ids,
            generar_calendario=True,
            dias_calendario=365
        )
        
        if result["success"]:
            typer.echo(f"✅ {result['message']}")
            typer.echo(f"   ID: {result['property_id']}")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_create())


@app.command("get")
def get_property(propiedad_id: Optional[int] = typer.Option(None, "--id")):
    """Obtiene detalles de una propiedad."""
    if propiedad_id is None:
        typer.echo("❌ Requiere: --id <numero>")
        raise typer.Exit(1)
    
    async def _get():
        service = PropertyService()
        result = await service.get_property(propiedad_id)
        
        if result["success"]:
            prop = result["property"]
            typer.echo(f"🏠 {prop['nombre']}")
            typer.echo(f"   ID: {prop['id']}")
            typer.echo(f"   Capacidad: {prop['capacidad']} personas")
            typer.echo(f"   Ciudad: {prop.get('ciudad', 'N/A')}")
            if prop.get('amenities'):
                typer.echo(f"   Amenities: {', '.join([a['nombre'] for a in prop['amenities']])}")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_get())


@app.command("list")
def list_properties(
    ciudad_id: Optional[int] = typer.Option(None, "--ciudad-id"),
    anfitrion_id: Optional[int] = typer.Option(None, "--anfitrion-id"),
):
    """Lista propiedades."""
    async def _list():
        service = PropertyService()
        
        if ciudad_id:
            result = await service.list_properties_by_city(ciudad_id)
        elif anfitrion_id:
            result = await service.list_properties_by_host(anfitrion_id)
        else:
            typer.echo("Usa --ciudad-id o --anfitrion-id")
            raise typer.Exit(1)
        
        if result["success"]:
            typer.echo(f"Total: {result['total']}")
            for prop in result["properties"]:
                typer.echo(f"  • {prop['nombre']} (ID: {prop['id']}, Cap: {prop['capacidad']})")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_list())


@app.command("update")
def update_property(
    propiedad_id: Optional[int] = typer.Option(None, "--id"),
    nombre: Optional[str] = typer.Option(None, "--nombre"),
    capacidad: Optional[int] = typer.Option(None, "--capacidad"),
):
    """Actualiza una propiedad."""
    if propiedad_id is None:
        typer.echo("❌ Requiere: --id <numero>")
        raise typer.Exit(1)
    
    async def _update():
        service = PropertyService()
        result = await service.update_property(propiedad_id, nombre=nombre, capacidad=capacidad)
        
        if result["success"]:
            typer.echo(f"✅ Actualizado: {result['property']['nombre']}")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_update())


@app.command("delete")
def delete_property(
    propiedad_id: Optional[int] = typer.Option(None, "--id"),
    confirm: bool = typer.Option(False, "--confirm"),
):
    """Elimina una propiedad."""
    if propiedad_id is None:
        typer.echo("❌ Requiere: --id <numero>")
        raise typer.Exit(1)
    
    async def _delete():
        if not confirm and not typer.confirm(f"¿Eliminar propiedad {propiedad_id}?"):
            typer.echo("Cancelado")
            raise typer.Exit(0)
        
        service = PropertyService()
        result = await service.delete_property(propiedad_id)
        
        if result["success"]:
            typer.echo(f"✅ {result['message']}")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_delete())


if __name__ == "__main__":
    app()
