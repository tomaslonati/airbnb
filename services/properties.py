"""
Servicio para gestionar propiedades.
"""

import asyncio
from typing import Optional, List, Dict, Any
from db import postgres
from utils.logging import get_logger
from utils.performance import measure_time, perf_stats

logger = get_logger(__name__)


class PropertyService:
    """Servicio para crear, actualizar y gestionar propiedades."""

    async def _validate_foreign_keys(
        self,
        pool,
        ciudad_id: int,
        anfitrion_id: int,
        tipo_propiedad_id: int,
        amenities: Optional[List[int]] = None,
        servicios: Optional[List[int]] = None,
        reglas: Optional[List[int]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Valida que todos los IDs externos existan.

        Returns:
            (is_valid, error_message)
        """
        try:
            # Validar ciudad
            ciudad = await pool.fetchval(
                "SELECT id FROM ciudad WHERE id = $1",
                ciudad_id
            )
            if not ciudad:
                return False, f"Ciudad con ID {ciudad_id} no existe"

            # Validar anfitrión
            anfitrion = await pool.fetchval(
                "SELECT id FROM anfitrion WHERE id = $1",
                anfitrion_id
            )
            if not anfitrion:
                return False, f"Anfitrión con ID {anfitrion_id} no existe"

            # Validar tipo de propiedad
            tipo = await pool.fetchval(
                "SELECT id FROM tipo_propiedad WHERE id = $1",
                tipo_propiedad_id
            )
            if not tipo:
                return False, f"Tipo de propiedad con ID {tipo_propiedad_id} no existe"

            # Validar amenities
            if amenities:
                for amenity_id in amenities:
                    amenity = await pool.fetchval(
                        "SELECT id FROM amenities WHERE id = $1",
                        amenity_id
                    )
                    if not amenity:
                        return False, f"Amenity con ID {amenity_id} no existe"

            # Validar servicios
            if servicios:
                for servicio_id in servicios:
                    servicio = await pool.fetchval(
                        "SELECT id FROM servicios WHERE id = $1",
                        servicio_id
                    )
                    if not servicio:
                        return False, f"Servicio con ID {servicio_id} no existe"

            # Validar reglas
            if reglas:
                for regla_id in reglas:
                    regla = await pool.fetchval(
                        "SELECT id FROM regla_propiedad WHERE id = $1",
                        regla_id
                    )
                    if not regla:
                        return False, f"Regla con ID {regla_id} no existe"

            return True, None

        except Exception as e:
            logger.error(f"Error en validación de FKs: {e}")
            return False, f"Error al validar datos: {str(e)}"

    async def get_available_cities(self) -> Dict[str, Any]:
        """
        Obtiene todas las ciudades disponibles.

        Returns:
            Dict con success=True y lista de ciudades, o error
        """
        try:
            pool = await postgres.get_client()
            ciudades = await pool.fetch(
                """
                SELECT id, nombre, cp, pais_id
                FROM ciudad
                ORDER BY id
                """
            )

            ciudades_list = [dict(ciudad) for ciudad in ciudades]

            logger.info(
                f"Ciudades disponibles obtenidas: {len(ciudades_list)}")
            return {
                "success": True,
                "items": ciudades_list
            }

        except Exception as e:
            logger.error(f"Error obteniendo ciudades: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }

    async def get_available_property_types(self) -> Dict[str, Any]:
        """
        Obtiene todos los tipos de propiedad disponibles.

        Returns:
            Dict con success=True y lista de tipos, o error
        """
        try:
            pool = await postgres.get_client()
            tipos = await pool.fetch(
                """
                SELECT id, nombre
                FROM tipo_propiedad
                ORDER BY id
                """
            )

            tipos_list = [dict(tipo) for tipo in tipos]

            logger.info(f"Tipos de propiedad obtenidos: {len(tipos_list)}")
            return {
                "success": True,
                "items": tipos_list
            }

        except Exception as e:
            logger.error(f"Error obteniendo tipos de propiedad: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }

    async def get_available_amenities(self) -> Dict[str, Any]:
        """
        Obtiene todos los amenities disponibles.

        Returns:
            Dict con success=True y lista de amenities, o error
        """
        try:
            pool = await postgres.get_client()
            amenities = await pool.fetch(
                """
                SELECT id, descripcion
                FROM amenities
                ORDER BY id
                """
            )

            amenities_list = [dict(amenity) for amenity in amenities]

            logger.info(f"Amenities obtenidos: {len(amenities_list)}")
            return {
                "success": True,
                "items": amenities_list
            }

        except Exception as e:
            logger.error(f"Error obteniendo amenities: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }

    async def get_available_services(self) -> Dict[str, Any]:
        """
        Obtiene todos los servicios disponibles.

        Returns:
            Dict con success=True y lista de servicios, o error
        """
        try:
            pool = await postgres.get_client()
            servicios = await pool.fetch(
                """
                SELECT id, descripcion
                FROM servicios
                ORDER BY id
                """
            )

            servicios_list = [dict(servicio) for servicio in servicios]

            logger.info(f"Servicios obtenidos: {len(servicios_list)}")
            return {
                "success": True,
                "items": servicios_list
            }

        except Exception as e:
            logger.error(f"Error obteniendo servicios: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }

    async def get_available_house_rules(self) -> Dict[str, Any]:
        """
        Obtiene todas las reglas de la casa disponibles.

        Returns:
            Dict con success=True y lista de reglas, o error
        """
        try:
            pool = await postgres.get_client()
            reglas = await pool.fetch(
                """
                SELECT id, descripcion
                FROM regla_propiedad
                ORDER BY id
                """
            )

            reglas_list = [dict(regla) for regla in reglas]

            logger.info(f"Reglas de la casa obtenidas: {len(reglas_list)}")
            return {
                "success": True,
                "items": reglas_list
            }

        except Exception as e:
            logger.error(f"Error obteniendo reglas de la casa: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }

    async def _get_host_id_from_auth(
        self,
        pool,
        auth_user_id: str
    ) -> Optional[int]:
        """
        Obtiene el anfitrion_id a partir del auth_user_id.
        """
        try:
            result = await pool.fetchval(
                """
                SELECT a.id
                FROM anfitrion a
                JOIN usuario u ON u.id = a.usuario_id
                WHERE u.auth_user_id = $1
                """,
                auth_user_id
            )
            return result
        except Exception as e:
            logger.error(f"Error obteniendo host_id desde auth: {e}")
            return None

    @measure_time("Creación de propiedad")
    async def create_property(
        self,
        nombre: str,
        descripcion: str,
        capacidad: int,
        ciudad_id: int,
        anfitrion_id: Optional[int] = None,
        auth_user_id: Optional[str] = None,
        tipo_propiedad_id: int = 1,
        horario_check_in: Optional[str] = None,
        horario_check_out: Optional[str] = None,
        imagenes: Optional[List[str]] = None,
        amenities: Optional[List[int]] = None,
        servicios: Optional[List[int]] = None,
        reglas: Optional[List[int]] = None,
        generar_calendario: bool = True,
        dias_calendario: int = 90,  # Reducido de 365 a 90 días para mejor UX
    ) -> Dict[str, Any]:
        """
        Crea una nueva propiedad de forma atómica.

        Args:
            nombre: Nombre de la propiedad
            descripcion: Descripción detallada
            capacidad: Cantidad de personas
            ciudad_id: ID de la ciudad
            anfitrion_id: ID del anfitrión (alternativa)
            auth_user_id: auth_user_id de Supabase (si anfitrion_id es None)
            tipo_propiedad_id: ID del tipo de propiedad
            horario_check_in: Horario de check-in (formato HH:MM, opcional)
            horario_check_out: Horario de check-out (formato HH:MM, opcional)
            imagenes: URLs de imágenes
            amenities: IDs de amenities
            servicios: IDs de servicios
            reglas: IDs de reglas
            generar_calendario: Generar calendario base
            dias_calendario: Cuántos días de calendario generar

        Returns:
            Resultado de la creación (success, error, o property_id)
        """
        try:
            pool = await postgres.get_client()

            # Si viene auth_user_id, resolver anfitrion_id
            if auth_user_id and not anfitrion_id:
                anfitrion_id = await self._get_host_id_from_auth(pool, auth_user_id)
                if not anfitrion_id:
                    return {
                        "success": False,
                        "error": "Usuario no está registrado como anfitrión"
                    }

            if not anfitrion_id:
                return {
                    "success": False,
                    "error": "Debes proporcionar anfitrion_id o auth_user_id"
                }

            logger.info(f"Validando datos para propiedad: {nombre}")

            # Validar todos los IDs externos
            is_valid, error_msg = await self._validate_foreign_keys(
                pool,
                ciudad_id,
                anfitrion_id,
                tipo_propiedad_id,
                amenities,
                servicios,
                reglas
            )

            if not is_valid:
                logger.warning(f"Validación fallida: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

            logger.info(f"Creando propiedad: {nombre}")

            # TRANSACCIÓN ATÓMICA: Iniciar con timeout para evitar bloqueos
            async with pool.acquire() as conn:
                try:
                    async with conn.transaction():
                        # 1. Crear la propiedad
                        query = """
                            INSERT INTO propiedad (
                                nombre, descripcion, capacidad,
                                ciudad_id, anfitrion_id, tipo_propiedad_id,
                                imagenes
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id, nombre, descripcion, capacidad
                        """

                        result = await conn.fetchrow(
                            query,
                            nombre,
                            descripcion,
                            capacidad,
                            ciudad_id,
                            anfitrion_id,
                            tipo_propiedad_id,
                            imagenes or []
                        )

                        propiedad_id = result['id']

                        # 2. Actualizar horarios si fueron proporcionados
                        if horario_check_in is not None or horario_check_out is not None:
                            try:
                                horario_query = """
                                    UPDATE propiedad
                                    SET horario_check_in = $2, horario_check_out = $3
                                    WHERE id = $1
                                """
                                logger.info(
                                    f"Actualizando horarios para propiedad {propiedad_id}: in={horario_check_in}, out={horario_check_out}")
                                await conn.execute(horario_query, propiedad_id, horario_check_in, horario_check_out)
                                logger.info(
                                    f"Horarios actualizados exitosamente para propiedad {propiedad_id}")
                            except Exception as horario_error:
                                logger.error(
                                    f"Error al actualizar horarios: {horario_error}")
                                # No fallar el proceso completo por esto
                                pass

                        propiedad_id = result['id']
                        logger.info(f"Propiedad creada con ID: {propiedad_id}")

                        # CORRECCIÓN: Ejecutar operaciones SECUENCIALMENTE dentro de la transacción
                        # (No podemos paralelizar operaciones que usan la misma conexión DB)
                        
                        if amenities:
                            await self._add_amenities(conn, propiedad_id, amenities)
                        if servicios:
                            await self._add_servicios(conn, propiedad_id, servicios)
                        if reglas:
                            await self._add_reglas(conn, propiedad_id, reglas)

                        # 5. Generar calendario base (dentro de la transacción)
                        if generar_calendario:
                            await self._generate_availability(
                                conn, propiedad_id, dias_calendario, ciudad_id
                            )
                            
                except Exception as tx_error:
                    logger.error(f"Error en transacción de creación: {tx_error}")
                    # La transacción se revierte automáticamente
                    raise

            logger.info(
                f"Propiedad {propiedad_id} creada exitosamente con todas las relaciones")

            # CASSANDRA SYNC: Ejecutar fuera de la transacción principal
            if hasattr(self, '_cassandra_fechas_pendientes') and self._cassandra_fechas_pendientes:
                prop_id, fechas_cassandra, ciudad_id_cassandra = self._cassandra_fechas_pendientes
                try:
                    # Importar aquí para evitar import circular
                    import asyncio
                    from db.cassandra import cassandra_init_date
                    
                    # Validar que tenemos datos válidos
                    if prop_id and fechas_cassandra and ciudad_id_cassandra:
                        # Sync en segundo plano para no bloquear la respuesta
                        if len(fechas_cassandra) <= 30:
                            await cassandra_init_date(prop_id, fechas_cassandra, ciudad_id_cassandra)
                            logger.info(f"✅ Cassandra sincronizada para propiedad {prop_id}")
                        else:
                            # Para volúmenes grandes, ejecutar en background
                            asyncio.create_task(self._sync_cassandra_background(prop_id, fechas_cassandra, ciudad_id_cassandra))
                            logger.info(f"🚀 Cassandra ({len(fechas_cassandra)} fechas) se sincronizará en segundo plano")
                    else:
                        logger.warning("⚠️  Datos de Cassandra incompletos, omitiendo sincronización")
                        
                except Exception as cassandra_error:
                    logger.warning(f"⚠️  Error en sync Cassandra (no crítico): {cassandra_error}")
                finally:
                    # Limpiar datos pendientes
                    self._cassandra_fechas_pendientes = None

            # CU3 CASSANDRA SYNC: Sincronizar con colección optimizada para CU3
            try:
                from db.cassandra import cassandra_sync_propiedad_cu3
                await cassandra_sync_propiedad_cu3(
                    propiedad_id=propiedad_id,
                    ciudad_id=ciudad_id,
                    nombre=nombre,
                    capacidad=capacidad,
                    servicios_ids=servicios or []
                )
            except Exception as cu3_error:
                logger.warning(f"⚠️  Error en sync CU3 Cassandra (no crítico): {cu3_error}")

            return {
                "success": True,
                "message": f"Propiedad '{nombre}' creada exitosamente",
                "property_id": propiedad_id,
                "property": dict(result)
            }

        except Exception as e:
            logger.error(f"Error al crear propiedad: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _add_amenities(self, conn, propiedad_id: int, amenity_ids: List[int]):
        """Agrega amenities a una propiedad usando batch operations (dentro de transacción)."""
        try:
            if not amenity_ids:
                return
                
            # OPTIMIZACIÓN: Construir query con VALUES múltiples para mejor rendimiento
            values_placeholder = ",".join([f"(${i*2+1}, ${i*2+2})" for i in range(len(amenity_ids))])
            query = f"""
                INSERT INTO propiedad_amenity (propiedad_id, amenity_id)
                VALUES {values_placeholder}
                ON CONFLICT DO NOTHING
            """
            
            # Aplanar los datos para la query
            query_args = []
            for amenity_id in amenity_ids:
                query_args.extend([propiedad_id, amenity_id])
            
            await conn.execute(query, *query_args)

            logger.info(
                f"Agregados {len(amenity_ids)} amenities a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar amenities: {e}")
            raise

    async def _add_servicios(self, conn, propiedad_id: int, servicio_ids: List[int]):
        """Agrega servicios a una propiedad usando batch operations (dentro de transacción)."""
        try:
            if not servicio_ids:
                return
                
            # OPTIMIZACIÓN: Construir query con VALUES múltiples
            values_placeholder = ",".join([f"(${i*2+1}, ${i*2+2})" for i in range(len(servicio_ids))])
            query = f"""
                INSERT INTO propiedad_servicio (propiedad_id, servicio_id)
                VALUES {values_placeholder}
                ON CONFLICT DO NOTHING
            """
            
            # Aplanar los datos para la query
            query_args = []
            for servicio_id in servicio_ids:
                query_args.extend([propiedad_id, servicio_id])
            
            await conn.execute(query, *query_args)

            logger.info(
                f"Agregados {len(servicio_ids)} servicios a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar servicios: {e}")
            raise

    async def _add_reglas(self, conn, propiedad_id: int, regla_ids: List[int]):
        """Agrega reglas a una propiedad usando batch operations (dentro de transacción)."""
        try:
            if not regla_ids:
                return
                
            # OPTIMIZACIÓN: Construir query con VALUES múltiples
            values_placeholder = ",".join([f"(${i*2+1}, ${i*2+2})" for i in range(len(regla_ids))])
            query = f"""
                INSERT INTO propiedad_regla (propiedad_id, regla_id)
                VALUES {values_placeholder}
                ON CONFLICT DO NOTHING
            """
            
            # Aplanar los datos para la query
            query_args = []
            for regla_id in regla_ids:
                query_args.extend([propiedad_id, regla_id])
            
            await conn.execute(query, *query_args)

            logger.info(
                f"Agregadas {len(regla_ids)} reglas a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar reglas: {e}")
            raise

    async def _generate_availability(
        self,
        conn,
        propiedad_id: int,
        dias: int = 365,
        ciudad_id: int = None
    ):
        """Genera disponibilidad base para los próximos N días usando batch operations."""
        try:
            from datetime import datetime, timedelta
            import asyncio
            from db.cassandra import cassandra_init_date

            fecha_inicio = datetime.now().date()
            tarifa_base = 100.0  # Tarifa por defecto

            # Preparar todos los datos en memoria primero
            fechas_data = []
            fechas_cassandra = []
            
            for i in range(dias):
                fecha = fecha_inicio + timedelta(days=i)
                fechas_data.append((propiedad_id, fecha, tarifa_base))
                fechas_cassandra.append(fecha)

            # SIMPLIFICACIÓN: Eliminar chunking que puede causar problemas de transacción
            query = """
                INSERT INTO fecha (propiedad_id, fecha, tarifa, esta_disponible)
                VALUES ($1, $2, $3, true)
                ON CONFLICT DO NOTHING
            """
            
            logger.info(f"📦 Insertando {len(fechas_data)} fechas en PostgreSQL")
            
            try:
                # Una sola operación executemany para evitar problemas de transacción
                await conn.executemany(query, fechas_data)
                logger.info(f"✅ PostgreSQL: {dias} fechas insertadas exitosamente")
                
            except Exception as db_error:
                logger.error(f"❌ Error insertando fechas: {db_error}")
                raise  # Re-levantar para que se revierta la transacción
            
            logger.info(f"📅 Calendario de {dias} días generado para propiedad {propiedad_id}")

            # SIMPLIFICACIÓN: Cassandra sync después de que se complete la transacción principal
            # Esto se ejecutará FUERA de la transacción para evitar conflictos
            if ciudad_id is not None:
                self._cassandra_fechas_pendientes = (propiedad_id, fechas_cassandra, ciudad_id)
            else:
                logger.warning(f"⚠️  No se puede sincronizar Cassandra: ciudad_id no proporcionado para propiedad {propiedad_id}")
            
            async def sync_cassandra():
                """Sincroniza con Cassandra en segundo plano."""
                try:
                    if fechas_cassandra:
                        await cassandra_init_date(propiedad_id, fechas_cassandra, ciudad_id)
                        logger.info(
                            f"✅ Cassandra: Sincronizada disponibilidad inicial para propiedad {propiedad_id}")
                except Exception as cassandra_error:
                    logger.warning(
                        f"⚠️  Cassandra sync falló (no crítico): {cassandra_error}")
            
            # Ejecutar Cassandra en segundo plano si hay muchas fechas
            if len(fechas_cassandra) > 30:
                # Para volúmenes grandes, hacer sync asíncrono
                asyncio.create_task(sync_cassandra())
                logger.info("🚀 Cassandra se sincronizará en segundo plano")
            else:
                # Para volúmenes pequeños, hacer sync inmediato
                await sync_cassandra()

        except Exception as e:
            logger.error(f"Error al generar disponibilidad: {e}")
            raise

    async def get_property(self, propiedad_id: int) -> Dict[str, Any]:
        """Obtiene los detalles completos de una propiedad incluyendo relaciones."""
        try:
            pool = await postgres.get_client()

            # Obtener propiedad base
            prop_query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.id = $1
            """

            prop = await pool.fetchrow(prop_query, propiedad_id)

            if not prop:
                return {"success": False, "error": "Propiedad no encontrada"}

            # Obtener amenities
            amenities = await pool.fetch(
                """
                SELECT a.id, a.descripcion
                FROM amenities a
                JOIN propiedad_amenity pa ON pa.amenity_id = a.id
                WHERE pa.propiedad_id = $1
                """,
                propiedad_id
            )

            # Obtener servicios
            servicios = await pool.fetch(
                """
                SELECT s.id, s.descripcion
                FROM servicios s
                JOIN propiedad_servicio ps ON ps.servicio_id = s.id
                WHERE ps.propiedad_id = $1
                """,
                propiedad_id
            )

            # Obtener reglas
            reglas = await pool.fetch(
                """
                SELECT r.id, r.descripcion
                FROM regla_propiedad r
                JOIN propiedad_regla pr ON pr.regla_id = r.id
                WHERE pr.propiedad_id = $1
                """,
                propiedad_id
            )

            return {
                "success": True,
                "property": {
                    **dict(prop),
                    "amenities": [dict(a) for a in amenities],
                    "servicios": [dict(s) for s in servicios],
                    "reglas": [dict(r) for r in reglas]
                }
            }

        except Exception as e:
            logger.error(f"Error al obtener propiedad: {e}")
            return {"success": False, "error": str(e)}

    async def list_properties_by_city(self, ciudad_id: int) -> Dict[str, Any]:
        """Lista todas las propiedades de una ciudad."""
        try:
            pool = await postgres.get_client()

            query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.ciudad_id = $1
                ORDER BY p.nombre
            """

            results = await pool.fetch(query, ciudad_id)

            return {
                "success": True,
                "total": len(results),
                "properties": [dict(r) for r in results]
            }

        except Exception as e:
            logger.error(f"Error al listar propiedades: {e}")
            return {"success": False, "error": str(e)}

    async def list_properties_by_host(self, anfitrion_id: int) -> Dict[str, Any]:
        """Lista todas las propiedades de un anfitrión."""
        try:
            pool = await postgres.get_client()

            query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.anfitrion_id = $1
                ORDER BY p.nombre
            """

            results = await pool.fetch(query, anfitrion_id)

            return {
                "success": True,
                "total": len(results),
                "properties": [dict(r) for r in results]
            }

        except Exception as e:
            logger.error(f"Error al listar propiedades del anfitrión: {e}")
            return {"success": False, "error": str(e)}

    async def update_property(
        self,
        property_id: int,
        nombre: str = None,
        descripcion: str = None,
        capacidad: int = None,
        ciudad_id: int = None,
        tipo_propiedad_id: int = None,
        horario_check_in: str = None,
        horario_check_out: str = None,
        imagenes: List[str] = None,
        amenities: List[int] = None,  # Reemplaza completamente los amenities
        servicios: List[int] = None,  # Reemplaza completamente los servicios
        reglas: List[int] = None,     # Reemplaza completamente las reglas
    ) -> Dict[str, Any]:
        """
        Actualiza una propiedad con todas sus características.

        Args:
            property_id: ID de la propiedad
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            capacidad: Nueva capacidad (opcional)
            ciudad_id: Nuevo ID de ciudad (opcional)
            tipo_propiedad_id: Nuevo tipo de propiedad (opcional)
            horario_check_in: Nuevo horario de check-in (opcional)
            horario_check_out: Nuevo horario de check-out (opcional)
            imagenes: Nuevas imágenes (opcional)
            amenities: Lista completa de IDs de amenities para reemplazar (opcional)
            servicios: Lista completa de IDs de servicios para reemplazar (opcional)
            reglas: Lista completa de IDs de reglas para reemplazar (opcional)

        Returns:
            Resultado de la actualización
        """
        try:
            pool = await postgres.get_client()

            # Atualizar en transacción completa
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Construir query dinámico para campos básicos
                    updates = []
                    params = []
                    param_idx = 1

                    if nombre is not None:
                        updates.append(f"nombre = ${param_idx}")
                        params.append(nombre)
                        param_idx += 1

                    if descripcion is not None:
                        updates.append(f"descripcion = ${param_idx}")
                        params.append(descripcion)
                        param_idx += 1

                    if capacidad is not None:
                        updates.append(f"capacidad = ${param_idx}")
                        params.append(capacidad)
                        param_idx += 1

                    if ciudad_id is not None:
                        updates.append(f"ciudad_id = ${param_idx}")
                        params.append(ciudad_id)
                        param_idx += 1

                    if tipo_propiedad_id is not None:
                        updates.append(f"tipo_propiedad_id = ${param_idx}")
                        params.append(tipo_propiedad_id)
                        param_idx += 1

                    if horario_check_in is not None:
                        updates.append(f"horario_check_in = ${param_idx}")
                        params.append(horario_check_in)
                        param_idx += 1

                    if horario_check_out is not None:
                        updates.append(f"horario_check_out = ${param_idx}")
                        params.append(horario_check_out)
                        param_idx += 1

                    if imagenes is not None:
                        updates.append(f"imagenes = ${param_idx}")
                        params.append(imagenes)
                        param_idx += 1

                    # Ejecutar actualización si hay campos para cambiar
                    if updates:
                        params.append(property_id)
                        query = f"""
                            UPDATE propiedad
                            SET {', '.join(updates)}
                            WHERE id = ${param_idx}
                        """
                        await conn.execute(query, *params)

                    # 2. Actualizar amenities si se especifica
                    if amenities is not None:
                        await conn.execute(
                            "DELETE FROM propiedad_amenity WHERE propiedad_id = $1",
                            property_id
                        )
                        if amenities:
                            await self._add_amenities(conn, property_id, amenities)

                    # 3. Actualizar servicios si se especifica
                    if servicios is not None:
                        await conn.execute(
                            "DELETE FROM propiedad_servicio WHERE propiedad_id = $1",
                            property_id
                        )
                        if servicios:
                            await self._add_servicios(conn, property_id, servicios)

                    # 4. Actualizar reglas si se especifica
                    if reglas is not None:
                        await conn.execute(
                            "DELETE FROM propiedad_regla WHERE propiedad_id = $1",
                            property_id
                        )
                        if reglas:
                            await self._add_reglas(conn, property_id, reglas)

            # Obtener datos actualizados de la propiedad
            result = await self.get_property(property_id)
            if not result["success"]:
                return result

            logger.info(f"Propiedad {property_id} completamente actualizada")

            return {
                "success": True,
                "message": "Propiedad completamente actualizada",
                "property": result["property"]
            }

        except Exception as e:
            logger.error(f"Error al actualizar propiedad completa: {e}")
            return {"success": False, "error": str(e)}

    async def delete_property(self, property_id: int) -> Dict[str, Any]:
        """
        Elimina una propiedad y todas sus relaciones (en transacción).

        Args:
            property_id: ID de la propiedad a eliminar

        Returns:
            Resultado de la eliminación
        """
        try:
            pool = await postgres.get_client()

            logger.info(f"Eliminando propiedad {property_id}")

            # TRANSACCIÓN ATÓMICA: Eliminar propiedad y todas las relaciones
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Eliminar amenities
                    await conn.execute(
                        "DELETE FROM propiedad_amenity WHERE propiedad_id = $1",
                        property_id
                    )

                    # 2. Eliminar servicios
                    await conn.execute(
                        "DELETE FROM propiedad_servicio WHERE propiedad_id = $1",
                        property_id
                    )

                    # 3. Eliminar reglas
                    await conn.execute(
                        "DELETE FROM propiedad_regla WHERE propiedad_id = $1",
                        property_id
                    )

                    # 4. Eliminar disponibilidad (calendario)
                    await conn.execute(
                        "DELETE FROM fecha WHERE propiedad_id = $1",
                        property_id
                    )

                    # 5. Eliminar reservas (si existen)
                    await conn.execute(
                        "DELETE FROM reserva WHERE propiedad_id = $1",
                        property_id
                    )

                    # 6. Finalmente, eliminar la propiedad
                    result = await conn.fetchval(
                        "DELETE FROM propiedad WHERE id = $1 RETURNING id",
                        property_id
                    )

            if result is None:
                return {
                    "success": False,
                    "error": f"Propiedad con ID {property_id} no existe"
                }

            logger.info(f"Propiedad {property_id} eliminada exitosamente")

            return {
                "success": True,
                "message": f"Propiedad {property_id} eliminada con todas sus relaciones"
            }

        except Exception as e:
            logger.error(f"Error al eliminar propiedad: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_cassandra_background(self, propiedad_id: int, fechas: list, ciudad_id: int):
        """Sincroniza Cassandra en segundo plano para volúmenes grandes."""
        try:
            from db.cassandra import cassandra_init_date
            await cassandra_init_date(propiedad_id, fechas, ciudad_id)
            logger.info(f"✅ Cassandra background sync completado para propiedad {propiedad_id}")
        except Exception as e:
            logger.warning(f"⚠️  Cassandra background sync falló para propiedad {propiedad_id}: {e}")
