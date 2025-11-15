#!/usr/bin/env python3
"""
Script para probar la integración MongoDB a través del flujo normal de autenticación
"""
import asyncio
import typer
from services.auth import AuthService
from services.mongo_host import MongoHostService
from utils.logging import get_logger

logger = get_logger(__name__)


async def test_auth_mongo_integration():
    """Prueba la integración MongoDB usando el flujo normal de autenticación"""
    mongo_service = None
    auth_service = None

    try:
        typer.echo("🔄 PRUEBA DE INTEGRACIÓN AUTH → MONGODB")
        typer.echo("=" * 50)

        # Inicializar servicios
        auth_service = AuthService()
        mongo_service = MongoHostService()

        # Verificar MongoDB
        mongo_connection = await mongo_service.verify_connection()
        if not mongo_connection.get('success'):
            typer.echo(f"❌ Error MongoDB: {mongo_connection.get('error')}")
            return
        typer.echo("✅ MongoDB conectado\n")

        # Obtener estado inicial de MongoDB
        initial_hosts = await mongo_service.get_all_hosts()
        initial_count = len(initial_hosts.get('hosts', [])
                            ) if initial_hosts.get('success') else 0
        typer.echo(f"📊 Documentos MongoDB iniciales: {initial_count}")

        # Prueba 1: Registrar HUESPED (no debe crear documento MongoDB)
        typer.echo("\n📝 Prueba 1: Registro HUESPED")
        typer.echo("-" * 30)

        guest_result = await auth_service.register(
            email="fresh_guest@example.com",
            password="test123",
            rol="HUESPED",
            nombre="Usuario Huésped Fresh"
        )
        typer.echo(f"Resultado: {guest_result.message}")

        if guest_result.success:
            # Verificar que NO se creó documento MongoDB
            after_guest = await mongo_service.get_all_hosts()
            after_guest_count = len(after_guest.get(
                'hosts', [])) if after_guest.get('success') else 0

            if after_guest_count == initial_count:
                typer.echo("✅ Correcto: HUESPED no creó documento MongoDB")
            else:
                typer.echo(
                    f"⚠️  Inesperado: Documentos cambió de {initial_count} a {after_guest_count}")

        # Prueba 2: Registrar ANFITRION (SÍ debe crear documento MongoDB)
        typer.echo("\n📝 Prueba 2: Registro ANFITRIÓN")
        typer.echo("-" * 30)

        host_result = await auth_service.register(
            email="fresh_host@example.com",
            password="test123",
            rol="ANFITRION",
            nombre="Usuario Anfitrión Fresh"
        )
        typer.echo(f"Resultado: {host_result.message}")

        if host_result.success and host_result.user_profile:
            anfitrion_id = host_result.user_profile.anfitrion_id
            typer.echo(f"ID Anfitrión obtenido: {anfitrion_id}")

            if anfitrion_id:
                # Verificar que SÍ se creó documento MongoDB
                host_doc = await mongo_service.get_host_document(anfitrion_id)
                if host_doc.get('success'):
                    doc = host_doc['document']
                    typer.echo(f"✅ Documento MongoDB creado:")
                    typer.echo(f"   Host ID: {doc['host_id']}")
                    typer.echo(f"   Ratings: {len(doc['ratings'])}")
                    typer.echo(f"   Stats: {doc['stats']}")
                else:
                    typer.echo(
                        f"❌ No se encontró documento para anfitrión ID {anfitrion_id}")
            else:
                typer.echo("❌ No se obtuvo ID de anfitrión")

        # Prueba 3: Registrar AMBOS (SÍ debe crear documento MongoDB)
        typer.echo("\n📝 Prueba 3: Registro AMBOS")
        typer.echo("-" * 30)

        both_result = await auth_service.register(
            email="fresh_both@example.com",
            password="test123",
            rol="AMBOS",
            nombre="Usuario Ambos Fresh"
        )
        typer.echo(f"Resultado: {both_result.message}")

        if both_result.success and both_result.user_profile:
            anfitrion_id = both_result.user_profile.anfitrion_id
            typer.echo(f"ID Anfitrión obtenido: {anfitrion_id}")

            if anfitrion_id:
                # Verificar que SÍ se creó documento MongoDB
                host_doc = await mongo_service.get_host_document(anfitrion_id)
                if host_doc.get('success'):
                    doc = host_doc['document']
                    typer.echo(f"✅ Documento MongoDB creado para AMBOS:")
                    typer.echo(f"   Host ID: {doc['host_id']}")
                    typer.echo(f"   Ratings: {len(doc['ratings'])}")
                    typer.echo(f"   Stats: {doc['stats']}")
                else:
                    typer.echo(
                        f"❌ No se encontró documento para anfitrión ID {anfitrion_id}")
            else:
                typer.echo("❌ No se obtuvo ID de anfitrión para usuario AMBOS")

        # Resumen final
        typer.echo("\n📊 RESUMEN FINAL")
        typer.echo("=" * 30)

        final_hosts = await mongo_service.get_all_hosts()
        if final_hosts.get('success'):
            final_count = len(final_hosts['hosts'])
            typer.echo(f"Total documentos MongoDB: {final_count}")
            typer.echo(f"Incremento esperado: 2 (ANFITRION + AMBOS)")
            typer.echo(f"Incremento real: {final_count - initial_count}")

            if final_count - initial_count == 2:
                typer.echo("✅ Integración funcionando correctamente")
            else:
                typer.echo("⚠️  Diferencia inesperada en documentos")

            # Mostrar detalles de los documentos
            typer.echo("\nDocumentos actuales:")
            for i, host in enumerate(final_hosts['hosts'], 1):
                host_id = host['host_id']
                typer.echo(f"  {i}. Host ID: {host_id}")

        typer.echo("\n🎉 Prueba de integración completada")

    except Exception as e:
        typer.echo(f"❌ Error durante la prueba: {str(e)}")
        logger.error("Error en prueba de integración", error=str(e))

    finally:
        # Limpiar recursos
        if auth_service and hasattr(auth_service, 'neo4j_user_service'):
            await auth_service.neo4j_user_service.close()


def test_simple_integration():
    """Función de entrada para el test simplificado"""
    asyncio.run(test_auth_mongo_integration())


if __name__ == "__main__":
    test_simple_integration()
