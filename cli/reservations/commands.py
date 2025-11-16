"""
Comandos CLI para gestión de reservas.
"""

import typer
from datetime import datetime
from services.reservations import ReservationService
from utils.logging import get_logger

logger = get_logger(__name__)

app = typer.Typer(
    name="reservations",
    help="Gestión de reservas de propiedades"
)


async def handle_reservation_management(user_profile):
    """Gestiona las reservas del huésped."""
    # Verificar que el usuario sea huésped
    if user_profile.rol not in ['HUESPED', 'AMBOS']:
        typer.echo("❌ Esta función solo está disponible para huéspedes")
        typer.echo("Presiona Enter para continuar...")
        input()
        return
    
    if not user_profile.huesped_id:
        typer.echo("❌ No se encontró ID de huésped")
        typer.echo("Presiona Enter para continuar...")
        input()
        return
    
    reservation_service = ReservationService()
    
    while True:
        typer.echo("\n📅 GESTIÓN DE RESERVAS")
        typer.echo("=" * 50)
        typer.echo(f"👤 Huésped: {user_profile.nombre} (ID: {user_profile.huesped_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver mis reservas")
        typer.echo("2. ➕ Crear nueva reserva")
        typer.echo("3. 📝 Ver detalles de una reserva")
        typer.echo("4. ❌ Cancelar reserva")
        typer.echo("5. 🔍 Ver disponibilidad de una propiedad")
        typer.echo("6. ⬅️  Volver al menú principal")
        
        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)
            
            if choice == 1:
                # Listar reservas
                await show_user_reservations(reservation_service, user_profile.huesped_id)
            elif choice == 2:
                # Crear reserva
                await create_reservation_interactive(reservation_service, user_profile.huesped_id)
            elif choice == 3:
                # Ver detalles
                await show_reservation_details(reservation_service)
            elif choice == 4:
                # Cancelar reserva
                await cancel_reservation_interactive(reservation_service, user_profile.huesped_id)
            elif choice == 5:
                # Ver disponibilidad
                await check_property_availability(reservation_service)
            elif choice == 6:
                # Volver
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 6.")
                typer.echo("Presiona Enter para continuar...")
                input()
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
            typer.echo("Presiona Enter para continuar...")
            input()
        except KeyboardInterrupt:
            break


async def show_user_reservations(reservation_service, huesped_id):
    """Muestra las reservas del huésped."""
    typer.echo("\n📋 MIS RESERVAS")
    typer.echo("=" * 50)
    
    include_cancelled = typer.confirm("¿Incluir reservas canceladas?", default=False)
    
    result = await reservation_service.get_user_reservations(huesped_id, include_cancelled)
    
    if result.get("success"):
        reservations = result.get("reservations", [])
        total = result.get("total", 0)
        
        if total == 0:
            typer.echo("📝 No tienes reservas registradas aún")
        else:
            typer.echo(f"Total de reservas: {total}\n")
            for reserva in reservations:
                status_emoji = "✅" if reserva['estado'] == "Confirmada" else "❌" if reserva['estado'] == "Cancelada" else "⏳"
                typer.echo(f"{status_emoji} Reserva #{reserva['id']}")
                typer.echo(f"   🏠 {reserva['propiedad_nombre']}")
                typer.echo(f"   📍 {reserva['ciudad']}, {reserva['pais']}")
                typer.echo(f"   📅 {reserva['check_in']} → {reserva['check_out']} ({reserva['num_nights']} noches)")
                typer.echo(f"   👥 {reserva['num_huespedes']} huésped(es)")
                typer.echo(f"   💰 ${reserva['precio_total']:.2f}")
                typer.echo(f"   📊 Estado: {reserva['estado']}")
                typer.echo()
    else:
        typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")
    
    typer.echo("Presiona Enter para continuar...")
    input()


