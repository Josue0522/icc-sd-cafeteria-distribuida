
"""
Cliente WebSocket de la API REST.

Publica los cambios de estado de los pedidos en el
servicio de notificaciones.

No administra las conexiones de los estudiantes;
esa responsabilidad pertenece al módulo de Bryan.
"""

import json
import logging

from websockets.sync.client import connect
from websockets.exceptions import WebSocketException

from .configuracion import (
    NOTIFICACIONES_WS_URL,
    NOTIFICACIONES_WS_TIMEOUT_SECONDS,
)

from .modelos import PedidoRespuesta


logger = logging.getLogger(__name__)


# 1. Mensajes asociados a los estados

MENSAJES_ESTADO = {
    "RECIBIDO": "Tu pedido fue recibido correctamente.",
    "PENDIENTE_CAJA": "Estamos verificando el registro de tu venta.",
    "VENTA_CONFIRMADA": "Tu venta fue confirmada.",
    "EN_PREPARACION": "Tu pedido está siendo preparado.",
    "LISTO": "¡Tu pedido está listo!",
    "ERROR_CAJA": "No fue posible confirmar tu venta.",
    "ERROR_COCINA": "No fue posible completar la preparación.",
}


# 2. Construir el evento WebSocket

def construir_evento_estado(
    pedido: PedidoRespuesta,
) -> dict:
    """
    Construye el mensaje JSON que recibirá el servicio
    de notificaciones.
    """

    fecha = (
        pedido.actualizado_en
        .isoformat()
        .replace("+00:00", "Z")
    )

    return {
        "tipo": "estado_actualizado",
        "pedido_id": str(pedido.pedido_id),
        "estado": pedido.estado.value,
        "mensaje": MENSAJES_ESTADO[pedido.estado.value],
        "fecha": fecha,
    }


# 3. Publicar el cambio de estado

def publicar_estado_pedido(
    pedido: PedidoRespuesta,
) -> bool:
    """
    Envía un evento al servidor WebSocket de notificaciones.

    Abre una conexión, envía un mensaje y cierra la conexión.

    Retorna:
        True: el mensaje pudo enviarse.
        False: ocurrió un problema de comunicación.

    Los problemas de notificación no deben interrumpir
    el procesamiento principal del pedido.
    """

    evento = construir_evento_estado(pedido)

    mensaje = json.dumps(
        evento,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    try:

        with connect(
            NOTIFICACIONES_WS_URL,
            open_timeout=NOTIFICACIONES_WS_TIMEOUT_SECONDS,
            close_timeout=NOTIFICACIONES_WS_TIMEOUT_SECONDS,
            max_size=65536,
            proxy=None,
        ) as websocket:

            websocket.send(mensaje)

        logger.info(
            "Notificación enviada para el pedido %s. Estado: %s.",
            pedido.pedido_id,
            pedido.estado.value,
        )

        return True

    except (OSError, TimeoutError, WebSocketException) as error:

        logger.warning(
            "No se pudo notificar el pedido %s: %s",
            pedido.pedido_id,
            error,
        )

        return False

    except Exception:

        # Una falla inesperada en las notificaciones no debe
        # detener el procesamiento principal del pedido.
        logger.exception(
            "Error inesperado al notificar el pedido %s.",
            pedido.pedido_id,
        )

        return False
