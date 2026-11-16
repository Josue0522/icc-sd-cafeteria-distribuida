
"""
Coordinador del procesamiento y recuperación de pedidos.

Organiza la comunicación entre caja mediante TCP
y cocina mediante XML-RPC.

Evita procesamientos simultáneos del mismo pedido y
permite reanudar pedidos que quedaron en estados pendientes.
"""

import logging
from threading import Lock
from uuid import UUID
from .notificaciones_cliente import publicar_estado_pedido

from .almacen import (
    obtener_pedido,
    listar_pedidos,
    actualizar_estado,
    TransicionEstadoInvalida,
)

from .modelos import EstadoPedido

from .servicios import (
    enviar_venta_tcp,
    preparar_pedido_rpc,
    ErrorServicioExterno,
)


logger = logging.getLogger(__name__)

# Dos intentos como máximo para la comunicación TCP.
MAX_INTENTOS_TCP = 2

# Control de pedidos que actualmente están siendo procesados.
_pedidos_en_proceso: set[UUID] = set()
_bloqueo_procesamiento = Lock()

# Publicar actualizaciones de estado

def actualizar_y_notificar(
    pedido_id: UUID,
    nuevo_estado: EstadoPedido,
):
    """
    Actualiza el estado oficial y publica el evento WebSocket.

    Si falla la notificación, el procesamiento del pedido
    continúa normalmente.
    """

    pedido_anterior = obtener_pedido(pedido_id)

    if pedido_anterior is None:
        return None

    pedido_actualizado = actualizar_estado(
        pedido_id,
        nuevo_estado,
    )

    if pedido_actualizado is None:
        return None

    # Evitar notificaciones de estados que no cambiaron.
    if pedido_anterior.estado != nuevo_estado:

        notificado = publicar_estado_pedido(
            pedido_actualizado
        )

        if not notificado:
            logger.warning(
                "No se pudo notificar el cambio del pedido %s. "
                "El estado oficial permanece en %s.",
                pedido_id,
                nuevo_estado.value,
            )

    return pedido_actualizado



# 1. Obtener los pedidos que pueden recuperarse

def listar_pedidos_recuperables() -> list[UUID]:
    """
    Devuelve los identificadores de pedidos cuyo procesamiento
    puede iniciarse o reanudarse.
    """

    estados_recuperables = {
        EstadoPedido.RECIBIDO,
        EstadoPedido.PENDIENTE_CAJA,
        EstadoPedido.VENTA_CONFIRMADA,
        EstadoPedido.EN_PREPARACION,
    }

    pedidos = listar_pedidos()

    return [
        pedido.pedido_id
        for pedido in pedidos
        if pedido.estado in estados_recuperables
    ]


# 2. Procesar o recuperar un pedido

def procesar_pedido(pedido_id: UUID) -> None:
    """
    Procesa o reanuda un pedido según su estado actual.

    No permite procesar simultáneamente el mismo pedido.
    """

    # Evitar que dos workers procesen el mismo pedido.
    with _bloqueo_procesamiento:

        if pedido_id in _pedidos_en_proceso:
            logger.warning(
                "El pedido %s ya está siendo procesado.",
                pedido_id,
            )
            return

        _pedidos_en_proceso.add(pedido_id)

    try:
        _procesar_pedido_interno(pedido_id)

    except Exception:
        logger.exception(
            "Error inesperado al procesar el pedido %s.",
            pedido_id,
        )

    finally:
        with _bloqueo_procesamiento:
            _pedidos_en_proceso.discard(pedido_id)


# 3. Lógica interna del procesamiento

