
"""
Pruebas automatizadas del módulo REST.

Se utiliza TestClient para probar FastAPI sin iniciar
un servidor Uvicorn independiente.
"""

import pytest

from fastapi.testclient import TestClient

from api.main import app
from api import almacen
from api.modelos import EstadoPedido

import api.main as modulo_main


# Cliente de pruebas de FastAPI.
client = TestClient(app)


# Preparación: limpiar el almacenamiento entre pruebas


@pytest.fixture(autouse=True)
def limpiar_almacen(monkeypatch):
    """
    Cada prueba comienza con almacenamiento vacío.

    Se sustituye temporalmente el coordinador para que
    las pruebas REST no dependan de servidores externos
    que todavía no están implementados.
    """

    monkeypatch.setattr(
        modulo_main,
        "procesar_pedido",
        lambda pedido_id: None,
    )

    monkeypatch.setattr(
        modulo_main,
        "publicar_estado_pedido",
        lambda pedido: True,
    )

    with almacen._bloqueo:
        almacen._pedidos.clear()
        almacen._idempotencia.clear()

    yield



# Datos de prueba

def crear_solicitud():
    return {
        "estudiante_id": "EST-001",
        "items": [
            {
                "producto_id": "CAF-001",
                "cantidad": 2
            }
        ],
        "observaciones": "Sin azúcar"
    }


# Prueba 1: creación correcta de un pedido

def test_crear_pedido_correctamente():

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-001"},
        json=crear_solicitud()
    )

    assert respuesta.status_code == 202

    datos = respuesta.json()

    assert datos["estudiante_id"] == "EST-001"
    assert datos["estado"] == "RECIBIDO"
    assert datos["items"][0]["cantidad"] == 2
    assert datos["total"] == "3.00"


# Prueba 2: evitar pedidos duplicados

def test_idempotencia_mismo_pedido():

    solicitud = crear_solicitud()
    headers = {"Idempotency-Key": "test-002"}

    primera = client.post(
        "/pedidos",
        headers=headers,
        json=solicitud
    )

    segunda = client.post(
        "/pedidos",
        headers=headers,
        json=solicitud
    )

    assert primera.status_code == 202
    assert segunda.status_code == 200

    assert (
        primera.json()["pedido_id"]
        == segunda.json()["pedido_id"]
    )


# Prueba 3: misma clave con datos diferentes

def test_conflicto_idempotencia():

    client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-003"},
        json=crear_solicitud()
    )

    solicitud_diferente = {
        "estudiante_id": "EST-001",
        "items": [
            {
                "producto_id": "SAN-001",
                "cantidad": 1
            }
        ]
    }

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-003"},
        json=solicitud_diferente
    )

    assert respuesta.status_code == 409

    assert (
        respuesta.json()["error"]["codigo"]
        == "CONFLICTO_IDEMPOTENCIA"
    )


# Prueba 4: producto inexistente

def test_producto_inexistente():

    solicitud = {
        "estudiante_id": "EST-001",
        "items": [
            {
                "producto_id": "PRODUCTO-999",
                "cantidad": 1
            }
        ]
    }

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-004"},
        json=solicitud
    )

    assert respuesta.status_code == 422

    assert (
        respuesta.json()["error"]["codigo"]
        == "PRODUCTO_NO_ENCONTRADO"
    )


# Prueba 5: cantidad inválida

def test_cantidad_invalida():

    solicitud = {
        "estudiante_id": "EST-001",
        "items": [
            {
                "producto_id": "CAF-001",
                "cantidad": 0
            }
        ]
    }

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-005"},
        json=solicitud
    )

    assert respuesta.status_code == 422


# Prueba 6: consultar un pedido existente

def test_consultar_pedido():

    creacion = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-006"},
        json=crear_solicitud()
    )

    pedido_id = creacion.json()["pedido_id"]

    respuesta = client.get(
        f"/pedidos/{pedido_id}"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["pedido_id"] == pedido_id
    assert respuesta.json()["estado"] == "RECIBIDO"


# Prueba 7: consultar un pedido inexistente

def test_pedido_no_encontrado():

    respuesta = client.get(
        "/pedidos/550e8400-e29b-41d4-a716-446655440000"
    )

    assert respuesta.status_code == 404


# Prueba 8: generar estadísticas

def test_estadisticas_de_pedidos():

    client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-008"},
        json=crear_solicitud()
    )

    respuesta = client.get("/reportes/ventas")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["total_pedidos"] == 1
    assert datos["pedidos_por_estado"]["RECIBIDO"] == 1
    assert datos["ventas_confirmadas"] == 0
    assert datos["ingresos_totales"] == "0.00"


