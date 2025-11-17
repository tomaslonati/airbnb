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


@app.command("availability")
def manage_availability(
    propiedad_id: Optional[int] = typer.Option(None, "--id"),
    fecha_inicio: Optional[str] = typer.Option(None, "--fecha-inicio", help="YYYY-MM-DD"),
    fecha_fin: Optional[str] = typer.Option(None, "--fecha-fin", help="YYYY-MM-DD"),
    disponible: Optional[bool] = typer.Option(None, "--disponible", help="true/false"),
    precio: Optional[float] = typer.Option(None, "--precio"),
    accion: Optional[str] = typer.Option(None, "--accion", help="bloquear|liberar|consultar|generar"),
):
    """
    Gestiona la disponibilidad de una propiedad.
    
    Ejemplos:
    - Consultar: availability --id 1 --accion consultar
    - Bloquear fechas: availability --id 1 --fecha-inicio 2024-12-01 --fecha-fin 2024-12-05 --accion bloquear
    - Liberar fechas: availability --id 1 --fecha-inicio 2024-12-01 --fecha-fin 2024-12-05 --accion liberar --precio 150.0
    - Generar calendario: availability --id 1 --accion generar
    """
    if propiedad_id is None:
        typer.echo("❌ Requiere: --id <numero>")
        raise typer.Exit(1)
    
    if accion is None:
        typer.echo("❌ Requiere: --accion (bloquear|liberar|consultar|generar)")
        raise typer.Exit(1)
    
    async def _manage_availability():
        from services.reservations import ReservationService
        from services.properties import PropertyService
        from datetime import datetime, date
        from decimal import Decimal
        
        if accion == "consultar":
            # Mostrar disponibilidad actual
            typer.echo(f"\n📅 DISPONIBILIDAD DE PROPIEDAD {propiedad_id}")
            typer.echo("=" * 50)
            
            # Aquí podrías agregar consultas a la BD para mostrar disponibilidad
            property_service = PropertyService()
            prop_info = await property_service.get_property(propiedad_id)
            
            if prop_info["success"]:
                prop = prop_info.get("property", {})
                typer.echo(f"🏠 Propiedad: {prop.get('nombre', 'N/A')}")
                typer.echo(f"🏙️  Ciudad: {prop.get('ciudad', 'N/A')}")
                typer.echo(f"👥 Capacidad: {prop.get('capacidad_personas', 'N/A')}")
                typer.echo("\n💡 Use --fecha-inicio y --fecha-fin para consultar fechas específicas")
            else:
                typer.echo(f"❌ {prop_info.get('error', 'Propiedad no encontrada')}")
                return
        
        elif accion == "generar":
            # Generar calendario base
            typer.echo(f"\n🗓️  Generando calendario base para propiedad {propiedad_id}...")
            
            property_service = PropertyService()
            # Simulamos la generación usando el método interno
            try:
                from db.postgres import get_client as get_postgres_client
                pool = await get_postgres_client()
                async with pool.acquire() as conn:
                    await property_service._generate_availability(conn, propiedad_id, 365)
                typer.echo("✅ Calendario generado para 365 días")
            except Exception as e:
                typer.echo(f"❌ Error generando calendario: {e}")
        
        elif accion in ["bloquear", "liberar"]:
            # Validar fechas
            if not fecha_inicio or not fecha_fin:
                typer.echo("❌ Requiere: --fecha-inicio YYYY-MM-DD --fecha-fin YYYY-MM-DD")
                return
            
            try:
                start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                
                if start_date >= end_date:
                    typer.echo("❌ La fecha de inicio debe ser anterior a la fecha fin")
                    return
                
            except ValueError:
                typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
                return
            
            reservation_service = ReservationService()
            
            if accion == "bloquear":
                typer.echo(f"\n🔒 Bloqueando fechas {start_date} → {end_date} para propiedad {propiedad_id}")
                await reservation_service._mark_dates_unavailable(
                    propiedad_id, start_date, end_date, "Bloqueo manual desde CLI"
                )
                typer.echo("✅ Fechas bloqueadas exitosamente")
                
            elif accion == "liberar":
                price_decimal = Decimal(str(precio)) if precio else Decimal('100.0')
                typer.echo(f"\n🔓 Liberando fechas {start_date} → {end_date} para propiedad {propiedad_id}")
                typer.echo(f"💰 Precio por noche: ${price_decimal}")
                
                await reservation_service._mark_dates_available(
                    propiedad_id, start_date, end_date, price_decimal
                )
                typer.echo("✅ Fechas liberadas exitosamente")
        
        else:
            typer.echo("❌ Acción no válida. Use: bloquear|liberar|consultar|generar")
    
    asyncio.run(_manage_availability())


