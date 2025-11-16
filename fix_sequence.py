"""
Script para corregir la secuencia de auto-incremento de la tabla reserva
"""
import asyncio
from db.postgres import get_client


async def fix_reserva_sequence():
    """
    Corrige la secuencia reserva_id_seq para evitar conflictos de clave primaria
    """
    print("🔧 CORRIGIENDO SECUENCIA DE RESERVA")
    print("=" * 50)

    pool = await get_client()
    async with pool.acquire() as conn:
        try:
            # 1. Obtener el máximo ID actual en la tabla reserva
            max_id_result = await conn.fetchval("SELECT COALESCE(MAX(id), 0) FROM reserva")
            print(f"📊 Máximo ID actual en tabla reserva: {max_id_result}")

            # 2. Obtener el valor actual de la secuencia
            current_seq_value = await conn.fetchval("SELECT currval('reserva_id_seq')")
            print(f"📊 Valor actual de secuencia: {current_seq_value}")

            # 3. Si la secuencia está por detrás del máximo ID, ajustarla
            if current_seq_value <= max_id_result:
                new_seq_value = max_id_result + 1
                await conn.fetchval("SELECT setval('reserva_id_seq', $1)", new_seq_value)
                print(f"✅ Secuencia ajustada a: {new_seq_value}")
            else:
                print("✅ La secuencia ya está correcta")

            # 4. Verificar el próximo valor que se generará
            next_value = await conn.fetchval("SELECT nextval('reserva_id_seq')")
            print(f"🔄 Próximo ID que se generará: {next_value}")

            # 5. Resetear la secuencia al valor anterior para no saltar un número
            await conn.fetchval("SELECT setval('reserva_id_seq', $1)", next_value - 1)

            print("✅ Secuencia corregida exitosamente")

        except Exception as e:
            print(f"❌ Error corrigiendo secuencia: {e}")
            raise


async def test_sequence():
    """
    Prueba que la secuencia funciona correctamente
    """
    print("\n🧪 PROBANDO SECUENCIA")
    print("=" * 50)

    pool = await get_client()
    async with pool.acquire() as conn:
        try:
            # Simular la inserción de una nueva reserva para verificar que no hay conflictos
            next_id = await conn.fetchval("SELECT nextval('reserva_id_seq')")
            print(f"📋 Próximo ID disponible: {next_id}")

            # Verificar que ese ID no existe en la tabla
            existing = await conn.fetchval("SELECT COUNT(*) FROM reserva WHERE id = $1", next_id)

            if existing == 0:
                print("✅ El próximo ID está disponible")
            else:
                print("❌ Conflicto: el próximo ID ya existe en la tabla")

            # Resetear para no consumir el ID
            await conn.fetchval("SELECT setval('reserva_id_seq', $1)", next_id - 1)

        except Exception as e:
            print(f"❌ Error en prueba: {e}")


async def main():
    await fix_reserva_sequence()
    await test_sequence()


if __name__ == "__main__":
    asyncio.run(main())