# Prueba 9: rango de fechas incorrecto

def test_rango_fechas_invalido():

    respuesta = client.get(
        "/reportes/ventas",
        params={
            "desde": "2026-11-15",
            "hasta": "2026-11-14"
        }
    )

    assert respuesta.status_code == 400



# Prueba 10: transiciones válidas

def test_transiciones_validas():

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-010"},
        json=crear_solicitud()
    )

    pedido_id = __import__("uuid").UUID(
        respuesta.json()["pedido_id"]
    )

    # Recibido -> Venta confirmada.
    pedido = almacen.actualizar_estado(
        pedido_id,
        EstadoPedido.VENTA_CONFIRMADA
    )
    assert pedido.estado == EstadoPedido.VENTA_CONFIRMADA

    # Venta confirmada -> En preparación.
    pedido = almacen.actualizar_estado(
        pedido_id,
        EstadoPedido.EN_PREPARACION
    )
    assert pedido.estado == EstadoPedido.EN_PREPARACION

    # En preparación -> Listo.
    pedido = almacen.actualizar_estado(
        pedido_id,
        EstadoPedido.LISTO
    )
    assert pedido.estado == EstadoPedido.LISTO


# Prueba 11: rechazar una transición no permitida

def test_rechazar_salto_de_estado():

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-011"},
        json=crear_solicitud()
    )

    pedido_id = __import__("uuid").UUID(
        respuesta.json()["pedido_id"]
    )

    # No se permite pasar directamente de RECIBIDO a LISTO.
    with pytest.raises(almacen.TransicionEstadoInvalida):
        almacen.actualizar_estado(
            pedido_id,
            EstadoPedido.LISTO
        )

    # El pedido debe conservar su estado original.
    pedido = almacen.obtener_pedido(pedido_id)

    assert pedido.estado == EstadoPedido.RECIBIDO


# Prueba 12: repetir una actualización de estado

def test_repetir_estado_sin_modificar_pedido():

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-012"},
        json=crear_solicitud()
    )

    pedido_id = __import__("uuid").UUID(
        respuesta.json()["pedido_id"]
    )

    original = almacen.obtener_pedido(pedido_id)

    actualizado = almacen.actualizar_estado(
        pedido_id,
        EstadoPedido.RECIBIDO
    )

    assert actualizado.estado == EstadoPedido.RECIBIDO
    assert actualizado.actualizado_en == original.actualizado_en



# Prueba 13: crear un pedido programa el coordinador

def test_crear_pedido_programa_coordinador(monkeypatch):

    llamadas = []

    def coordinador_simulado(pedido_id):
        llamadas.append(pedido_id)

    # Sustituir temporalmente el coordinador real.
    monkeypatch.setattr(
        modulo_main,
        "procesar_pedido",
        coordinador_simulado,
    )

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-013"},
        json=crear_solicitud(),
    )

    assert respuesta.status_code == 202

    # El coordinador debe ejecutarse una vez.
    assert len(llamadas) == 1

    # Debe recibir el UUID del pedido creado.
    assert str(llamadas[0]) == respuesta.json()["pedido_id"]


# Prueba 14: un reintento no programa otro procesamiento

def test_reintento_no_programa_coordinador_dos_veces(monkeypatch):

    llamadas = []

    def coordinador_simulado(pedido_id):
        llamadas.append(pedido_id)

    monkeypatch.setattr(
        modulo_main,
        "procesar_pedido",
        coordinador_simulado,
    )

    solicitud = crear_solicitud()
    headers = {"Idempotency-Key": "test-014"}

    primera = client.post(
        "/pedidos",
        headers=headers,
        json=solicitud,
    )

    segunda = client.post(
        "/pedidos",
        headers=headers,
        json=solicitud,
    )

    assert primera.status_code == 202
    assert segunda.status_code == 200

    # Solamente debe haberse programado una ejecución.
    assert len(llamadas) == 1

    assert (
        primera.json()["pedido_id"]
        == segunda.json()["pedido_id"]
    )


# Prueba 15: publicar el estado inicial RECIBIDO

def test_notificar_pedido_recibido(monkeypatch):

    eventos = []

    monkeypatch.setattr(
        modulo_main,
        "publicar_estado_pedido",
        lambda pedido: eventos.append(
            pedido.estado.value
        ) or True,
    )

    respuesta = client.post(
        "/pedidos",
        headers={"Idempotency-Key": "test-015"},
        json=crear_solicitud(),
    )

    assert respuesta.status_code == 202

    assert eventos == ["RECIBIDO"]