async def create_reservation_interactive(reservation_service, huesped_id):
    """Crea una reserva de forma interactiva."""
    typer.echo("\n➕ CREAR NUEVA RESERVA")
    typer.echo("=" * 50)
    
    try:
        propiedad_id = typer.prompt("🏠 ID de la propiedad", type=int)
        
        # Obtener fechas
        typer.echo("\n📅 Fechas (formato: YYYY-MM-DD)")
        check_in_str = typer.prompt("   Fecha de entrada")
        check_out_str = typer.prompt("   Fecha de salida")
        
        try:
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("\n❌ Formato de fecha inválido. Usa YYYY-MM-DD")
            typer.echo("Presiona Enter para continuar...")
            input()
            return
        
        num_huespedes = typer.prompt("👥 Número de huéspedes", type=int, default=1)
        comentarios = typer.prompt("💬 Comentarios especiales (Enter para omitir)", default="")
        
        typer.echo("\n🔄 Creando reserva...")
        
        result = await reservation_service.create_reservation(
            propiedad_id=propiedad_id,
            huesped_id=huesped_id,
            check_in=check_in,
            check_out=check_out,
            num_huespedes=num_huespedes,
            comentarios=comentarios if comentarios else None
        )
        
        if result.get("success"):
            reserva = result.get("reservation")
            typer.echo(f"\n✅ {result.get('message')}")
            typer.echo(f"🆔 ID de la reserva: {reserva['id']}")
            typer.echo(f"🏠 Propiedad: {reserva['propiedad_nombre']}")
            typer.echo(f"📅 {reserva['check_in']} → {reserva['check_out']} ({reserva['num_nights']} noches)")
            typer.echo(f"💰 Precio total: ${reserva['precio_total']:.2f}")
            typer.echo(f"📊 Estado: {reserva['estado']}")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")
    
    except ValueError as e:
        typer.echo(f"\n❌ Error en los datos ingresados: {e}")
    except Exception as e:
        typer.echo(f"\n❌ Error inesperado: {e}")
    
    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_reservation_details(reservation_service):
    """Muestra los detalles de una reserva."""
    typer.echo("\n📝 VER DETALLES DE RESERVA")
    typer.echo("=" * 50)
    
    try:
        reserva_id = typer.prompt("🆔 ID de la reserva", type=int)
        
        result = await reservation_service.get_reservation(reserva_id)
        
        if result.get("success"):
            reserva = result.get("reservation")
            prop = reserva['propiedad']
            
            typer.echo(f"\n📋 Reserva #{reserva['id']}")
            typer.echo(f"   📊 Estado: {reserva['estado']}")
            typer.echo(f"   📅 Creada: {reserva['fecha_creacion']}")
            
            typer.echo("\n🏠 Propiedad:")
            typer.echo(f"   {prop['nombre']}")
            typer.echo(f"   {prop['descripcion']}")
            typer.echo(f"   📍 {prop['ciudad']}, {prop['pais']}")
            
            typer.echo("\n📅 Estadía:")
            typer.echo(f"   Check-in: {reserva['check_in']}")
            typer.echo(f"   Check-out: {reserva['check_out']}")
            typer.echo(f"   Noches: {reserva['num_nights']}")
            typer.echo(f"   Huéspedes: {reserva['num_huespedes']}")
            
            typer.echo("\n💰 Información de pago:")
            typer.echo(f"   Total: ${reserva['precio_total']:.2f}")
            typer.echo(f"   Método: {reserva['metodo_pago']}")
            
            if reserva.get('comentarios'):
                typer.echo("\n💬 Comentarios:")
                typer.echo(f"   {reserva['comentarios']}")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")
    
    except ValueError:
        typer.echo("\n❌ ID inválido")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")
    
    typer.echo("\nPresiona Enter para continuar...")
    input()


async def cancel_reservation_interactive(reservation_service, huesped_id):
    """Cancela una reserva de forma interactiva."""
    typer.echo("\n❌ CANCELAR RESERVA")
    typer.echo("=" * 50)
    
    try:
        reserva_id = typer.prompt("🆔 ID de la reserva a cancelar", type=int)
        
        # Mostrar detalles de la reserva antes de cancelar
        reserva_result = await reservation_service.get_reservation(reserva_id)
        
        if not reserva_result.get("success"):
            typer.echo(f"❌ Error: {reserva_result.get('error')}")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return
        
        reserva = reserva_result.get("reservation")
        
        # Verificar ownership
        if reserva['huesped']['id'] != huesped_id:
            typer.echo("❌ Esta reserva no te pertenece")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return
        
        typer.echo("\n⚠️  Vas a cancelar:")
        typer.echo(f"   Reserva #{reserva['id']}")
        typer.echo(f"   🏠 {reserva['propiedad']['nombre']}")
        typer.echo(f"   📅 {reserva['check_in']} → {reserva['check_out']}")
        typer.echo(f"   💰 ${reserva['precio_total']:.2f}")
        
        if typer.confirm("\n¿Estás seguro de que deseas cancelar esta reserva?"):
            reason = typer.prompt("💬 Razón de la cancelación (opcional)", default="")
            
            typer.echo("\n🔄 Cancelando reserva...")
            
            result = await reservation_service.cancel_reservation(
                reserva_id,
                huesped_id,
                reason if reason else None
            )
            
            if result.get("success"):
                typer.echo(f"\n✅ {result.get('message')}")
            else:
                typer.echo(f"\n❌ Error: {result.get('error')}")
        else:
            typer.echo("\n❌ Cancelación abortada")
    
    except ValueError:
        typer.echo("\n❌ ID inválido")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")
    
    typer.echo("\nPresiona Enter para continuar...")
    input()


async def check_property_availability(reservation_service):
    """Verifica la disponibilidad de una propiedad."""
    typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD")
    typer.echo("=" * 50)
    
    try:
        propiedad_id = typer.prompt("🏠 ID de la propiedad", type=int)
        
        typer.echo("\n📅 Rango de fechas (formato: YYYY-MM-DD)")
        start_str = typer.prompt("   Fecha inicio")
        end_str = typer.prompt("   Fecha fin")
        
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("\n❌ Formato de fecha inválido. Usa YYYY-MM-DD")
            typer.echo("Presiona Enter para continuar...")
            input()
            return
        
        typer.echo("\n🔄 Consultando disponibilidad...")
        
        result = await reservation_service.get_property_availability(
            propiedad_id,
            start_date,
            end_date
        )
        
        if result.get("success"):
            available = result.get("available_dates", [])
            unavailable = result.get("unavailable_dates", [])
            
            typer.echo(f"\n📊 Disponibilidad para propiedad #{propiedad_id}")
            typer.echo(f"   Período: {result['start_date']} → {result['end_date']}")
            typer.echo(f"   Total días: {result['total_days']}")
            typer.echo(f"   ✅ Disponibles: {len(available)} días")
            typer.echo(f"   ❌ No disponibles: {len(unavailable)} días")
            
            if available and len(available) <= 10:
                typer.echo("\n✅ Fechas disponibles:")
                for date_info in available[:10]:
                    typer.echo(f"   {date_info['fecha']} - ${date_info['precio']:.2f}/noche")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")
    
    except ValueError:
        typer.echo("\n❌ Datos inválidos")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")
    
    typer.echo("\nPresiona Enter para continuar...")
    input()