@app.command("calendar")
def show_calendar(
    propiedad_id: Optional[int] = typer.Option(None, "--id"),
    mes: Optional[int] = typer.Option(None, "--mes", help="1-12"),
    año: Optional[int] = typer.Option(None, "--año", help="YYYY"),
):
    """
    Muestra el calendario de disponibilidad de una propiedad.
    
    Ejemplo: calendar --id 1 --mes 12 --año 2024
    """
    if propiedad_id is None:
        typer.echo("❌ Requiere: --id <numero>")
        raise typer.Exit(1)
    
    async def _show_calendar():
        from datetime import datetime, date, timedelta
        import calendar
        
        # Usar mes y año actuales si no se especifican
        now = datetime.now()
        target_month = mes if mes else now.month
        target_year = año if año else now.year
        
        typer.echo(f"\n📅 CALENDARIO DE DISPONIBILIDAD - PROPIEDAD {propiedad_id}")
        typer.echo(f"🗓️  {calendar.month_name[target_month]} {target_year}")
        typer.echo("=" * 60)
        
        # Aquí podrías consultar la base de datos para obtener disponibilidad real
        # Por ahora, mostraremos un calendario básico
        
        cal = calendar.monthcalendar(target_year, target_month)
        typer.echo("L  M  M  J  V  S  D")
        typer.echo("-" * 20)
        
        for week in cal:
            week_str = ""
            for day in week:
                if day == 0:
                    week_str += "   "
                else:
                    # Aquí podrías verificar disponibilidad real desde la BD
                    # Por ahora, marcamos algunos días como ejemplo
                    if day % 3 == 0:  # Ejemplo: cada 3er día ocupado
                        week_str += f"{day:2}❌"
                    else:
                        week_str += f"{day:2}✅"
            typer.echo(week_str)
        
        typer.echo("\n🟢 ✅ = Disponible  🔴 ❌ = Ocupado")
        typer.echo("💡 Use 'availability' para gestionar disponibilidad")
    
    asyncio.run(_show_calendar())


