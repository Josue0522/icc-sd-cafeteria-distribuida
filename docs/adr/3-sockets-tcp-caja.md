# ADR-003: Comunicación TCP entre la API y caja y facturación

## Estado

Propuesto.

## Contexto

El sistema de cafetería necesita registrar en caja las ventas correspondientes a los pedidos aceptados por la API REST. Para ello, la API y el módulo de caja deben intercambiar los datos de cada venta mediante un protocolo de comunicación entre procesos.

El mensaje debe identificar el pedido y la operación, incluir sus productos e importes y permitir que caja responda con una confirmación o un error. También se necesita evitar que un reintento registre dos veces la misma venta.

## Alternativas evaluadas

| Alternativa | Contexto | Ventajas | Desventajas |
|---|---|---|---|
| REST sobre HTTP | La API enviaría la venta a un endpoint HTTP de caja. | Usa un protocolo conocido y facilita la inspección de solicitudes. | Requiere exponer un servidor HTTP en caja y no coincide con el mecanismo TCP definido para este componente. |
| Sockets TCP | La API abre una conexión TCP con caja e intercambia mensajes en un formato acordado. | Comunicación directa entre procesos, control explícito del protocolo y uso del contrato de caja definido para el proyecto. | El equipo debe delimitar los mensajes y gestionar desconexiones, tiempos de espera y errores. |
| XML-RPC | La API invocaría una operación remota del servicio de caja. | Permite representar llamadas entre procesos con una interfaz definida. | Añade un mecanismo distinto al acordado para la comunicación con caja. |
| WebSockets | Mantiene una conexión persistente y bidireccional entre componentes. | Permite intercambiar mensajes en ambas direcciones sobre una conexión persistente. | Está orientado a las notificaciones en tiempo real y resulta innecesario para el intercambio puntual de una venta. |

## Decisión

Se propone utilizar sockets TCP para la comunicación entre la API REST y el servicio de caja y facturación.

La API enviará una solicitud por conexión como un objeto JSON codificado en UTF-8 y terminado en un salto de línea (`\n`). El servicio procesará una solicitud por conexión y devolverá una respuesta JSON con el mismo delimitador. El tamaño máximo del mensaje será de 65 536 bytes.

La solicitud incluirá `version`, `tipo`, `operacion_id`, `pedido_id`, `moneda`, `items` y `total`. Los importes se transmitirán como cadenas decimales, y caja verificará los subtotales y el total usando `Decimal`.

El servicio escuchará por defecto en `127.0.0.1:9001`; la dirección y el puerto podrán configurarse mediante `TCP_HOST` y `TCP_PORT`. La respuesta confirmará la venta o describirá el error. Las solicitudes repetidas con el mismo `operacion_id` y el mismo contenido recibirán la respuesta original; si el identificador se reutiliza con contenido diferente, la operación se rechazará.

## Justificación

TCP permite que la API envíe directamente a caja los datos necesarios para registrar una venta y reciba el resultado en la misma conexión. El delimitador de línea permite identificar el final de cada mensaje, mientras que el formato JSON mantiene el contenido legible e interoperable entre los módulos.

El identificador `operacion_id` permite reconocer reintentos y evitar el registro duplicado durante la ejecución del servicio. La representación decimal evita errores de precisión en los importes monetarios.

## Atributos de calidad beneficiados

**Integridad de datos:** los importes se validan con `Decimal` y se comprueba que la suma de los subtotales coincida con el total.

**Fiabilidad:** la clave de operación permite responder de forma idempotente a reintentos con el mismo contenido.

**Interoperabilidad:** API y caja intercambian mensajes JSON con un contrato explícito.

## Consecuencias

### Consecuencias positivas

1. La API y caja pueden intercambiar solicitudes y respuestas sin depender de una interfaz HTTP en el servicio de caja.
2. El contrato define los campos de venta, el formato de importes y la estructura de confirmaciones y errores.
3. Los reintentos de una operación idéntica no crean una segunda venta mientras el proceso mantenga su registro en memoria.
4. El servicio puede atender conexiones de clientes de manera concurrente.

### Consecuencias negativas y limitaciones

1. Las conexiones pueden fallar o expirar; la API debe interpretar esos errores y decidir si corresponde reintentar.
2. Las ventas y claves de idempotencia se guardan en memoria y se pierden al reiniciar el servicio.
3. El comprobante generado es simulado; el módulo no procesa pagos ni genera una factura tributaria.
4. La implementación no incorpora autenticación, por lo que se limita al entorno de desarrollo previsto.
5. El protocolo requiere que ambos módulos respeten el formato JSON terminado en salto de línea y los límites establecidos.

## Referencias

- Contrato TCP de caja: `docs/arquitectura/tcp-caja.md`.
- Contratos entre servicios: `docs/arquitectura/contratos-comunicacion.md`.
- Implementación de caja y facturación: `caja_facturacion/`.
