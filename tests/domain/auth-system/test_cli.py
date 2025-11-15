"""
Script temporal para probar solo los comandos que funcionan
"""
import typer
import asyncio
from services.auth import AuthService

app = typer.Typer(
    name="airbnb-backend",
    help="Backend CLI para sistema tipo Airbnb con múltiples bases de datos"
)

@app.command()
def auth(
    action: str = typer.Argument(
        ..., help="Acción: 'login', 'register', 'logout', 'profile', o 'status'"),
    email: str = typer.Option(
        None, "--email", "-e", help="Email del usuario"),
    password: str = typer.Option(
        None, "--password", "-p", help="Contraseña"),
    rol: str = typer.Option(
        None, "--role", "-r", help="Rol: HUESPED, ANFITRION o AMBOS"),
    nombre: str = typer.Option(
        None, "--name", "-n", help="Nombre completo del usuario"),
):
    """Gestiona autenticación de usuarios (registro, login, logout, perfil)."""

    async def _auth():
        auth_service = AuthService()
        
        if action == "register":
            if not email or not password or not rol or not nombre:
                typer.echo("❌ Para registrar necesitas: --email, --password, --role, --name")
                return
                
            result = await auth_service.register(email, password, rol, nombre)
            typer.echo(f"{result.message}")
            
        elif action == "login":
            if not email or not password:
                typer.echo("❌ Para login necesitas: --email, --password")
                return
                
            result = await auth_service.login(email, password)
            typer.echo(f"{result.message}")
            
        else:
            typer.echo(f"❌ Acción '{action}' no implementada aún")

    asyncio.run(_auth())

if __name__ == "__main__":
    app()