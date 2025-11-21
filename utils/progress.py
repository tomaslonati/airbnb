"""
Utilidades para mostrar progreso en el CLI.
"""

import time
import asyncio
from typing import List, Callable, Any
import typer


class ProgressIndicator:
    """Indicador de progreso simple para operaciones largas."""
    
    def __init__(self, message: str = "Procesando"):
        self.message = message
        self.is_running = False
        self.task = None
        
    async def start(self):
        """Inicia el indicador de progreso."""
        self.is_running = True
        self.task = asyncio.create_task(self._animate())
        
    async def stop(self):
        """Detiene el indicador de progreso."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        # Limpiar la línea
        print("\r" + " " * 50 + "\r", end="")
        
    async def _animate(self):
        """Animación del indicador."""
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        
        try:
            while self.is_running:
                char = spinner_chars[i % len(spinner_chars)]
                print(f"\r{char} {self.message}...", end="", flush=True)
                await asyncio.sleep(0.1)
                i += 1
        except asyncio.CancelledError:
            pass


class ProgressBar:
    """Barra de progreso simple para operaciones con pasos conocidos."""
    
    def __init__(self, total: int, prefix: str = "Progreso", width: int = 30):
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.width = width
        self.start_time = time.time()
        
    def update(self, step: int = 1):
        """Actualiza la barra de progreso."""
        self.current += step
        self._display()
        
    def _display(self):
        """Muestra la barra de progreso."""
        if self.total == 0:
            percent = 100
        else:
            percent = (self.current / self.total) * 100
            
        filled = int(self.width * self.current / self.total) if self.total > 0 else self.width
        bar = "█" * filled + "░" * (self.width - filled)
        
        elapsed_time = time.time() - self.start_time
        
        print(f"\r{self.prefix}: [{bar}] {percent:.1f}% ({self.current}/{self.total}) - {elapsed_time:.1f}s", end="", flush=True)
        
        if self.current >= self.total:
            print()  # Nueva línea al completar


async def with_progress(
    coro: Callable,
    message: str = "Procesando",
    show_spinner: bool = True
) -> Any:
    """
    Ejecuta una corrutina mostrando un indicador de progreso.
    
    Args:
        coro: Corrutina a ejecutar
        message: Mensaje a mostrar
        show_spinner: Si mostrar el spinner animado
    
    Returns:
        Resultado de la corrutina
    """
    if show_spinner:
        progress = ProgressIndicator(message)
        await progress.start()
        
        try:
            result = await coro
            return result
        finally:
            await progress.stop()
    else:
        return await coro


def show_step(step_num: int, total_steps: int, description: str):
    """Muestra el paso actual en un proceso multi-paso."""
    typer.echo(f"📋 Paso {step_num}/{total_steps}: {description}")


def show_success(message: str):
    """Muestra un mensaje de éxito."""
    typer.echo(f"✅ {message}")


def show_warning(message: str):
    """Muestra un mensaje de advertencia."""
    typer.echo(f"⚠️  {message}")


def show_error(message: str):
    """Muestra un mensaje de error."""
    typer.echo(f"❌ {message}")


def show_info(message: str):
    """Muestra un mensaje informativo."""
    typer.echo(f"ℹ️  {message}")