
"""
Almacenamiento temporal de pedidos de la cafetería.

Administra el catálogo, los pedidos y las claves de idempotencia.

"""

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from threading import RLock
from uuid import UUID, uuid4

from .modelos import (
    EstadoPedido,
    ItemPedido,
    PedidoRespuesta,
    SolicitudCrearPedido,
    ReporteVentas,
)


# 1. Catálogo provisional de productos

# Estos productos son datos de demostración.

CATALOGO = {
    "CAF-001": {
        "nombre": "Café americano",
        "precio": Decimal("1.50"),
    },
    "SAN-001": {
        "nombre": "Sándwich",
        "precio": Decimal("2.75"),
    },
}


# 2. Almacenamiento en memoria

# Diccionario que almacena los pedidos por su UUID.
_pedidos: dict[UUID, PedidoRespuesta] = {}

# Relaciona cada clave de idempotencia con:
# (huella de la solicitud, identificador del pedido).
_idempotencia: dict[str, tuple[str, UUID]] = {}

# Protege las operaciones cuando llegan solicitudes simultáneas.
_bloqueo = RLock()


# 3. Excepciones propias del almacenamiento

class ProductoNoEncontrado(Exception):
    """Se produce cuando un producto no existe en el catálogo."""
    pass


class ClaveIdempotenciaEnConflicto(Exception):
    """Se produce cuando una clave se reutiliza con otros datos."""
    pass

class TransicionEstadoInvalida(Exception):
    """Se produce cuando un pedido intenta cambiar a un estado no permitido."""
    pass


# Transiciones de estado permitidas

TRANSICIONES_PERMITIDAS = {
    EstadoPedido.RECIBIDO: {
        EstadoPedido.PENDIENTE_CAJA,
        EstadoPedido.VENTA_CONFIRMADA,
        EstadoPedido.ERROR_CAJA,
    },

    EstadoPedido.PENDIENTE_CAJA: {
        EstadoPedido.VENTA_CONFIRMADA,
        EstadoPedido.ERROR_CAJA,
    },

    EstadoPedido.VENTA_CONFIRMADA: {
        EstadoPedido.EN_PREPARACION,
    },

    EstadoPedido.EN_PREPARACION: {
        EstadoPedido.LISTO,
        EstadoPedido.ERROR_COCINA,
    },

    EstadoPedido.LISTO: set(),
    EstadoPedido.ERROR_CAJA: set(),
    EstadoPedido.ERROR_COCINA: set(),
}



# 4. Identificar el contenido de una solicitud

def _calcular_huella(solicitud: SolicitudCrearPedido) -> str:
    """
    Genera una huella SHA-256 del contenido de la solicitud.

    Permite comprobar si una clave de idempotencia se está
    utilizando nuevamente con exactamente los mismos datos.
    """

    datos = solicitud.model_dump(mode="json")

    contenido = json.dumps(
        datos,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        contenido.encode("utf-8")
    ).hexdigest()


# 5. Construir los productos y calcular el total

def _construir_items(
    solicitud: SolicitudCrearPedido,
) -> tuple[list[ItemPedido], Decimal]:
    """
    Consulta el catálogo y construye los productos del pedido.

    Los precios siempre se obtienen del catálogo del sistema,
    nunca de los valores enviados por el estudiante.
    """

    items: list[ItemPedido] = []
    total = Decimal("0.00")

    for item_solicitado in solicitud.items:

        producto = CATALOGO.get(item_solicitado.producto_id)

        if producto is None:
            raise ProductoNoEncontrado(
                f"El producto {item_solicitado.producto_id} "
                "no existe en el catálogo."
            )

        precio = producto["precio"]
        cantidad = item_solicitado.cantidad

        subtotal = (
            precio * Decimal(cantidad)
        ).quantize(Decimal("0.01"))

        item = ItemPedido(
            producto_id=item_solicitado.producto_id,
            nombre=producto["nombre"],
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal,
        )

        items.append(item)
        total += subtotal

    return items, total.quantize(Decimal("0.01"))


# 6. Registrar un pedido con idempotencia

