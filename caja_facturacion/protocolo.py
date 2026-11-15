"""Protocolo JSON por línea usado entre la API y caja.

Preparado con asistencia de Codex para revisión del equipo.
"""

from __future__ import annotations

import json
from typing import Any


MAX_MESSAGE_BYTES = 65_536


class ErrorProtocolo(ValueError):
    """Error de encuadre, codificación o estructura del mensaje."""

    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def codificar_mensaje(mensaje: dict[str, Any]) -> bytes:
    """Serializa un objeto JSON UTF-8 y añade el delimitador de línea."""
    try:
        contenido = json.dumps(
            mensaje,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ErrorProtocolo("JSON_NO_SERIALIZABLE", "No se pudo serializar el mensaje.") from error

    if len(contenido) > MAX_MESSAGE_BYTES:
        raise ErrorProtocolo("MENSAJE_DEMASIADO_GRANDE", "El mensaje supera el límite permitido.")
    return contenido + b"\n"


def decodificar_mensaje(datos: bytes) -> dict[str, Any]:
    """Decodifica exactamente un objeto JSON terminado en salto de línea."""
    if len(datos) > MAX_MESSAGE_BYTES + 1:
        raise ErrorProtocolo("MENSAJE_DEMASIADO_GRANDE", "El mensaje supera el límite permitido.")
    if not datos.endswith(b"\n"):
        raise ErrorProtocolo("MENSAJE_INCOMPLETO", "El mensaje debe terminar con salto de línea.")

    contenido = datos[:-1]
    if b"\n" in contenido:
        raise ErrorProtocolo("MENSAJES_MULTIPLES", "Se admite un solo mensaje por conexión.")

    try:
        texto = contenido.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ErrorProtocolo("UTF8_INVALIDO", "El mensaje debe usar codificación UTF-8.") from error

    try:
        mensaje = json.loads(texto)
    except json.JSONDecodeError as error:
        raise ErrorProtocolo("JSON_INVALIDO", "El mensaje no contiene JSON válido.") from error

    if not isinstance(mensaje, dict):
        raise ErrorProtocolo("JSON_INVALIDO", "El mensaje JSON debe ser un objeto.")
    return mensaje


def crear_respuesta_error_protocolo(error: ErrorProtocolo) -> dict[str, Any]:
    """Crea una respuesta de error con el formato común de caja."""
    return {
        "ok": False,
        "tipo": "ERROR_CAJA",
        "operacion_id": None,
        "pedido_id": None,
        "error": {
            "codigo": error.codigo,
            "mensaje": error.mensaje,
            "reintentable": False,
        },
    }
