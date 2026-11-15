"""Pruebas del servidor TCP de caja, preparadas con asistencia de Codex."""

from __future__ import annotations

import json
import socket
import threading
import time
from uuid import uuid4

import pytest

from caja_facturacion.protocolo import codificar_mensaje
from caja_facturacion.servidor_tcp import crear_servidor


@pytest.fixture
def servidor_tcp():
    servidor = crear_servidor("127.0.0.1", 0, timeout_cliente=0.5)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=2)


def solicitud_valida() -> dict:
    pedido_id = str(uuid4())
    return {
        "version": 1,
        "tipo": "REGISTRAR_VENTA",
        "operacion_id": f"VENTA-{pedido_id}",
        "pedido_id": pedido_id,
        "moneda": "USD",
        "items": [
            {
                "producto_id": "CAF-001",
                "nombre": "Café americano",
                "cantidad": 2,
                "precio_unitario": "1.50",
                "subtotal": "3.00",
            }
        ],
        "total": "3.00",
    }


def intercambiar(direccion: tuple[str, int], datos: dict) -> dict:
    with socket.create_connection(direccion, timeout=1) as cliente:
        cliente.settimeout(1)
        cliente.sendall(codificar_mensaje(datos))
        respuesta = bytearray()
        while not respuesta.endswith(b"\n"):
            bloque = cliente.recv(4096)
            if not bloque:
                break
            respuesta.extend(bloque)
    return json.loads(respuesta.decode("utf-8"))


def test_venta_correcta_devuelve_comprobante_en_centavos(servidor_tcp):
    solicitud = solicitud_valida()
    respuesta = intercambiar(servidor_tcp.server_address, solicitud)

    assert respuesta["ok"] is True
    assert respuesta["tipo"] == "VENTA_CONFIRMADA"
    assert respuesta["operacion_id"] == solicitud["operacion_id"]
    assert respuesta["pedido_id"] == solicitud["pedido_id"]
    assert respuesta["comprobante"]["total_centavos"] == 300
    assert servidor_tcp.registro.cantidad_ventas == 1


def test_misma_operacion_devuelve_el_resultado_original(servidor_tcp):
    solicitud = solicitud_valida()

    primera = intercambiar(servidor_tcp.server_address, solicitud)
    segunda = intercambiar(servidor_tcp.server_address, solicitud)

    assert segunda == primera
    assert servidor_tcp.registro.cantidad_ventas == 1


def test_operacion_reutilizada_con_contenido_distinto_se_rechaza(servidor_tcp):
    solicitud = solicitud_valida()
    intercambiar(servidor_tcp.server_address, solicitud)
    solicitud["items"][0]["cantidad"] = 3
    solicitud["items"][0]["subtotal"] = "4.50"
    solicitud["total"] = "4.50"

    respuesta = intercambiar(servidor_tcp.server_address, solicitud)

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "OPERACION_ID_REUTILIZADO"
    assert servidor_tcp.registro.cantidad_ventas == 1


def test_json_invalido_devuelve_error_y_servidor_sigue_activo(servidor_tcp):
    with socket.create_connection(servidor_tcp.server_address, timeout=1) as cliente:
        cliente.settimeout(1)
        cliente.sendall(b"{json roto}\n")
        with cliente.makefile("rb") as entrada:
            respuesta = json.loads(entrada.readline().decode("utf-8"))

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "JSON_INVALIDO"

    buena = intercambiar(servidor_tcp.server_address, solicitud_valida())
    assert buena["ok"] is True


def test_importe_incorrecto_se_rechaza(servidor_tcp):
    solicitud = solicitud_valida()
    solicitud["items"][0]["precio_unitario"] = "1.005"

    respuesta = intercambiar(servidor_tcp.server_address, solicitud)

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "IMPORTE_INVALIDO"
    assert servidor_tcp.registro.cantidad_ventas == 0


def test_cliente_desconectado_no_detiene_el_servidor(servidor_tcp):
    with socket.create_connection(servidor_tcp.server_address, timeout=1) as cliente:
        cliente.sendall(b'{"version":1')

    time.sleep(0.05)
    respuesta = intercambiar(servidor_tcp.server_address, solicitud_valida())

    assert respuesta["ok"] is True


def test_puerto_sin_servidor_reporta_servicio_no_disponible():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temporal:
        temporal.bind(("127.0.0.1", 0))
        direccion = temporal.getsockname()

    with pytest.raises(OSError):
        socket.create_connection(direccion, timeout=0.2)
