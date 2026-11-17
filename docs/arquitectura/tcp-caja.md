# Caja y facturación por TCP

Este documento describe el módulo TCP de caja. El formato de entrada se basa en el mensaje que construye `api.servicios.construir_solicitud_venta` en la rama REST. La sección TCP de `contratos-comunicacion.md` se actualizó con ese formato; el equipo debe revisar el contrato al integrar todos los módulos.

## Ejecutar

Desde la raíz del proyecto, en una terminal:

```powershell
python -m caja_facturacion.servidor_tcp
```

Por defecto escucha en `127.0.0.1:9001`, con timeout de 3 segundos por cliente. Se pueden configurar `TCP_HOST` y `TCP_PORT`, o pasar opciones:

```powershell
python -m caja_facturacion.servidor_tcp --host 127.0.0.1 --puerto 9001
```

## Protocolo

La conexión usa UTF-8. Cada solicitud y respuesta es un objeto JSON terminado en `\n`; se atiende una solicitud por conexión. El tamaño máximo del mensaje es 65 536 bytes.

La API envía una venta con `version`, `tipo`, `operacion_id`, `pedido_id`, `moneda`, `items` y `total`. Los importes llegan como texto decimal con hasta dos posiciones, por ejemplo `"1.50"`. Caja calcula con `Decimal`, verifica subtotales y total, y no usa `float`.

Ejemplo abreviado de la solicitud que genera la API:

```json
{
  "version": 1,
  "tipo": "REGISTRAR_VENTA",
  "operacion_id": "VENTA-550e8400-e29b-41d4-a716-446655440000",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "moneda": "USD",
  "items": [
    {
      "producto_id": "CAF-001",
      "nombre": "Café americano",
      "cantidad": 2,
      "precio_unitario": "1.50",
      "subtotal": "3.00"
    }
  ],
  "total": "3.00"
}
```

Una confirmación incluye `ok: true`, `tipo: "VENTA_CONFIRMADA"`, ambos identificadores, un `venta_id` y el comprobante simulado. `total_centavos` es un entero; USD 3,00 se representa como `300`. Los errores usan `ok: false`, `tipo: "ERROR_CAJA"` y un objeto `error` con código, mensaje y si el cliente puede reintentar.

Si se repite el mismo `operacion_id` con el mismo contenido, se devuelve la respuesta original. Si se reutiliza con datos distintos, se rechaza la operación.

## Pruebas

Con pytest instalado:

```powershell
python -m pytest pruebas/test_caja_tcp.py -v
```

Las pruebas cubren venta, duplicados, JSON inválido, importes, desconexión del cliente y puerto no disponible. Registra los resultados después de ejecutarlas en tu entorno.

## Limitaciones

Las ventas y claves de idempotencia viven en memoria y se pierden al reiniciar el proceso. El comprobante es simulado; no procesa pagos ni genera facturas tributarias. El servicio es de desarrollo y no incorpora autenticación.
