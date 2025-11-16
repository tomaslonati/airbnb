"""
CLI simplificado solo para propiedades - workaround para issue de Typer/Click
"""

import typer
import asyncio
from typing import Optional
from datetime import date
from services.properties import PropertyService
from services.reservations import ReservationService

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
                typer.echo(
                    f"   Amenities: {', '.join([a['nombre'] for a in prop['amenities']])}")
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
                typer.echo(
                    f"  • {prop['nombre']} (ID: {prop['id']}, Cap: {prop['capacidad']})")
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


@app.command("block-dates")
def block_dates(
    propiedad_id: int = typer.Option(..., "--property-id",
                                     "-p", help="ID de la propiedad"),
    start_date: str = typer.Option(..., "--start",
                                   "-s", help="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end", "-e",
                                 help="Fecha fin (YYYY-MM-DD)"),
):
    """Bloquea fechas para que no estén disponibles para reservas."""

    async def _block():
        try:
            # Convertir fechas
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)

            if end <= start:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                raise typer.Exit(1)

            service = ReservationService()
            await service._mark_dates_unavailable(propiedad_id, start, end)

            num_days = (end - start).days
            typer.echo(
                f"✅ Bloqueadas {num_days} fechas para propiedad {propiedad_id} ({start} a {end})")

        except ValueError as e:
            typer.echo(f"❌ Formato de fecha inválido. Usar YYYY-MM-DD")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Error: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_block())


@app.command("unblock-dates")
def unblock_dates(
    propiedad_id: int = typer.Option(..., "--property-id",
                                     "-p", help="ID de la propiedad"),
    start_date: str = typer.Option(..., "--start",
                                   "-s", help="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end", "-e",
                                 help="Fecha fin (YYYY-MM-DD)"),
    price_per_night: Optional[float] = typer.Option(
        None, "--price", help="Precio por noche (opcional)"),
):
    """Desbloquea fechas para que estén disponibles para reservas."""

    async def _unblock():
        try:
            # Convertir fechas
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)

            if end <= start:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                raise typer.Exit(1)

            service = ReservationService()
            await service._mark_dates_available(propiedad_id, start, end, price_per_night)

            num_days = (end - start).days
            price_msg = f" a ${price_per_night}/noche" if price_per_night else ""
            typer.echo(
                f"✅ Desbloqueadas {num_days} fechas para propiedad {propiedad_id}{price_msg} ({start} a {end})")

        except ValueError as e:
            typer.echo(f"❌ Formato de fecha inválido. Usar YYYY-MM-DD")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Error: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_unblock())


@app.command("check-availability")
def check_availability(
    propiedad_id: int = typer.Option(..., "--property-id",
                                     "-p", help="ID de la propiedad"),
    start_date: str = typer.Option(..., "--start",
                                   "-s", help="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end", "-e",
                                 help="Fecha fin (YYYY-MM-DD)"),
):
    """Verifica si una propiedad está disponible en las fechas especificadas."""

    async def _check():
        try:
            # Convertir fechas
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)

            if end <= start:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                raise typer.Exit(1)

            service = ReservationService()
            is_available = await service._check_availability(propiedad_id, start, end)

            num_days = (end - start).days

            if is_available:
                typer.echo(
                    f"✅ Propiedad {propiedad_id} DISPONIBLE para {num_days} días ({start} a {end})")

                # Mostrar precio estimado
                total_price = await service._calculate_total_price(propiedad_id, start, end)
                typer.echo(f"💰 Precio estimado: ${total_price}")
            else:
                typer.echo(
                    f"❌ Propiedad {propiedad_id} NO DISPONIBLE para {num_days} días ({start} a {end})")

        except ValueError as e:
            typer.echo(f"❌ Formato de fecha inválido. Usar YYYY-MM-DD")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Error: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_check())


if __name__ == "__main__":
    app()
