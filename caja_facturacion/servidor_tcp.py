"""Servidor TCP de caja y facturación simulada.

Preparado con asistencia de Codex para revisión de Josué y del equipo.
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import socketserver
from typing import Any

from .comprobantes import RegistroVentas, respuesta_error
from .protocolo import (
    ErrorProtocolo,
    MAX_MESSAGE_BYTES,
    codificar_mensaje,
    crear_respuesta_error_protocolo,
    decodificar_mensaje,
)


LOG = logging.getLogger("caja_facturacion")


def _recibir_linea(conexion: socket.socket, limite: int) -> bytes | None:
    """Lee hasta el primer salto de línea sin asumir cómo se fragmenta TCP."""
    datos = bytearray()
    while len(datos) <= limite:
        bloque = conexion.recv(min(4096, limite + 2 - len(datos)))
        if not bloque:
            if not datos:
                return None
            raise ErrorProtocolo("MENSAJE_INCOMPLETO", "El cliente cerró la conexión antes del salto de línea.")

        posicion = bloque.find(b"\n")
        if posicion >= 0:
            datos.extend(bloque[:posicion + 1])
            if bloque[posicion + 1:].strip():
                raise ErrorProtocolo("MENSAJES_MULTIPLES", "Se admite una solicitud por conexión.")
            return bytes(datos)

        datos.extend(bloque)
        if len(datos) > limite:
            raise ErrorProtocolo("MENSAJE_DEMASIADO_GRANDE", "El mensaje supera el límite permitido.")

    raise ErrorProtocolo("MENSAJE_DEMASIADO_GRANDE", "El mensaje supera el límite permitido.")


class ServidorCaja(socketserver.ThreadingTCPServer):
    """Servidor concurrente; cada conexión atiende una sola venta."""

    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 32

    def __init__(
        self,
        direccion: tuple[str, int],
        registro: RegistroVentas | None = None,
        timeout_cliente: float = 3.0,
        max_message_bytes: int = MAX_MESSAGE_BYTES,
    ) -> None:
        self.registro = registro or RegistroVentas()
        self.timeout_cliente = timeout_cliente
        self.max_message_bytes = max_message_bytes
        super().__init__(direccion, ManejadorCaja)


class ManejadorCaja(socketserver.BaseRequestHandler):
    """Recibe JSON, delega la venta y devuelve una respuesta JSON."""

    def handle(self) -> None:
        self.request.settimeout(self.server.timeout_cliente)
        datos: dict[str, Any] = {}
        try:
            linea = _recibir_linea(self.request, self.server.max_message_bytes)
            if linea is None:
                return
            datos = decodificar_mensaje(linea)
            respuesta = self.server.registro.registrar(datos)
        except ErrorProtocolo as error:
            respuesta = crear_respuesta_error_protocolo(error)
        except socket.timeout:
            respuesta = respuesta_error(datos, "TIMEOUT_CLIENTE", "Se agotó el tiempo para recibir la solicitud.")
        except (ConnectionError, OSError) as error:
            LOG.info("Conexión TCP cerrada durante la atención: %s", error)
            return
        except Exception:
            LOG.exception("Error inesperado al procesar una conexión TCP.")
            respuesta = respuesta_error(datos, "ERROR_INTERNO", "Caja no pudo procesar la solicitud.")

        try:
            self.request.sendall(codificar_mensaje(respuesta))
        except (ConnectionError, OSError, ErrorProtocolo) as error:
            LOG.info("No se pudo devolver la respuesta al cliente: %s", error)


def crear_servidor(
    host: str | None = None,
    puerto: int | None = None,
    *,
    timeout_cliente: float = 3.0,
    registro: RegistroVentas | None = None,
) -> ServidorCaja:
    """Crea el servidor usando TCP_HOST/TCP_PORT o los valores por defecto."""
    host = host if host is not None else os.getenv("TCP_HOST", "127.0.0.1")
    if puerto is None:
        try:
            puerto = int(os.getenv("TCP_PORT", "9001"))
        except ValueError as error:
            raise ValueError("TCP_PORT debe ser un entero.") from error
    if not 0 <= puerto <= 65535:
        raise ValueError("El puerto debe estar entre 0 y 65535.")
    if timeout_cliente <= 0:
        raise ValueError("El timeout debe ser mayor que cero.")
    return ServidorCaja((host, puerto), registro, timeout_cliente)


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor TCP de caja de la cafetería")
    parser.add_argument("--host", default=None, help="Host (por defecto TCP_HOST o 127.0.0.1)")
    parser.add_argument("--puerto", type=int, default=None, help="Puerto (por defecto TCP_PORT o 9001)")
    argumentos = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with crear_servidor(argumentos.host, argumentos.puerto) as servidor:
        LOG.info("Caja TCP escuchando en %s:%s", *servidor.server_address)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            LOG.info("Cierre solicitado desde la consola.")


if __name__ == "__main__":
    main()
