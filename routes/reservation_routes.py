"""
Rutas relacionadas con gestión de reservas.
"""

from typing import Dict, Any
from datetime import date, datetime
from routes.base import BaseRoute
from services.reservations import ReservationService
from utils.logging import get_logger

logger = get_logger(__name__)


class CreateReservationRoute(BaseRoute):
    """Ruta para crear una nueva reserva."""

    def __init__(self):
        super().__init__(
            name="create_reservation",
            description="Crea una nueva reserva de propiedad"
        )
        self.reservation_service = ReservationService()

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros para crear reserva."""
        required_fields = ['property_id', 'user_id', 'check_in', 'check_out']

        for field in required_fields:
            if field not in params or not params[field]:
                logger.warning("Campo requerido faltante", field=field)
                return False

        # Validar fechas
        try:
            check_in = date.fromisoformat(params['check_in'])
            check_out = date.fromisoformat(params['check_out'])

            if check_in >= check_out:
                logger.warning("Fecha de salida debe ser posterior a entrada")
                return False

            if check_in < date.today():
                logger.warning("Fecha de entrada no puede ser en el pasado")
                return False

            params['check_in'] = check_in
            params['check_out'] = check_out

        except ValueError:
            logger.warning("Formato de fecha inválido")
            return False

        # Validar número de huéspedes
        if 'guests' in params:
            try:
                guests = int(params['guests'])
                if guests <= 0:
                    return False
                params['guests'] = guests
            except (ValueError, TypeError):
                return False

        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva reserva."""
        property_id = params['property_id']
        user_id = params['user_id']
        check_in = params['check_in']
        check_out = params['check_out']

        reservation = await self.reservation_service.create_reservation(
            property_id, user_id, check_in, check_out
        )

        return {
            'reservation_created': True,
            'reservation': reservation
        }


class GetUserReservationsRoute(BaseRoute):
    """Ruta para obtener reservas de un usuario."""

    def __init__(self):
        super().__init__(
            name="get_user_reservations",
            description="Obtiene todas las reservas de un usuario"
        )
        self.reservation_service = ReservationService()

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros para obtener reservas."""
        if 'user_id' not in params or not params['user_id']:
            return False

        # Validar límite si está presente
        if 'limit' in params:
            try:
                limit = int(params['limit'])
                if limit <= 0:
                    return False
                params['limit'] = limit
            except (ValueError, TypeError):
                return False

        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene reservas del usuario."""
        user_id = params['user_id']

        reservations = await self.reservation_service.get_user_reservations(user_id)

        # Aplicar límite si se especifica
        limit = params.get('limit')
        if limit and len(reservations) > limit:
            reservations = reservations[:limit]

        return {
            'user_id': user_id,
            'reservations_count': len(reservations),
            'reservations': reservations
        }


class CancelReservationRoute(BaseRoute):
    """Ruta para cancelar una reserva."""

    def __init__(self):
        super().__init__(
            name="cancel_reservation",
            description="Cancela una reserva existente"
        )

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros para cancelar reserva."""
        required_fields = ['reservation_id', 'user_id']

        for field in required_fields:
            if field not in params or not params[field]:
                return False

        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancela una reserva."""
        reservation_id = params['reservation_id']
        user_id = params['user_id']
        reason = params.get('reason', 'User cancellation')

        # En una implementación real, aquí actualizarías la base de datos
        # y registrarías el evento en Cassandra

        return {
            'reservation_cancelled': True,
            'reservation_id': reservation_id,
            'user_id': user_id,
            'cancellation_reason': reason,
            'cancelled_at': datetime.utcnow().isoformat()
        }


class GetReservationDetailsRoute(BaseRoute):
    """Ruta para obtener detalles de una reserva."""

    def __init__(self):
        super().__init__(
            name="get_reservation_details",
            description="Obtiene detalles completos de una reserva específica"
        )

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros para obtener detalles."""
        return 'reservation_id' in params and params['reservation_id']

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene detalles de una reserva."""
        reservation_id = params['reservation_id']

        # En una implementación real, consultarías la base de datos
        reservation_details = {
            'reservation_id': reservation_id,
            'property_id': 'prop-123',
            'property_title': 'Beautiful Apartment in Palermo',
            'user_id': 'user-456',
            'user_name': 'Juan Pérez',
            'check_in': '2024-12-15',
            'check_out': '2024-12-20',
            'guests': 2,
            'total_price': 750.00,
            'status': 'CONFIRMED',
            'special_requests': 'Late check-in',
            'created_at': '2024-11-14T10:30:00Z',
            'host_info': {
                'host_id': 'host-789',
                'host_name': 'María García',
                'host_phone': '+54 11 1234-5678'
            },
            'payment_info': {
                'method': 'credit_card',
                'status': 'completed',
                'transaction_id': 'txn_abc123'
            }
        }

        return {
            'reservation_found': True,
            'reservation': reservation_details
        }
