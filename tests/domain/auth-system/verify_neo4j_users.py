#!/usr/bin/env python3
"""
Comando CLI para verificar usuarios en Neo4j
"""
import asyncio
import typer
from services.neo4j_user import Neo4jUserService
from db.neo4j import Neo4jConnection


async def verify_neo4j_users():
    """Verifica que los usuarios estén correctamente creados en Neo4j"""
    neo_service = None

    try:
        typer.echo("🔍 Verificando usuarios en Neo4j...")
        typer.echo("=" * 50)

        # Inicializar servicio
        neo_service = Neo4jUserService()

        # Verificar conexión
        connection_result = await neo_service.verify_connection()
        if not connection_result.get('success'):
            typer.echo(
                f"❌ Error de conexión: {connection_result.get('error')}")
            return

        typer.echo("✅ Conexión a Neo4j exitosa\n")

        # Obtener todos los usuarios
        users_result = await neo_service.get_all_users()

        if not users_result.get('success'):
            typer.echo(
                f"❌ Error obteniendo usuarios: {users_result.get('error')}")
            return

        users = users_result.get('users', [])

        if not users:
            typer.echo("📝 No hay usuarios creados en Neo4j")
            return

        typer.echo(f"👥 {len(users)} usuario(s) encontrado(s) en Neo4j:")
        typer.echo("-" * 30)

        for user in users:
            user_id = user.get('id')
            rol = user.get('rol', 'N/A')
            created_at = user.get('created_at', 'N/A')

            role_emoji = {
                'HUESPED': '🛏️',
                'ANFITRION': '🏠',
                'AMBOS': '🔄'
            }.get(rol, '❓')

            typer.echo(f"  {role_emoji} ID: {user_id} | Rol: {rol}")
            if created_at != 'N/A':
                typer.echo(f"      📅 Creado: {created_at}")
            typer.echo()

        # Estadísticas por rol
        rol_counts = {}
        for user in users:
            rol = user.get('rol', 'UNKNOWN')
            rol_counts[rol] = rol_counts.get(rol, 0) + 1

        typer.echo("📊 Estadísticas por rol:")
        for rol, count in rol_counts.items():
            role_emoji = {
                'HUESPED': '🛏️',
                'ANFITRION': '🏠',
                'AMBOS': '🔄'
            }.get(rol, '❓')
            typer.echo(f"  {role_emoji} {rol}: {count}")

        typer.echo(
            f"\n✅ Verificación completada - Total: {len(users)} usuarios")

    except Exception as e:
        typer.echo(f"❌ Error durante la verificación: {str(e)}")

    finally:
        if neo_service:
            await neo_service.close()


def verify_users():
    """Comando CLI para verificar usuarios en Neo4j"""
    asyncio.run(verify_neo4j_users())


if __name__ == "__main__":
    verify_users()
