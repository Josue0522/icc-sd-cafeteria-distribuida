import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from xmlrpc.client import ServerProxy

from cocina.servidor_rpc import ServicioCocina, crear_servidor
from api import servicios


PRODUCTOS = [{"producto_id": "CAF-001", "nombre": "Café americano", "cantidad": 2}]


@pytest.fixture
def servidor_rpc():
    servidor, cocina = crear_servidor(puerto=0, segundos_preparacion=0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}", cocina
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=3)


def test_preparacion_exitosa():
    servicio = ServicioCocina(segundos_preparacion=0)
    pedido_id = str(uuid4())
    respuesta = servicio.preparar_pedido(pedido_id, PRODUCTOS)
    assert respuesta["pedido_id"] == pedido_id
    assert respuesta["estado"] == "LISTO"
    assert respuesta["ok"] is True
    assert servicio.preparaciones_iniciadas == 1


def test_idempotencia_secuencial():
    servicio = ServicioCocina(segundos_preparacion=0)
    pedido_id = str(uuid4())
    servicio.preparar_pedido(pedido_id, PRODUCTOS)
    repetido = servicio.preparar_pedido(pedido_id, PRODUCTOS)
    assert repetido["duplicado"] is True
    assert servicio.preparaciones_iniciadas == 1


def test_mismo_id_con_productos_diferentes():
    servicio = ServicioCocina(segundos_preparacion=0)
    pedido_id = str(uuid4())
    servicio.preparar_pedido(pedido_id, PRODUCTOS)
    otro = [{"producto_id": "SAN-001", "nombre": "Sándwich", "cantidad": 1}]
    respuesta = servicio.preparar_pedido(pedido_id, otro)
    assert respuesta["ok"] is False
    assert respuesta["codigo"] == "PEDIDO_INCONSISTENTE"
    assert servicio.preparaciones_iniciadas == 1


@pytest.mark.parametrize("productos", [
    [],
    [{"producto_id": "CAF-001", "nombre": "Café", "cantidad": 0}],
    [{"producto_id": "CAF-001", "nombre": "Café", "cantidad": True}],
    [{"producto_id": "", "nombre": "Café", "cantidad": 2}],
    [{"producto_id": "CAF-001", "cantidad": 2}],
])
def test_productos_invalidos(productos):
    servicio = ServicioCocina(segundos_preparacion=0)
    respuesta = servicio.preparar_pedido(str(uuid4()), productos)
    assert respuesta["ok"] is False
    assert respuesta["estado"] == "ERROR_COCINA"
    assert servicio.preparaciones_iniciadas == 0


def test_uuid_invalido():
    servicio = ServicioCocina(segundos_preparacion=0)
    respuesta = servicio.preparar_pedido("123", PRODUCTOS)
    assert respuesta["codigo"] == "PEDIDO_INVALIDO"


def test_concurrencia_mismo_pedido_no_duplica():
    servicio = ServicioCocina(segundos_preparacion=0.02)
    pedido_id = str(uuid4())
    with ThreadPoolExecutor(max_workers=3) as pool:
        resultados = list(pool.map(lambda _: servicio.preparar_pedido(pedido_id, PRODUCTOS), range(3)))
    assert all(r["estado"] == "LISTO" for r in resultados)
    assert sum(r["duplicado"] for r in resultados) == 2
    assert servicio.preparaciones_iniciadas == 1


def test_error_controlado():
    servicio = ServicioCocina(segundos_preparacion=0, simular_error=True)
    pedido_id = str(uuid4())
    respuesta = servicio.preparar_pedido(pedido_id, PRODUCTOS)
    assert respuesta["ok"] is False
    assert respuesta["estado"] == "ERROR_COCINA"
    assert servicio.consultar_pedido(pedido_id)["estado"] == "ERROR_COCINA"


def test_consulta_de_estado():
    servicio = ServicioCocina(segundos_preparacion=0)
    pedido_id = str(uuid4())
    assert servicio.consultar_pedido(pedido_id)["codigo"] == "NO_ENCONTRADO"
    servicio.preparar_pedido(pedido_id, PRODUCTOS)
    assert servicio.consultar_pedido(pedido_id)["estado"] == "LISTO"


