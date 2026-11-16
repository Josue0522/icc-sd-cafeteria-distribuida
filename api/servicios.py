
"""
Clientes de comunicación interna del sistema distribuido.

Contiene:
- Cliente TCP para caja y facturación.
- Cliente XML-RPC para cocina.

"""

import json
import socket
import xmlrpc.client

from uuid import UUID
from typing import Any
from http.client import HTTPException

from .configuracion import (
    TCP_HOST,
    TCP_PORT,
    TCP_TIMEOUT_SECONDS,
    TCP_MAX_MESSAGE_BYTES,
    RPC_URL,
    RPC_TIMEOUT_SECONDS,
)

from .modelos import PedidoRespuesta


# 1. EXCEPCIÓN GENERAL DE COMUNICACIÓN

class ErrorServicioExterno(Exception):
    """
    Representa un error durante la comunicación con
    un servicio externo del sistema.
    """

    def __init__(
        self,
        servicio: str,
        codigo: str,
        mensaje: str,
        reintentable: bool = True,
    ):
        self.servicio = servicio
        self.codigo = codigo
        self.mensaje = mensaje
        self.reintentable = reintentable

        super().__init__(mensaje)


# 2. CLIENTE TCP: CAJA Y FACTURACIÓN

def construir_solicitud_venta(
    pedido: PedidoRespuesta,
) -> dict[str, Any]:
    """
    Construye el mensaje que la API enviará al servidor TCP.

    El operacion_id se genera a partir del pedido_id para
    mantener el mismo identificador en todos los reintentos.
    """

    operacion_id = f"VENTA-{pedido.pedido_id}"

    items = []

    for item in pedido.items:

        items.append({
            "producto_id": item.producto_id,
            "nombre": item.nombre,
            "cantidad": item.cantidad,
            "precio_unitario": format(
                item.precio_unitario, ".2f"
            ),
            "subtotal": format(
                item.subtotal, ".2f"
            ),
        })

    return {
        "version": 1,
        "tipo": "REGISTRAR_VENTA",
        "operacion_id": operacion_id,
        "pedido_id": str(pedido.pedido_id),
        "moneda": pedido.moneda,
        "items": items,
        "total": format(pedido.total, ".2f"),
    }


def _recibir_linea_tcp(
    conexion: socket.socket,
) -> bytes:
    """
    Recibe un mensaje TCP hasta encontrar un salto de línea.

    TCP es un flujo de bytes, por lo que no debemos asumir
    que cada recv() contiene un mensaje completo.
    """

    buffer = bytearray()

    while True:

        espacio_restante = TCP_MAX_MESSAGE_BYTES - len(buffer) + 1

        bloque = conexion.recv(
            min(4096, espacio_restante)
        )

        if not bloque:
            raise ErrorServicioExterno(
                servicio="caja",
                codigo="CONEXION_CERRADA",
                mensaje="Caja cerró la conexión antes de responder.",
            )

        buffer.extend(bloque)

        posicion = buffer.find(b"\n")

        if posicion >= 0:

            mensaje = bytes(buffer[:posicion])
            datos_adicionales = bytes(buffer[posicion + 1:])

            if len(mensaje) > TCP_MAX_MESSAGE_BYTES:
                raise ErrorServicioExterno(
                    servicio="caja",
                    codigo="MENSAJE_DEMASIADO_GRANDE",
                    mensaje="La respuesta TCP supera el tamaño permitido.",
                    reintentable=False,
                )

            if datos_adicionales.strip():
                raise ErrorServicioExterno(
                    servicio="caja",
                    codigo="RESPUESTA_TCP_INVALIDA",
                    mensaje="Se recibieron datos adicionales inesperados.",
                    reintentable=False,
                )

            return mensaje

        if len(buffer) > TCP_MAX_MESSAGE_BYTES:
            raise ErrorServicioExterno(
                servicio="caja",
                codigo="MENSAJE_DEMASIADO_GRANDE",
                mensaje="La respuesta TCP supera el tamaño permitido.",
                reintentable=False,
            )


def enviar_venta_tcp(
    pedido: PedidoRespuesta,
) -> dict[str, Any]:
    """
    Se conecta al servidor TCP de caja, envía la venta
    y devuelve la respuesta recibida.

    Los errores de comunicación se convierten en
    ErrorServicioExterno para facilitar su tratamiento
    desde la API.
    """

    solicitud = construir_solicitud_venta(pedido)

    mensaje = (
        json.dumps(
            solicitud,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )

    if len(mensaje) - 1 > TCP_MAX_MESSAGE_BYTES:
        raise ErrorServicioExterno(
            servicio="caja",
            codigo="SOLICITUD_DEMASIADO_GRANDE",
            mensaje="El pedido supera el tamaño máximo permitido.",
            reintentable=False,
        )

    try:

        with socket.create_connection(
            (TCP_HOST, TCP_PORT),
            timeout=TCP_TIMEOUT_SECONDS,
        ) as conexion:

            conexion.settimeout(TCP_TIMEOUT_SECONDS)

            # Enviar la solicitud completa.
            conexion.sendall(mensaje)

            # Esperar la respuesta delimitada por salto de línea.
            respuesta_bytes = _recibir_linea_tcp(conexion)

    except socket.timeout as error:

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="TIMEOUT_TCP",
            mensaje="Caja no respondió dentro del tiempo establecido.",
        ) from error

    except OSError as error:

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="ERROR_CONEXION_TCP",
            mensaje=f"No fue posible comunicarse con caja: {error}",
        ) from error

    # Interpretar la respuesta recibida.
    try:

        respuesta = json.loads(
            respuesta_bytes.decode("utf-8")
        )

    except (UnicodeDecodeError, json.JSONDecodeError) as error:

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="RESPUESTA_TCP_INVALIDA",
            mensaje="Caja devolvió una respuesta JSON inválida.",
            reintentable=False,
        ) from error

    # Verificar la estructura de la respuesta.
    if not isinstance(respuesta, dict):

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="FORMATO_TCP_INVALIDO",
            mensaje="La respuesta de caja no tiene el formato esperado.",
            reintentable=False,
        )

    operacion_esperada = solicitud["operacion_id"]

    if (
        respuesta.get("operacion_id") != operacion_esperada
        or respuesta.get("pedido_id") != str(pedido.pedido_id)
        or not isinstance(respuesta.get("ok"), bool)
    ):

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="RESPUESTA_TCP_INCONSISTENTE",
            mensaje="La respuesta de caja no corresponde al pedido enviado.",
            reintentable=False,
        )

    if respuesta.get("ok"):

        if respuesta.get("tipo") != "VENTA_CONFIRMADA":
            raise ErrorServicioExterno(
                servicio="caja",
                codigo="RESPUESTA_TCP_INCONSISTENTE",
                mensaje="Caja devolvió un tipo de confirmación inesperado.",
                reintentable=False,
            )

    elif respuesta.get("tipo") != "ERROR_CAJA":

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="RESPUESTA_TCP_INCONSISTENTE",
            mensaje="Caja devolvió un tipo de error inesperado.",
            reintentable=False,
        )

    # Una respuesta negativa de caja es un resultado de negocio,
    # no un error de conexión. La API decidirá cómo actualizar
    # el estado del pedido.
    return respuesta


