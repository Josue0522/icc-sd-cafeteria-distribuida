
"""
Pruebas del cliente WebSocket utilizado por la API REST.
"""

import json

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import api.notificaciones_cliente as notificaciones_cliente

from api.modelos import (
    PedidoRespuesta,
    EstadoPedido,
)


# 1. Crear un pedido de prueba

def crear_pedido_demo():

    ahora = datetime.now(timezone.utc)

    return PedidoRespuesta(
        pedido_id=uuid4(),
        estudiante_id="EST-001",
        estado=EstadoPedido.EN_PREPARACION,
        items=[],
        total=Decimal("0.00"),
        moneda="USD",
        observaciones=None,
        creado_en=ahora,
        actualizado_en=ahora,
    )


# Prueba 1: construir el evento correctamente

def test_construir_evento_estado():

    pedido = crear_pedido_demo()

    evento = notificaciones_cliente.construir_evento_estado(
        pedido
    )

    assert evento["tipo"] == "estado_actualizado"
    assert evento["pedido_id"] == str(pedido.pedido_id)
    assert evento["estado"] == "EN_PREPARACION"

    assert evento["mensaje"] == (
        "Tu pedido está siendo preparado."
    )

    assert evento["fecha"].endswith("Z")


# Prueba 2: publicar el evento correctamente

def test_publicar_evento_correctamente(monkeypatch):

    pedido = crear_pedido_demo()

    datos_enviados = {}

    class ConexionFalsa:

        def __enter__(self):
            return self

        def __exit__(self, tipo, valor, traceback):
            return False

        def send(self, mensaje):
            datos_enviados["mensaje"] = mensaje

    def conexion_simulada(url, **kwargs):

        datos_enviados["url"] = url
        datos_enviados["configuracion"] = kwargs

        return ConexionFalsa()

    monkeypatch.setattr(
        notificaciones_cliente,
        "connect",
        conexion_simulada,
    )

    resultado = notificaciones_cliente.publicar_estado_pedido(
        pedido
    )

    evento = json.loads(datos_enviados["mensaje"])

    assert resultado is True

    assert (
        evento["pedido_id"]
        == str(pedido.pedido_id)
    )

    assert evento["estado"] == "EN_PREPARACION"

    assert datos_enviados["url"].startswith("ws://")

    assert (
        datos_enviados["configuracion"]["proxy"]
        is None
    )


# Prueba 3: servicio de notificaciones no disponible

def test_notificacion_no_disponible(monkeypatch):

    pedido = crear_pedido_demo()

    def conexion_fallida(url, **kwargs):
        raise OSError(
            "Servidor de notificaciones no disponible."
        )

    monkeypatch.setattr(
        notificaciones_cliente,
        "connect",
        conexion_fallida,
    )

    resultado = notificaciones_cliente.publicar_estado_pedido(
        pedido
    )

    # La falla de notificaciones no debe lanzar una excepción.
    assert resultado is False
