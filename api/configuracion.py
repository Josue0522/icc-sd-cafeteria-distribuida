
"""
Configuración de conexiones del sistema distribuido.

Los valores predeterminados se utilizan para desarrollo local.
Pueden modificarse mediante variables de entorno.
"""

import os


def obtener_entero(nombre: str, valor_defecto: int) -> int:
    """Obtiene una variable de entorno de tipo entero."""

    try:
        valor = int(os.getenv(nombre, str(valor_defecto)))
    except ValueError as error:
        raise ValueError(
            f"La variable {nombre} debe ser un número entero."
        ) from error

    return valor


def obtener_decimal(nombre: str, valor_defecto: float) -> float:
    """Obtiene una variable de entorno de tipo decimal."""

    try:
        valor = float(os.getenv(nombre, str(valor_defecto)))
    except ValueError as error:
        raise ValueError(
            f"La variable {nombre} debe ser numérica."
        ) from error

    if valor <= 0:
        raise ValueError(
            f"La variable {nombre} debe ser mayor que cero."
        )

    return valor


# Configuración del servicio TCP (Caja y facturación)

TCP_HOST = os.getenv("TCP_HOST", "127.0.0.1")

TCP_PORT = obtener_entero("TCP_PORT", 9001)

TCP_TIMEOUT_SECONDS = obtener_decimal(
    "TCP_TIMEOUT_SECONDS", 3.0
)

TCP_MAX_MESSAGE_BYTES = obtener_entero(
    "TCP_MAX_MESSAGE_BYTES", 65536
)


# Configuración del servicio RPC (Cocina)

RPC_URL = os.getenv(
    "RPC_URL",
    "http://127.0.0.1:9002"
)

RPC_TIMEOUT_SECONDS = obtener_decimal(
    "RPC_TIMEOUT_SECONDS", 15.0
)


# Validaciones de configuración

if not TCP_HOST.strip():
    raise ValueError("TCP_HOST no puede estar vacío.")

if not 1 <= TCP_PORT <= 65535:
    raise ValueError("TCP_PORT debe estar entre 1 y 65535.")

if TCP_MAX_MESSAGE_BYTES <= 0:
    raise ValueError("El tamaño máximo del mensaje debe ser positivo.")

if not RPC_URL.startswith(("http://", "https://")):
    raise ValueError("RPC_URL debe comenzar con http:// o https://")



# Configuración del servicio de notificaciones WebSocket

NOTIFICACIONES_WS_URL = os.getenv(
    "NOTIFICACIONES_WS_URL",
    "ws://127.0.0.1:9003/ws/interno/notificaciones"
)

NOTIFICACIONES_WS_TIMEOUT_SECONDS = obtener_decimal(
    "NOTIFICACIONES_WS_TIMEOUT_SECONDS", 3.0
)


if not NOTIFICACIONES_WS_URL.startswith(("ws://", "wss://")):
    raise ValueError(
        "NOTIFICACIONES_WS_URL debe comenzar con ws:// o wss://"
    )