@app.command("buscar-disponibles")
def buscar_propiedades_disponibles(
    fecha: str = typer.Option(..., "--fecha", help="Fecha a consultar (YYYY-MM-DD)"),
    ciudad_id: int = typer.Option(None, "--ciudad-id", help="ID de la ciudad (opcional)")
):
    """CU 4: Busca propiedades disponibles en una fecha específica."""
    async def _buscar_disponibles():
        try:
            from datetime import datetime
            from services.reservations import ReservationService
            
            # Validar fecha
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                typer.echo("❌ Formato de fecha inválido. Usa YYYY-MM-DD")
                raise typer.Exit(1)
            
            typer.echo(f"\n🔍 BUSCANDO PROPIEDADES DISPONIBLES")
            typer.echo("="*50)
            typer.echo(f"📅 Fecha: {fecha}")
            if ciudad_id:
                typer.echo(f"🏙️  Ciudad ID: {ciudad_id}")
            else:
                typer.echo("🌍 Todas las ciudades")
            
            reservation_service = ReservationService()
            result = await reservation_service.get_propiedades_disponibles_fecha(fecha_obj, ciudad_id)
            
            if result["success"]:
                propiedades = result["propiedades"]
                typer.echo(f"\n✅ Encontradas {result['total']} propiedades disponibles:")
                
                if propiedades:
                    typer.echo("\n" + "="*80)
                    for prop in propiedades:
                        typer.echo(f"🏠 ID: {prop.get('propiedad_id')}")
                        typer.echo(f"   📝 Nombre: {prop.get('nombre', 'Sin nombre')}")
                        typer.echo(f"   💰 Precio: ${prop.get('precio_noche', 0)}/noche")
                        typer.echo(f"   👥 Capacidad: {prop.get('capacidad', 1)} persona(s)")
                        typer.echo(f"   🏡 Tipo: {prop.get('tipo_propiedad', 'No especificado')}")
                        typer.echo(f"   🏙️  Ciudad ID: {prop.get('ciudad_id')}")
                        typer.echo("-" * 60)
                else:
                    typer.echo("😞 No hay propiedades disponibles para esta fecha.")
            else:
                typer.echo(f"❌ Error: {result['error']}")
                raise typer.Exit(1)
                
        except Exception as e:
            typer.echo(f"❌ Error buscando propiedades: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_buscar_disponibles())


@app.command("reservas-host")
def consultar_reservas_host(
    host_id: int = typer.Option(..., "--host-id", help="ID del host"),
    fecha_inicio: str = typer.Option(None, "--fecha-inicio", help="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: str = typer.Option(None, "--fecha-fin", help="Fecha fin (YYYY-MM-DD)")
):
    """CU 6: Consulta reservas de un host por rango de fechas."""
    async def _consultar_reservas_host():
        try:
            from datetime import datetime
            from services.reservations import ReservationService
            
            fecha_inicio_obj = None
            fecha_fin_obj = None
            
            # Validar fechas si se proporcionan
            if fecha_inicio:
                try:
                    fecha_inicio_obj = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Formato de fecha inicio inválido. Usa YYYY-MM-DD")
                    raise typer.Exit(1)
                    
            if fecha_fin:
                try:
                    fecha_fin_obj = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Formato de fecha fin inválido. Usa YYYY-MM-DD")
                    raise typer.Exit(1)
            
            typer.echo(f"\n📋 RESERVAS DEL HOST")
            typer.echo("="*40)
            typer.echo(f"👤 Host ID: {host_id}")
            if fecha_inicio_obj:
                typer.echo(f"📅 Desde: {fecha_inicio}")
            if fecha_fin_obj:
                typer.echo(f"📅 Hasta: {fecha_fin}")
            
            reservation_service = ReservationService()
            result = await reservation_service.get_reservas_host(host_id, fecha_inicio_obj, fecha_fin_obj)
            
            if result["success"]:
                reservas = result["reservas"]
                typer.echo(f"\n✅ Encontradas {result['total']} reservas:")
                
                if reservas:
                    typer.echo("\n" + "="*80)
                    for reserva in reservas:
                        typer.echo(f"🆔 Reserva ID: {reserva.get('reserva_id')}")
                        typer.echo(f"   🏠 Propiedad ID: {reserva.get('propiedad_id')}")
                        typer.echo(f"   👤 Huésped ID: {reserva.get('huesped_id')}")
                        typer.echo(f"   📅 Check-in: {reserva.get('fecha_inicio')}")
                        typer.echo(f"   📅 Check-out: {reserva.get('fecha_fin')}")
                        typer.echo(f"   💰 Total: ${reserva.get('precio_total', 0)}")
                        typer.echo(f"   📊 Estado: {reserva.get('estado', 'confirmada')}")
                        typer.echo("-" * 60)
                else:
                    typer.echo("😞 No hay reservas para este host en el período especificado.")
            else:
                typer.echo(f"❌ Error: {result['error']}")
                raise typer.Exit(1)
                
        except Exception as e:
            typer.echo(f"❌ Error consultando reservas de host: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_consultar_reservas_host())


@app.command("reservas-ciudad")
def consultar_reservas_ciudad(
    ciudad_id: int = typer.Option(..., "--ciudad-id", help="ID de la ciudad"),
    fecha_inicio: str = typer.Option(None, "--fecha-inicio", help="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: str = typer.Option(None, "--fecha-fin", help="Fecha fin (YYYY-MM-DD)")
):
    """CU 5: Consulta reservas de una ciudad por rango de fechas."""
    async def _consultar_reservas_ciudad():
        try:
            from datetime import datetime
            from services.reservations import ReservationService
            
            fecha_inicio_obj = None
            fecha_fin_obj = None
            
            # Validar fechas si se proporcionan
            if fecha_inicio:
                try:
                    fecha_inicio_obj = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Formato de fecha inicio inválido. Usa YYYY-MM-DD")
                    raise typer.Exit(1)
                    
            if fecha_fin:
                try:
                    fecha_fin_obj = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Formato de fecha fin inválido. Usa YYYY-MM-DD")
                    raise typer.Exit(1)
            
            typer.echo(f"\n🏙️  RESERVAS DE LA CIUDAD")
            typer.echo("="*40)
            typer.echo(f"🏙️  Ciudad ID: {ciudad_id}")
            if fecha_inicio_obj:
                typer.echo(f"📅 Desde: {fecha_inicio}")
            if fecha_fin_obj:
                typer.echo(f"📅 Hasta: {fecha_fin}")
            
            reservation_service = ReservationService()
            result = await reservation_service.get_reservas_ciudad(ciudad_id, fecha_inicio_obj, fecha_fin_obj)
            
            if result["success"]:
                reservas = result["reservas"]
                typer.echo(f"\n✅ Encontradas {result['total']} reservas:")
                
                if reservas:
                    typer.echo("\n" + "="*80)
                    for reserva in reservas:
                        typer.echo(f"🆔 Reserva ID: {reserva.get('reserva_id')}")
                        typer.echo(f"   🏠 Propiedad ID: {reserva.get('propiedad_id')}")
                        typer.echo(f"   👤 Host ID: {reserva.get('host_id')}")
                        typer.echo(f"   👤 Huésped ID: {reserva.get('huesped_id')}")
                        typer.echo(f"   📅 Check-in: {reserva.get('fecha_inicio')}")
                        typer.echo(f"   📅 Check-out: {reserva.get('fecha_fin')}")
                        typer.echo(f"   💰 Total: ${reserva.get('precio_total', 0)}")
                        typer.echo(f"   📊 Estado: {reserva.get('estado', 'confirmada')}")
                        typer.echo("-" * 60)
                else:
                    typer.echo("😞 No hay reservas para esta ciudad en el período especificado.")
            else:
                typer.echo(f"❌ Error: {result['error']}")
                raise typer.Exit(1)
                
        except Exception as e:
            typer.echo(f"❌ Error consultando reservas de ciudad: {e}")
            raise typer.Exit(1)
    
    asyncio.run(_consultar_reservas_ciudad())


if __name__ == "__main__":
    app()