# 3. TRANSPORTES XML-RPC CON TIMEOUT

class TransporteRPCConTimeout(xmlrpc.client.Transport):
    """
    Configura un tiempo máximo de espera para conexiones HTTP
    utilizadas por XML-RPC.
    """

    def __init__(self, timeout: float):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host: str):
        conexion = super().make_connection(host)
        conexion.timeout = self.timeout
        return conexion


class TransporteSeguroRPCConTimeout(xmlrpc.client.SafeTransport):
    """
    Variante para servidores XML-RPC que utilicen HTTPS.
    """

    def __init__(self, timeout: float):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host: str):
        conexion = super().make_connection(host)
        conexion.timeout = self.timeout
        return conexion


# 4. CLIENTE XML-RPC: COCINA

def preparar_pedido_rpc(
    pedido_id: UUID | str,
    productos: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Invoca la función remota preparar_pedido() del servidor
    XML-RPC de cocina.

    Los productos se envían con identificador, nombre y cantidad.
    """

    pedido_id_texto = str(pedido_id)

    # Preparar los datos compatibles con XML-RPC.
    productos_rpc = []

    for producto in productos:

        if not isinstance(producto, dict):
            raise ValueError(
                "Cada producto debe ser un diccionario."
            )

        producto_id = producto.get("producto_id")
        nombre = producto.get("nombre")
        cantidad = producto.get("cantidad")

        if not isinstance(producto_id, str) or not producto_id.strip():
            raise ValueError("El producto necesita un producto_id válido.")

        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El producto necesita un nombre válido.")

        if (
            isinstance(cantidad, bool)
            or not isinstance(cantidad, int)
            or cantidad <= 0
        ):
            raise ValueError("La cantidad del producto debe ser positiva.")

        productos_rpc.append({
            "producto_id": producto_id,
            "nombre": nombre,
            "cantidad": cantidad,
        })

    # Elegir transporte HTTP o HTTPS.
    if RPC_URL.startswith("https://"):
        transporte = TransporteSeguroRPCConTimeout(
            RPC_TIMEOUT_SECONDS
        )
    else:
        transporte = TransporteRPCConTimeout(
            RPC_TIMEOUT_SECONDS
        )

    try:

        with xmlrpc.client.ServerProxy(
            RPC_URL,
            transport=transporte,
            allow_none=False,
        ) as servidor:

            respuesta = servidor.preparar_pedido(
                pedido_id_texto,
                productos_rpc,
            )

    except xmlrpc.client.Fault as error:

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="ERROR_RPC_REMOTO",
            mensaje=f"Cocina devolvió un error RPC: {error.faultString}",
            reintentable=False,
        ) from error

    except (socket.timeout, TimeoutError) as error:

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="TIMEOUT_RPC",
            mensaje="Cocina no respondió dentro del tiempo establecido.",
        ) from error

    except (OSError, HTTPException, xmlrpc.client.ProtocolError) as error:

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="ERROR_CONEXION_RPC",
            mensaje=f"No fue posible comunicarse con cocina: {error}",
        ) from error

    except xmlrpc.client.Error as error:

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="RESPUESTA_RPC_INVALIDA",
            mensaje=f"Cocina devolvió una respuesta RPC inválida: {error}",
            reintentable=False,
        ) from error

    # Verificar la respuesta de cocina.
    if not isinstance(respuesta, dict):

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="FORMATO_RPC_INVALIDO",
            mensaje="La respuesta de cocina no tiene el formato esperado.",
            reintentable=False,
        )

    if (
        respuesta.get("pedido_id") != pedido_id_texto
        or not isinstance(respuesta.get("ok"), bool)
    ):

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="RESPUESTA_RPC_INCONSISTENTE",
            mensaje="La respuesta de cocina no corresponde al pedido enviado.",
            reintentable=False,
        )

    estado_esperado = (
        "LISTO" if respuesta["ok"] else "ERROR_COCINA"
    )

    if respuesta.get("estado") != estado_esperado:

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="ESTADO_RPC_INVALIDO",
            mensaje="Cocina devolvió un estado inesperado.",
            reintentable=False,
        )

    return respuesta
