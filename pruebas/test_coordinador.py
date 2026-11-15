
"""
Pruebas automatizadas del coordinador de pedidos.

Se simulan las respuestas de TCP y XML-RPC para comprobar
el flujo sin necesitar los servidores de caja y cocina.
"""

import pytest

from uuid import uuid4

from api import almacen, coordinador

from api.modelos import (
    EstadoPedido,
    SolicitudCrearPedido,
)

from api.servicios import ErrorServicioExterno


# 1. Preparación del almacenamiento

@pytest.fixture(autouse=True)
def limpiar_almacen(monkeypatch):
    """
    Cada prueba comienza y termina con el almacenamiento vacío.
    """

    with almacen._bloqueo:
        almacen._pedidos.clear()
        almacen._idempotencia.clear()

    monkeypatch.setattr(
        coordinador,
        "publicar_estado_pedido",
        lambda pedido: True,
    )

    yield

    with almacen._bloqueo:
        almacen._pedidos.clear()
        almacen._idempotencia.clear()


# 2. Crear un pedido para las pruebas

def crear_pedido_prueba():

    solicitud = SolicitudCrearPedido(
        estudiante_id="EST-001",
        items=[
            {
                "producto_id": "CAF-001",
                "cantidad": 2
            }
        ]
    )

    pedido, es_nuevo = almacen.crear_pedido(
        solicitud,
        f"coordinador-{uuid4()}",
    )

    assert es_nuevo is True

    return pedido


# Prueba 1: procesamiento exitoso