def test_rpc_red_y_cliente_de_mateo(monkeypatch, servidor_rpc):
    url, cocina = servidor_rpc
    monkeypatch.setattr(servicios, "RPC_URL", url)
    with ServerProxy(url) as rpc:
        assert rpc.ping()["ok"] is True
    pedido_id = str(uuid4())
    respuesta = servicios.preparar_pedido_rpc(pedido_id, PRODUCTOS)
    assert respuesta["pedido_id"] == pedido_id
    assert respuesta["estado"] == "LISTO"
    assert cocina.preparaciones_iniciadas == 1


def test_respuesta_repetida_por_red(monkeypatch, servidor_rpc):
    url, cocina = servidor_rpc
    monkeypatch.setattr(servicios, "RPC_URL", url)
    pedido_id = str(uuid4())
    primera = servicios.preparar_pedido_rpc(pedido_id, PRODUCTOS)
    segunda = servicios.preparar_pedido_rpc(pedido_id, PRODUCTOS)
    assert primera["duplicado"] is False
    assert segunda["duplicado"] is True
    assert cocina.preparaciones_iniciadas == 1


def test_error_rpc_validado_por_cliente_mateo(monkeypatch):
    servidor, _ = crear_servidor(puerto=0, segundos_preparacion=0, simular_error=True)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    monkeypatch.setattr(servicios, "RPC_URL", f"http://127.0.0.1:{servidor.server_address[1]}")
    try:
        resultado = servicios.preparar_pedido_rpc(str(uuid4()), PRODUCTOS)
        assert resultado["ok"] is False
        assert resultado["estado"] == "ERROR_COCINA"
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=3)


def test_pedido_completo_con_coordinador_de_mateo(monkeypatch, servidor_rpc):
    from api import almacen, coordinador
    from api.modelos import EstadoPedido, SolicitudCrearPedido

    url, cocina = servidor_rpc
    monkeypatch.setattr(servicios, "RPC_URL", url)
    monkeypatch.setattr(coordinador, "publicar_estado_pedido", lambda _pedido: True)
    monkeypatch.setattr(
        coordinador, "enviar_venta_tcp",
        lambda _pedido: {"ok": True, "tipo": "VENTA_CONFIRMADA"},
    )
    # Aquí la única parte simulada es Caja TCP y las notificaciones;
    # Cocina es un servidor XML-RPC real en un hilo independiente.
    pedido, _ = almacen.crear_pedido(
        SolicitudCrearPedido(estudiante_id="EST-PRUEBA", items=[{"producto_id": "CAF-001", "cantidad": 2}]),
        f"rpc-{uuid4()}",
    )
    try:
        coordinador.procesar_pedido(pedido.pedido_id)
        assert almacen.obtener_pedido(pedido.pedido_id).estado == EstadoPedido.LISTO
        assert cocina.preparaciones_iniciadas == 1
    finally:
        with almacen._bloqueo:
            almacen._pedidos.pop(pedido.pedido_id, None)
            for clave, valor in list(almacen._idempotencia.items()):
                if valor[1] == pedido.pedido_id:
                    almacen._idempotencia.pop(clave, None)


def test_servicio_indisponible(monkeypatch):
    from api.servicios import ErrorServicioExterno

    servidor, _ = crear_servidor(puerto=0, segundos_preparacion=0)
    puerto = servidor.server_address[1]
    servidor.server_close()
    monkeypatch.setattr(servicios, "RPC_URL", f"http://127.0.0.1:{puerto}")
    monkeypatch.setattr(servicios, "RPC_TIMEOUT_SECONDS", 0.25)
    with pytest.raises(ErrorServicioExterno) as captura:
        servicios.preparar_pedido_rpc(str(uuid4()), PRODUCTOS)
    assert captura.value.codigo in {"ERROR_CONEXION_RPC", "TIMEOUT_RPC"}
