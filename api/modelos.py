
"""
Modelos y validaciones de datos para la API REST.

Define las estructuras utilizadas para recibir solicitudes,
representar pedidos y devolver respuestas.

"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# 1. Estados posibles de un pedido

class EstadoPedido(str, Enum):
    RECIBIDO = "RECIBIDO"
    PENDIENTE_CAJA = "PENDIENTE_CAJA"
    VENTA_CONFIRMADA = "VENTA_CONFIRMADA"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO = "LISTO"
    ERROR_CAJA = "ERROR_CAJA"
    ERROR_COCINA = "ERROR_COCINA"


# 2. Producto recibido desde el estudiante

class ItemPedidoSolicitud(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producto_id: str = Field(
        min_length=1,
        max_length=50,
        description="Identificador del producto"
    )

    cantidad: int = Field(
        gt=0,
        description="Cantidad solicitada, debe ser mayor que cero"
    )


# 3. Solicitud para crear un pedido

class SolicitudCrearPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estudiante_id: str = Field(
        min_length=1,
        max_length=50
    )

    items: list[ItemPedidoSolicitud] = Field(
        min_length=1,
        description="Lista de productos del pedido"
    )

    observaciones: str | None = Field(
        default=None,
        max_length=300
    )


# 4. Producto dentro de un pedido registrado


class ItemPedido(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int = Field(gt=0)

    precio_unitario: Decimal = Field(
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2
    )

    subtotal: Decimal = Field(
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2
    )



# 5. Respuesta completa de un pedido

class PedidoRespuesta(BaseModel):
    pedido_id: UUID
    estudiante_id: str

    estado: EstadoPedido

    items: list[ItemPedido]

    total: Decimal = Field(
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2
    )
    moneda: Literal["USD"] = "USD"

    observaciones: str | None = None

    creado_en: datetime
    actualizado_en: datetime


# 6. Estructura general de errores

class ErrorDetalle(BaseModel):
    codigo: str
    mensaje: str
    detalles: dict[str, Any] | None = None


class RespuestaError(BaseModel):
    error: ErrorDetalle


# 7. Modelo de estadísticas de ventas

class ReporteVentas(BaseModel):
    desde: date | None = None
    hasta: date | None = None

    total_pedidos: int

    pedidos_por_estado: dict[str, int]

    ventas_confirmadas: int

    ingresos_totales: Decimal = Field(
        ge=Decimal("0.00"),
        max_digits=12,
        decimal_places=2
    )

    moneda: Literal["USD"] = "USD"