def _procesar_pedido_interno(pedido_id: UUID) -> None:
    """
    Ejecuta únicamente las operaciones que correspondan
    al estado actual del pedido.
    """

    pedido = obtener_pedido(pedido_id)

    if pedido is None:
        logger.error(
            "No se encontró el pedido %s.",
            pedido_id,
        )
        return

    logger.info(
        "Procesando pedido %s desde estado %s.",
        pedido_id,
        pedido.estado.value,
    )

    # Los pedidos terminados no vuelven a procesarse.
    estados_finales = {
        EstadoPedido.LISTO,
        EstadoPedido.ERROR_CAJA,
        EstadoPedido.ERROR_COCINA,
    }

    if pedido.estado in estados_finales:
        return

    # 4. Etapa de caja mediante TCP

    if pedido.estado in {
        EstadoPedido.RECIBIDO,
        EstadoPedido.PENDIENTE_CAJA,
    }:

        respuesta_caja = None

        for intento in range(1, MAX_INTENTOS_TCP + 1):

            try:
                logger.info(
                    "Enviando pedido %s a caja. Intento %s.",
                    pedido_id,
                    intento,
                )

                respuesta_caja = enviar_venta_tcp(pedido)
                break

            except ErrorServicioExterno as error:

                logger.warning(
                    "Error de caja para el pedido %s: %s",
                    pedido_id,
                    error.mensaje,
                )

                if (
                    error.reintentable
                    and intento < MAX_INTENTOS_TCP
                ):
                    continue

                # La operación puede haberse procesado
                # aunque no hayamos recibido la respuesta.
                try:
                    actualizar_y_notificar(
                        pedido_id,
                        EstadoPedido.PENDIENTE_CAJA,
                    )
                except TransicionEstadoInvalida:
                    logger.exception(
                        "No se pudo actualizar el estado del pedido %s.",
                        pedido_id,
                    )

                return

        if respuesta_caja is None:
            return

        # Caja rechazó definitivamente la venta.
        if not respuesta_caja["ok"]:

            actualizar_y_notificar(
                pedido_id,
                EstadoPedido.ERROR_CAJA,
            )

            logger.warning(
                "Caja rechazó el pedido %s.",
                pedido_id,
            )

            return

        # Caja confirmó la venta.
        pedido = actualizar_y_notificar(
            pedido_id,
            EstadoPedido.VENTA_CONFIRMADA,
        )

        logger.info(
            "Venta confirmada para el pedido %s.",
            pedido_id,
        )

        if pedido is None:
            return

    # 5. Pasar a preparación si corresponde

    if pedido.estado == EstadoPedido.VENTA_CONFIRMADA:

        pedido = actualizar_y_notificar(
            pedido_id,
            EstadoPedido.EN_PREPARACION,
        )

        if pedido is None:
            return

    # 6. Ejecutar o reanudar la etapa de cocina mediante RPC

    if pedido.estado != EstadoPedido.EN_PREPARACION:
        return

    productos = [
        {
            "producto_id": item.producto_id,
            "nombre": item.nombre,
            "cantidad": item.cantidad,
        }
        for item in pedido.items
    ]

    try:
        respuesta_cocina = preparar_pedido_rpc(
            pedido_id,
            productos,
        )

    except ErrorServicioExterno as error:

        logger.error(
            "Error de comunicación con cocina para el pedido %s: %s",
            pedido_id,
            error.mensaje,
        )

        # Se conserva EN_PREPARACION porque no sabemos
        # si cocina terminó antes de perderse la respuesta.
        return

    # 7. Registrar el resultado final de cocina

    if respuesta_cocina["ok"]:
        estado_final = EstadoPedido.LISTO
    else:
        estado_final = EstadoPedido.ERROR_COCINA

    actualizar_y_notificar(
        pedido_id,
        estado_final,
    )

    logger.info(
        "Pedido %s finalizado con estado %s.",
        pedido_id,
        estado_final.value,
    )


# 8. Recuperar un pedido individual

def recuperar_pedido(pedido_id: UUID) -> bool:
    """
    Permite solicitar la recuperación de un pedido pendiente.

    Retorna True cuando el pedido puede recuperarse.
    No sustituye a un sistema de recuperación automática.
    """

    pedido = obtener_pedido(pedido_id)

    if pedido is None:
        return False

    estados_recuperables = {
        EstadoPedido.RECIBIDO,
        EstadoPedido.PENDIENTE_CAJA,
        EstadoPedido.VENTA_CONFIRMADA,
        EstadoPedido.EN_PREPARACION,
    }

    if pedido.estado not in estados_recuperables:
        return False

    procesar_pedido(pedido_id)

    return True
