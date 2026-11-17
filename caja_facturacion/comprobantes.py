"""Validación de ventas y almacenamiento en memoria.

Preparado con asistencia de Codex para revisión del equipo.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import re
import threading
from typing import Any
from uuid import UUID


PATRON_IMPORTE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d{1,2})?$")


class ErrorVenta(ValueError):
    """Error de validación de la solicitud de venta."""

    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass(frozen=True)
class VentaValidada:
    operacion_id: str
    pedido_id: str
    moneda: str
    items: tuple[dict[str, Any], ...]
    total: Decimal
    huella: str


def _leer_importe(valor: Any, campo: str) -> Decimal:
    if not isinstance(valor, str) or not PATRON_IMPORTE.fullmatch(valor):
        raise ErrorVenta("IMPORTE_INVALIDO", f"{campo} debe ser texto decimal con hasta dos decimales.")
    try:
        importe = Decimal(valor)
    except InvalidOperation as error:
        raise ErrorVenta("IMPORTE_INVALIDO", f"{campo} no es un importe válido.") from error
    if not importe.is_finite():
        raise ErrorVenta("IMPORTE_INVALIDO", f"{campo} debe ser un importe finito.")
    return importe


def validar_solicitud_venta(datos: dict[str, Any]) -> VentaValidada:
    """Valida el mensaje que construye `api.servicios.construir_solicitud_venta`."""
    if datos.get("version") != 1 or isinstance(datos.get("version"), bool):
        raise ErrorVenta("VERSION_NO_SOPORTADA", "La versión del protocolo debe ser 1.")
    if datos.get("tipo") != "REGISTRAR_VENTA":
        raise ErrorVenta("TIPO_NO_SOPORTADO", "El tipo de solicitud debe ser REGISTRAR_VENTA.")

    operacion_id = datos.get("operacion_id")
    pedido_id = datos.get("pedido_id")
    if not isinstance(operacion_id, str) or not operacion_id.strip():
        raise ErrorVenta("OPERACION_ID_INVALIDO", "operacion_id es obligatorio.")
    if len(operacion_id) > 200:
        raise ErrorVenta("OPERACION_ID_INVALIDO", "operacion_id supera el tamaño permitido.")
    if not isinstance(pedido_id, str):
        raise ErrorVenta("PEDIDO_ID_INVALIDO", "pedido_id debe ser un UUID en texto.")
    try:
        pedido_id = str(UUID(pedido_id))
    except (ValueError, AttributeError) as error:
        raise ErrorVenta("PEDIDO_ID_INVALIDO", "pedido_id debe ser un UUID válido.") from error

    moneda = datos.get("moneda")
    if moneda != "USD":
        raise ErrorVenta("MONEDA_NO_SOPORTADA", "Caja solo admite importes en USD.")

    items_datos = datos.get("items")
    if not isinstance(items_datos, list) or not items_datos:
        raise ErrorVenta("ITEMS_INVALIDOS", "items debe ser una lista no vacía.")

    items: list[dict[str, Any]] = []
    suma = Decimal("0.00")
    for indice, item in enumerate(items_datos, start=1):
        if not isinstance(item, dict):
            raise ErrorVenta("ITEM_INVALIDO", f"El producto {indice} debe ser un objeto.")

        producto_id = item.get("producto_id")
        nombre = item.get("nombre")
        cantidad = item.get("cantidad")
        if not isinstance(producto_id, str) or not producto_id.strip():
            raise ErrorVenta("PRODUCTO_INVALIDO", f"El producto {indice} no tiene producto_id válido.")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorVenta("PRODUCTO_INVALIDO", f"El producto {indice} no tiene nombre válido.")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ErrorVenta("CANTIDAD_INVALIDA", f"La cantidad del producto {indice} debe ser un entero positivo.")

        precio = _leer_importe(item.get("precio_unitario"), f"items[{indice}].precio_unitario")
        subtotal = _leer_importe(item.get("subtotal"), f"items[{indice}].subtotal")
        if precio * cantidad != subtotal:
            raise ErrorVenta("SUBTOTAL_INVALIDO", f"El subtotal del producto {indice} no coincide con precio por cantidad.")

        items.append({
            "producto_id": producto_id.strip(),
            "nombre": nombre.strip(),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": subtotal,
        })
        suma += subtotal

    total = _leer_importe(datos.get("total"), "total")
    if total != suma:
        raise ErrorVenta("TOTAL_INVALIDO", "El total no coincide con la suma de los subtotales.")

    normalizado = {
        "pedido_id": pedido_id,
        "moneda": moneda,
        "items": [
            {
                **item,
                "precio_unitario": format(item["precio_unitario"], ".2f"),
                "subtotal": format(item["subtotal"], ".2f"),
            }
            for item in items
        ],
        "total": format(total, ".2f"),
    }
    huella = json.dumps(normalizado, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return VentaValidada(operacion_id, pedido_id, moneda, tuple(items), total, huella)


def crear_comprobante(numero: str, total: Decimal, moneda: str) -> dict[str, Any]:
    """Crea un comprobante simulado; los centavos salen como entero."""
    return {
        "numero": numero,
        "total_centavos": int(total * 100),
        "moneda": moneda,
    }


class RegistroVentas:
    """Registro de ventas en memoria con idempotencia por operacion_id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._resultados: dict[str, tuple[str, dict[str, Any]]] = {}
        self._siguiente = 1

    @property
    def cantidad_ventas(self) -> int:
        with self._lock:
            return len(self._resultados)

    def registrar(self, datos: dict[str, Any]) -> dict[str, Any]:
        try:
            venta = validar_solicitud_venta(datos)
        except ErrorVenta as error:
            return respuesta_error(datos, error.codigo, error.mensaje)

        with self._lock:
            anterior = self._resultados.get(venta.operacion_id)
            if anterior is not None:
                huella_anterior, respuesta = anterior
                if huella_anterior == venta.huella:
                    return dict(respuesta)
                return respuesta_error(
                    datos,
                    "OPERACION_ID_REUTILIZADO",
                    "operacion_id ya fue utilizado con datos diferentes.",
                )

            consecutivo = self._siguiente
            self._siguiente += 1
            respuesta = {
                "ok": True,
                "tipo": "VENTA_CONFIRMADA",
                "operacion_id": venta.operacion_id,
                "pedido_id": venta.pedido_id,
                "venta_id": f"VENTA-{consecutivo:06d}",
                "comprobante": crear_comprobante(
                    f"COMP-{consecutivo:06d}", venta.total, venta.moneda
                ),
            }
            self._resultados[venta.operacion_id] = (venta.huella, respuesta)
            return dict(respuesta)


def respuesta_error(datos: dict[str, Any], codigo: str, mensaje: str) -> dict[str, Any]:
    """Construye un error compatible con el cliente TCP de la API."""
    operacion_id = datos.get("operacion_id")
    pedido_id = datos.get("pedido_id")
    return {
        "ok": False,
        "tipo": "ERROR_CAJA",
        "operacion_id": operacion_id if isinstance(operacion_id, str) else None,
        "pedido_id": pedido_id if isinstance(pedido_id, str) else None,
        "error": {
            "codigo": codigo,
            "mensaje": mensaje,
            "reintentable": False,
        },
    }
