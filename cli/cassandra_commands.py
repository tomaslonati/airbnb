"""
CLI Commands para probar los 4 casos de uso de Cassandra recién agregados.
"""

import asyncio
import typer
from datetime import datetime, date
from typing import List, Optional
import json

# Crear la aplicación CLI
app = typer.Typer()

@app.command("propiedades-disponibles")
def consultar_propiedades_disponibles(
    fecha: str = typer.Argument(..., help="Fecha en formato YYYY-MM-DD"),
    formato: str = typer.Option("table", "--formato", "-f", help="Formato de salida: table, json"),
):
    """
    🏠 CU 4: Consultar propiedades disponibles en una fecha específica.
    
    Ejemplo:
        python cli/cassandra_commands.py propiedades-disponibles 2026-03-15
    """
    asyncio.run(_consultar_propiedades_disponibles_async(fecha, formato))

async def _consultar_propiedades_disponibles_async(fecha_str: str, formato: str):
    """Función asíncrona para consultar propiedades disponibles."""
    try:
        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Error: Formato de fecha inválido. Use YYYY-MM-DD")
            return
        
        from services.reservations import ReservationService
        reservation_service = ReservationService()
        
        typer.echo(f"\n🔄 Consultando propiedades disponibles para {fecha_str}...")
        
        result = await reservation_service.get_propiedades_disponibles_fecha(fecha)
        
        if result.get("success"):
            propiedades = result.get("propiedades", [])
            
            if formato == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                typer.echo(f"\n🏠 PROPIEDADES DISPONIBLES - {fecha_str}")
                typer.echo("=" * 60)
                typer.echo(f"📊 Total encontradas: {len(propiedades)}")
                
                if propiedades:
                    typer.echo("\n" + "-" * 60)
                    typer.echo(f"{'ID':<8} {'Ciudad':<15} {'Precio':<12} {'Capacidad':<10}")
                    typer.echo("-" * 60)
                    
                    for prop in propiedades[:20]:  # Limitar a 20 resultados
                        prop_id = prop.get('propiedad_id', 'N/A')
                        ciudad = prop.get('ciudad_nombre', 'N/A')[:14]
                        precio = f"${prop.get('precio_noche', 0):.2f}"
                        capacidad = prop.get('capacidad_huespedes', 'N/A')
                        typer.echo(f"{prop_id:<8} {ciudad:<15} {precio:<12} {capacidad:<10}")
                    
                    if len(propiedades) > 20:
                        typer.echo(f"\n... y {len(propiedades) - 20} más")
                        typer.echo(f"💡 Use --formato json para ver todos los resultados")
                else:
                    typer.echo("\n📭 No hay propiedades disponibles en esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

@app.command("reservas-host")
def consultar_reservas_host(
    host_id: int = typer.Argument(..., help="ID del host/anfitrión"),
    fecha: str = typer.Argument(..., help="Fecha en formato YYYY-MM-DD"),
    formato: str = typer.Option("table", "--formato", "-f", help="Formato de salida: table, json"),
):
    """
    🏡 CU 6: Consultar reservas de un host en una fecha específica.
    
    Ejemplo:
        python cli/cassandra_commands.py reservas-host 1 2026-03-15
    """
    asyncio.run(_consultar_reservas_host_async(host_id, fecha, formato))

async def _consultar_reservas_host_async(host_id: int, fecha_str: str, formato: str):
    """Función asíncrona para consultar reservas por host."""
    try:
        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Error: Formato de fecha inválido. Use YYYY-MM-DD")
            return
        
        from services.reservations import ReservationService
        reservation_service = ReservationService()
        
        typer.echo(f"\n🔄 Consultando reservas del host {host_id} para {fecha_str}...")
        
        result = await reservation_service.get_reservas_host(host_id, fecha)
        
        if result.get("success"):
            reservas = result.get("reservas", [])
            
            if formato == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                typer.echo(f"\n🏡 RESERVAS DEL HOST {host_id} - {fecha_str}")
                typer.echo("=" * 70)
                typer.echo(f"📊 Total encontradas: {len(reservas)}")
                
                if reservas:
                    typer.echo("\n" + "-" * 70)
                    typer.echo(f"{'Reserva ID':<12} {'Propiedad':<12} {'Huésped':<12} {'Precio':<12} {'Estado':<10}")
                    typer.echo("-" * 70)
                    
                    for reserva in reservas:
                        reserva_id = reserva.get('reserva_id', 'N/A')
                        propiedad_id = reserva.get('propiedad_id', 'N/A')
                        huesped_id = reserva.get('huesped_id', 'N/A')
                        precio = f"${reserva.get('precio_total', 0):.2f}"
                        estado = reserva.get('estado', 'N/A')
                        typer.echo(f"{reserva_id:<12} {propiedad_id:<12} {huesped_id:<12} {precio:<12} {estado:<10}")
                else:
                    typer.echo("\n📭 No hay reservas para este host en esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

@app.command("reservas-ciudad")
def consultar_reservas_ciudad(
    ciudad_id: int = typer.Argument(..., help="ID de la ciudad"),
    fecha: str = typer.Argument(..., help="Fecha en formato YYYY-MM-DD"),
    formato: str = typer.Option("table", "--formato", "-f", help="Formato de salida: table, json"),
):
    """
    🏙️ CU 5: Consultar reservas de una ciudad en una fecha específica.
    
    Ejemplo:
        python cli/cassandra_commands.py reservas-ciudad 1 2026-03-15
    """
    asyncio.run(_consultar_reservas_ciudad_async(ciudad_id, fecha, formato))

async def _consultar_reservas_ciudad_async(ciudad_id: int, fecha_str: str, formato: str):
    """Función asíncrona para consultar reservas por ciudad."""
    try:
        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Error: Formato de fecha inválido. Use YYYY-MM-DD")
            return
        
        from services.reservations import ReservationService
        reservation_service = ReservationService()
        
        typer.echo(f"\n🔄 Consultando reservas de la ciudad {ciudad_id} para {fecha_str}...")
        
        result = await reservation_service.get_reservas_ciudad(ciudad_id, fecha)
        
        if result.get("success"):
            reservas = result.get("reservas", [])
            
            if formato == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                typer.echo(f"\n🏙️ RESERVAS DE LA CIUDAD {ciudad_id} - {fecha_str}")
                typer.echo("=" * 70)
                typer.echo(f"📊 Total encontradas: {len(reservas)}")
                
                if reservas:
                    typer.echo("\n" + "-" * 70)
                    typer.echo(f"{'Reserva ID':<12} {'Propiedad':<12} {'Host':<8} {'Huésped':<12} {'Precio':<12} {'Estado':<10}")
                    typer.echo("-" * 70)
                    
                    for reserva in reservas:
                        reserva_id = reserva.get('reserva_id', 'N/A')
                        propiedad_id = reserva.get('propiedad_id', 'N/A')
                        host_id = reserva.get('host_id', 'N/A')
                        huesped_id = reserva.get('huesped_id', 'N/A')
                        precio = f"${reserva.get('precio_total', 0):.2f}"
                        estado = reserva.get('estado', 'N/A')
                        typer.echo(f"{reserva_id:<12} {propiedad_id:<12} {host_id:<8} {huesped_id:<12} {precio:<12} {estado:<10}")
                else:
                    typer.echo("\n📭 No hay reservas para esta ciudad en esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

@app.command("verificar-disponibilidad")
def verificar_disponibilidad_propiedad(
    propiedad_id: int = typer.Argument(..., help="ID de la propiedad"),
    fecha: str = typer.Argument(..., help="Fecha en formato YYYY-MM-DD"),
    formato: str = typer.Option("table", "--formato", "-f", help="Formato de salida: table, json"),
):
    """
    🔍 EXTRA: Verificar disponibilidad específica de una propiedad en una fecha.
    
    Este comando usa el caso de uso 4 (CU4) pero filtra por una propiedad específica.
    
    Ejemplo:
        python cli/cassandra_commands.py verificar-disponibilidad 29 2026-03-15
    """
    asyncio.run(_verificar_disponibilidad_async(propiedad_id, fecha, formato))

async def _verificar_disponibilidad_async(propiedad_id: int, fecha_str: str, formato: str):
    """Función asíncrona para verificar disponibilidad específica."""
    try:
        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Error: Formato de fecha inválido. Use YYYY-MM-DD")
            return
        
        from services.reservations import ReservationService
        reservation_service = ReservationService()
        
        typer.echo(f"\n🔄 Verificando disponibilidad de propiedad {propiedad_id} para {fecha_str}...")
        
        # Usar el servicio de propiedades disponibles y filtrar
        result = await reservation_service.get_propiedades_disponibles_fecha(fecha)
        
        if result.get("success"):
            propiedades = result.get("propiedades", [])
            propiedad_encontrada = None
            
            # Buscar la propiedad específica
            for prop in propiedades:
                if prop.get('propiedad_id') == propiedad_id:
                    propiedad_encontrada = prop
                    break
            
            if formato == "json":
                response = {
                    "success": True,
                    "propiedad_id": propiedad_id,
                    "fecha": fecha_str,
                    "disponible": propiedad_encontrada is not None,
                    "detalles": propiedad_encontrada if propiedad_encontrada else None
                }
                print(json.dumps(response, indent=2, ensure_ascii=False))
            else:
                typer.echo(f"\n🔍 VERIFICACIÓN DE DISPONIBILIDAD")
                typer.echo("=" * 50)
                typer.echo(f"🏠 Propiedad ID: {propiedad_id}")
                typer.echo(f"📅 Fecha: {fecha_str}")
                
                if propiedad_encontrada:
                    typer.echo("✅ Estado: DISPONIBLE")
                    typer.echo(f"💰 Precio: ${propiedad_encontrada.get('precio_noche', 0):.2f}/noche")
                    typer.echo(f"🏙️ Ciudad: {propiedad_encontrada.get('ciudad_nombre', 'N/A')}")
                    typer.echo(f"👥 Capacidad: {propiedad_encontrada.get('capacidad_huespedes', 'N/A')} huéspedes")
                else:
                    typer.echo("❌ Estado: NO DISPONIBLE")
                    typer.echo("💡 La propiedad no está disponible en esta fecha o no existe")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

@app.command("test-todos")
def test_todos_los_casos():
    """
    🧪 PRUEBA COMPLETA: Ejecuta todos los casos de uso con datos de ejemplo.
    
    Esta función prueba los 4 casos de uso con datos conocidos para validar funcionamiento.
    """
    asyncio.run(_test_todos_los_casos_async())

async def _test_todos_los_casos_async():
    """Función asíncrona para probar todos los casos."""
    try:
        fecha_test = "2026-03-15"
        
        typer.echo("\n🧪 EJECUTANDO PRUEBAS DE TODOS LOS CASOS DE USO DE CASSANDRA")
        typer.echo("=" * 80)
        
        # Test CU 4: Propiedades disponibles
        typer.echo("\n🔍 Test CU 4: Propiedades disponibles en una fecha...")
        await _consultar_propiedades_disponibles_async(fecha_test, "table")
        
        typer.echo("\n" + "-" * 80)
        
        # Test CU 6: Reservas por host (usar host_id = 1)
        typer.echo("\n🔍 Test CU 6: Reservas del host 1...")
        await _consultar_reservas_host_async(1, fecha_test, "table")
        
        typer.echo("\n" + "-" * 80)
        
        # Test CU 5: Reservas por ciudad (usar ciudad_id = 1)
        typer.echo("\n🔍 Test CU 5: Reservas de la ciudad 1...")
        await _consultar_reservas_ciudad_async(1, fecha_test, "table")
        
        typer.echo("\n" + "-" * 80)
        
        # Test verificación específica (propiedad 29 que sabemos que existe)
        typer.echo("\n🔍 Test EXTRA: Verificar disponibilidad de propiedad 29...")
        await _verificar_disponibilidad_async(29, fecha_test, "table")
        
        typer.echo("\n" + "=" * 80)
        typer.echo("✅ TODAS LAS PRUEBAS COMPLETADAS")
        typer.echo("💡 Para más detalles, use --formato json en cada comando")
        
    except Exception as e:
        typer.echo(f"❌ Error durante las pruebas: {str(e)}")

if __name__ == "__main__":
    app()