def test_procesamiento_completo(monkeypatch):

    pedido = crear_pedido_prueba()

    llamadas_tcp = []
    llamadas_rpc = []
    estados_notificados = []

    def caja_simulada(pedido_recibido):

        llamadas_tcp.append(pedido_recibido.pedido_id)

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        llamadas_rpc.append(pedido_id)

        return {
            "ok": True,
            "pedido_id": str(pedido_id),
            "estado": "LISTO",
            "mensaje": "Pedido preparado correctamente",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "publicar_estado_pedido",
        lambda pedido: estados_notificados.append(
            pedido.estado.value
        ) or True,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.LISTO

    assert len(llamadas_tcp) == 1
    assert len(llamadas_rpc) == 1
    assert estados_notificados == [
        "VENTA_CONFIRMADA",
        "EN_PREPARACION",
        "LISTO",
    ]


# Prueba 2: caja rechaza la venta

def test_caja_rechaza_venta(monkeypatch):

    pedido = crear_pedido_prueba()

    llamadas_rpc = []

    def caja_simulada(pedido_recibido):

        return {
            "ok": False,
            "tipo": "ERROR_CAJA",
        }

    def cocina_simulada(pedido_id, productos):

        llamadas_rpc.append(pedido_id)

        pytest.fail(
            "No debe solicitarse preparación si caja rechaza la venta."
        )

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.ERROR_CAJA
    assert len(llamadas_rpc) == 0


# Prueba 3: caja no responde

def test_caja_no_responde(monkeypatch):

    pedido = crear_pedido_prueba()

    intentos = []

    def caja_simulada(pedido_recibido):

        intentos.append(pedido_recibido.pedido_id)

        raise ErrorServicioExterno(
            servicio="caja",
            codigo="TIMEOUT_TCP",
            mensaje="Caja no respondió.",
            reintentable=True,
        )

    def cocina_simulada(pedido_id, productos):

        pytest.fail(
            "No debe iniciarse la preparación sin confirmar caja."
        )

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert len(intentos) == 2
    assert resultado.estado == EstadoPedido.PENDIENTE_CAJA


# Prueba 4: cocina no responde

def test_cocina_no_responde(monkeypatch):

    pedido = crear_pedido_prueba()

    def caja_simulada(pedido_recibido):

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        raise ErrorServicioExterno(
            servicio="cocina",
            codigo="TIMEOUT_RPC",
            mensaje="Cocina no respondió.",
            reintentable=True,
        )

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    # No se supone que la preparación haya fallado.
    assert resultado.estado == EstadoPedido.EN_PREPARACION


# Prueba 5: cocina devuelve un error

def test_cocina_devuelve_error(monkeypatch):

    pedido = crear_pedido_prueba()

    def caja_simulada(pedido_recibido):

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        return {
            "ok": False,
            "pedido_id": str(pedido_id),
            "estado": "ERROR_COCINA",
            "mensaje": "No se pudo preparar el pedido.",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.ERROR_COCINA


# Prueba 6: recuperar un pedido pendiente de caja

def test_recuperar_pedido_pendiente(monkeypatch):

    pedido = crear_pedido_prueba()

    # Simular que anteriormente caja no respondió.
    almacen.actualizar_estado(
        pedido.pedido_id,
        EstadoPedido.PENDIENTE_CAJA,
    )

    def caja_simulada(pedido_recibido):

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        return {
            "ok": True,
            "pedido_id": str(pedido_id),
            "estado": "LISTO",
            "mensaje": "Pedido preparado correctamente",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.LISTO


# Prueba 7: no procesar dos veces un pedido terminado

def test_no_reprocesar_pedido_terminado(monkeypatch):

    pedido = crear_pedido_prueba()

    llamadas_tcp = []
    llamadas_rpc = []

    def caja_simulada(pedido_recibido):

        llamadas_tcp.append(pedido_recibido.pedido_id)

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        llamadas_rpc.append(pedido_id)

        return {
            "ok": True,
            "pedido_id": str(pedido_id),
            "estado": "LISTO",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    # Primera ejecución.
    coordinador.procesar_pedido(pedido.pedido_id)

    # Segunda ejecución del mismo pedido.
    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.LISTO

    # No se deben repetir las llamadas externas.
    assert len(llamadas_tcp) == 1
    assert len(llamadas_rpc) == 1



# Prueba 8: recuperar EN_PREPARACION sin repetir la venta

def test_recuperar_preparacion_sin_repetir_venta(monkeypatch):

    pedido = crear_pedido_prueba()

    # Simular que caja ya confirmó la venta.
    almacen.actualizar_estado(
        pedido.pedido_id,
        EstadoPedido.VENTA_CONFIRMADA,
    )

    almacen.actualizar_estado(
        pedido.pedido_id,
        EstadoPedido.EN_PREPARACION,
    )

    llamadas_tcp = []
    llamadas_rpc = []

    def caja_simulada(pedido_recibido):
        llamadas_tcp.append(pedido_recibido.pedido_id)

        pytest.fail(
            "No se debe volver a contactar con caja."
        )

    def cocina_simulada(pedido_id, productos):
        llamadas_rpc.append(pedido_id)

        return {
            "ok": True,
            "pedido_id": str(pedido_id),
            "estado": "LISTO",
            "mensaje": "Pedido preparado correctamente",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.LISTO
    assert len(llamadas_tcp) == 0
    assert len(llamadas_rpc) == 1


# Prueba 9: no recuperar un pedido terminado

def test_no_recuperar_pedido_terminado(monkeypatch):

    pedido = crear_pedido_prueba()

    almacen.actualizar_estado(
        pedido.pedido_id,
        EstadoPedido.ERROR_CAJA,
    )

    def servicio_no_disponible(*args, **kwargs):
        pytest.fail(
            "No deben ejecutarse servicios para un pedido terminado."
        )

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        servicio_no_disponible,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        servicio_no_disponible,
    )

    resultado = coordinador.recuperar_pedido(
        pedido.pedido_id
    )

    assert resultado is False

    pedido_actual = almacen.obtener_pedido(pedido.pedido_id)

    assert pedido_actual.estado == EstadoPedido.ERROR_CAJA


# Prueba 10: listar los pedidos recuperables

def test_listar_pedidos_recuperables():

    pedido_recibido = crear_pedido_prueba()
    pedido_caja = crear_pedido_prueba()
    pedido_rpc = crear_pedido_prueba()
    pedido_finalizado = crear_pedido_prueba()

    # Preparar los distintos estados.
    almacen.actualizar_estado(
        pedido_caja.pedido_id,
        EstadoPedido.PENDIENTE_CAJA,
    )

    almacen.actualizar_estado(
        pedido_rpc.pedido_id,
        EstadoPedido.VENTA_CONFIRMADA,
    )

    almacen.actualizar_estado(
        pedido_rpc.pedido_id,
        EstadoPedido.EN_PREPARACION,
    )

    almacen.actualizar_estado(
        pedido_finalizado.pedido_id,
        EstadoPedido.ERROR_CAJA,
    )

    recuperables = coordinador.listar_pedidos_recuperables()

    assert set(recuperables) == {
        pedido_recibido.pedido_id,
        pedido_caja.pedido_id,
        pedido_rpc.pedido_id,
    }

    assert pedido_finalizado.pedido_id not in recuperables


# Prueba 11: impedir procesamiento simultáneo

def test_evitar_procesamiento_simultaneo(monkeypatch):

    pedido = crear_pedido_prueba()

    llamadas_tcp = []
    llamadas_rpc = []

    def caja_simulada(pedido_recibido):

        llamadas_tcp.append(pedido_recibido.pedido_id)

        # Intentar procesar nuevamente el mismo pedido
        # mientras el primer procesamiento sigue activo.
        coordinador.procesar_pedido(
            pedido_recibido.pedido_id
        )

        return {
            "ok": True,
            "tipo": "VENTA_CONFIRMADA",
        }

    def cocina_simulada(pedido_id, productos):

        llamadas_rpc.append(pedido_id)

        return {
            "ok": True,
            "pedido_id": str(pedido_id),
            "estado": "LISTO",
            "mensaje": "Pedido preparado correctamente",
        }

    monkeypatch.setattr(
        coordinador,
        "enviar_venta_tcp",
        caja_simulada,
    )

    monkeypatch.setattr(
        coordinador,
        "preparar_pedido_rpc",
        cocina_simulada,
    )

    coordinador.procesar_pedido(pedido.pedido_id)

    resultado = almacen.obtener_pedido(pedido.pedido_id)

    assert resultado.estado == EstadoPedido.LISTO
    assert len(llamadas_tcp) == 1
    assert len(llamadas_rpc) == 1