def crear_pedido(
    solicitud: SolicitudCrearPedido,
    clave_idempotencia: str,
) -> tuple[PedidoRespuesta, bool]:
    """
    Registra un pedido nuevo o devuelve el pedido original
    cuando recibe una solicitud repetida.

    Retorna:
        (pedido, True): pedido creado por primera vez.
        (pedido, False): pedido existente por idempotencia.
    """

    if not clave_idempotencia or not clave_idempotencia.strip():
        raise ValueError("La clave de idempotencia es obligatoria.")

    if len(clave_idempotencia) > 128:
        raise ValueError("La clave de idempotencia es demasiado larga.")

    huella = _calcular_huella(solicitud)

    with _bloqueo:

        # Comprobar si ya existe esta clave.
        registro = _idempotencia.get(clave_idempotencia)

        if registro is not None:

            huella_anterior, pedido_id = registro

            # La misma clave no puede representar otra solicitud.
            if huella_anterior != huella:
                raise ClaveIdempotenciaEnConflicto(
                    "La clave de idempotencia ya fue utilizada "
                    "con datos diferentes."
                )

            pedido_existente = _pedidos[pedido_id]

            return pedido_existente.model_copy(deep=True), False

        # Construir los productos y calcular el precio.
        items, total = _construir_items(solicitud)

        # Generar identificador y fechas.
        pedido_id = uuid4()
        ahora = datetime.now(timezone.utc)

        pedido = PedidoRespuesta(
            pedido_id=pedido_id,
            estudiante_id=solicitud.estudiante_id,
            estado=EstadoPedido.RECIBIDO,
            items=items,
            total=total,
            moneda="USD",
            observaciones=solicitud.observaciones,
            creado_en=ahora,
            actualizado_en=ahora,
        )

        # Guardar el pedido y su clave de idempotencia.
        _pedidos[pedido_id] = pedido

        _idempotencia[clave_idempotencia] = (
            huella,
            pedido_id,
        )

        return pedido.model_copy(deep=True), True


# 7. Consultar un pedido

def obtener_pedido(pedido_id: UUID) -> PedidoRespuesta | None:
    """
    Busca un pedido por su identificador.

    Retorna None si no existe.
    """

    with _bloqueo:

        pedido = _pedidos.get(pedido_id)

        if pedido is None:
            return None

        return pedido.model_copy(deep=True)


# 8. Actualizar el estado de un pedido

def actualizar_estado(
    pedido_id: UUID,
    nuevo_estado: EstadoPedido,
) -> PedidoRespuesta | None:
    """
    Actualiza el estado de un pedido solamente si la
    transición está permitida.

    Retorna None si el pedido no existe.

    Si se intenta repetir el estado actual, devuelve el
    pedido sin modificarlo.
    """

    with _bloqueo:

        pedido = _pedidos.get(pedido_id)

        if pedido is None:
            return None

        # Una actualización repetida no debe generar errores.
        if pedido.estado == nuevo_estado:
            return pedido.model_copy(deep=True)

        # Consultar los estados permitidos desde el actual.
        estados_permitidos = TRANSICIONES_PERMITIDAS.get(
            pedido.estado,
            set()
        )

        # Rechazar los cambios que no estén autorizados.
        if nuevo_estado not in estados_permitidos:
            raise TransicionEstadoInvalida(
                f"No se puede cambiar el pedido de "
                f"{pedido.estado.value} a {nuevo_estado.value}."
            )

        # Crear la versión actualizada del pedido.
        pedido_actualizado = pedido.model_copy(
            update={
                "estado": nuevo_estado,
                "actualizado_en": datetime.now(timezone.utc),
            }
        )

        _pedidos[pedido_id] = pedido_actualizado

        return pedido_actualizado.model_copy(deep=True)



# 9. Consultar todos los pedidos

def listar_pedidos() -> list[PedidoRespuesta]:
    """
    Devuelve una copia de todos los pedidos registrados.
    """

    with _bloqueo:

        return [
            pedido.model_copy(deep=True)
            for pedido in _pedidos.values()
        ]



# 10. Generar estadísticas de ventas

def obtener_estadisticas(
    desde: date | None = None,
    hasta: date | None = None,
) -> ReporteVentas:
    """
    Calcula estadísticas utilizando los pedidos almacenados
    en memoria.

    Los filtros desde y hasta se aplican sobre la fecha
    de creación del pedido.
    """

    # Estados que indican que la venta fue confirmada.
    # ERROR_COCINA se incluye porque la venta ya fue
    # confirmada antes del problema de preparación.
    estados_venta_confirmada = {
        EstadoPedido.VENTA_CONFIRMADA,
        EstadoPedido.EN_PREPARACION,
        EstadoPedido.LISTO,
        EstadoPedido.ERROR_COCINA,
    }

    with _bloqueo:

        # Seleccionar los pedidos según las fechas.
        pedidos_filtrados = [
            pedido
            for pedido in _pedidos.values()
            if (desde is None or pedido.creado_en.date() >= desde)
            and (hasta is None or pedido.creado_en.date() <= hasta)
        ]

        # Inicializar el contador de todos los estados.
        pedidos_por_estado = {
            estado.value: 0
            for estado in EstadoPedido
        }

        # Contabilizar los pedidos por estado.
        for pedido in pedidos_filtrados:
            pedidos_por_estado[pedido.estado.value] += 1

        # Seleccionar solamente las ventas confirmadas.
        ventas = [
            pedido
            for pedido in pedidos_filtrados
            if pedido.estado in estados_venta_confirmada
        ]

        # Calcular los ingresos utilizando Decimal.
        ingresos = sum(
            (venta.total for venta in ventas),
            Decimal("0.00")
        )

        return ReporteVentas(
            desde=desde,
            hasta=hasta,
            total_pedidos=len(pedidos_filtrados),
            pedidos_por_estado=pedidos_por_estado,
            ventas_confirmadas=len(ventas),
            ingresos_totales=ingresos,
            moneda="USD",
        )
