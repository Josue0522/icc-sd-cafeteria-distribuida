# Contratos de comunicación

**Proyecto:** Sistema Distribuido de Gestión de Pedidos para una Cafetería Universitaria.

**Versión:** 1.0

**Responsable de la propuesta:** Mateo (API REST).

**Estado:** Propuesta inicial pendiente de revisión y aprobación del equipo.

## 1. Objetivo

Definir los formatos de datos, solicitudes, respuestas y reglas de comunicación entre los componentes del sistema.

Se utilizarán cuatro mecanismos:

- REST: gestión de pedidos y consultas.
- RPC (XML-RPC): comunicación con cocina.
- Sockets TCP: comunicación con caja y facturación.
- WebSockets: notificaciones al estudiante.

La API REST será responsable de mantener el estado oficial de los pedidos y coordinar los servicios internos.

## 2. Convenciones generales

### 2.1 Identificadores

- pedido_id: identificador UUID generado por la API para cada pedido.
- estudiante_id: identificador del estudiante.
- producto_id: identificador del producto del menú.
- operacion_id: identificador estable de la operación de venta. Se utilizará el mismo valor en todos los reintentos de una misma venta.
- venta_id: identificador de la venta generado por caja.

Todos los servicios deberán conservar el mismo pedido_id durante el procesamiento de un pedido.

### 2.2 Valores monetarios

Los importes se manejarán utilizando valores decimales con dos posiciones decimales y la moneda USD.

- Los precios se representarán como cadenas de texto en los mensajes JSON.
- Ejemplo: "1.50" representa USD 1,50.
- Los cálculos internos en Python utilizarán Decimal para evitar errores de precisión.
- No se utilizarán números de coma flotante (float) para operaciones monetarias.
- Los precios se obtendrán del catálogo administrado por la API, no de los valores enviados por el estudiante.

### 2.3 Fechas

Las fechas y horas se representarán mediante cadenas ISO 8601 en UTC.

Ejemplo: 2026-11-14T19:05:00Z.

### 2.4 Almacenamiento

Los pedidos, ventas, claves de idempotencia y resultados se conservarán en memoria.

Los datos se perderán cuando se reinicie el servidor. Esta limitación es aceptada para la práctica.

## 3. Estructura de un pedido

### 3.1 Solicitud de creación

El estudiante enviará los siguientes datos mediante REST:

```json
{
  "estudiante_id": "EST-001",
  "items": [
    {
      "producto_id": "CAF-001",
      "cantidad": 2
    },
    {
      "producto_id": "SAN-001",
      "cantidad": 1
    }
  ],
  "observaciones": "Sin azúcar"
}
```

Reglas:

- estudiante_id es obligatorio.
- items debe contener al menos un producto.
- producto_id es obligatorio.
- cantidad debe ser un entero mayor que cero.
- observaciones es opcional.
- El cliente no enviará los precios como valores confiables.
- La API obtendrá los precios desde su catálogo en memoria y calculará los importes.

### 3.2 Representación interna del pedido

Una vez validado, la API almacenará una estructura similar a esta:

```json
{
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estudiante_id": "EST-001",
  "estado": "RECIBIDO",
  "items": [
    {
      "producto_id": "CAF-001",
      "nombre": "Café americano",
      "cantidad": 2,
      "precio_unitario": "1.50",
      "subtotal": "3.00"
    }
  ],
  "total": "3.00",
  "moneda": "USD",
  "observaciones": "Sin azúcar",
  "creado_en": "2026-11-14T19:00:00Z",
  "actualizado_en": "2026-11-14T19:00:00Z"
}
```

## 4. Estados del pedido

Los estados oficiales serán:

| Estado | Descripción |
|---|---|
| RECIBIDO | La API recibió y registró el pedido. |
| PENDIENTE_CAJA | No se pudo confirmar el resultado de la operación de caja. |
| VENTA_CONFIRMADA | Caja confirmó el registro de la venta. |
| EN_PREPARACION | Cocina está preparando el pedido. |
| LISTO | Cocina terminó la preparación. |
| ERROR_CAJA | Caja rechazó definitivamente la operación. |
| ERROR_COCINA | Cocina no pudo completar la preparación. |

PENDIENTE_CAJA representa un resultado desconocido por timeout o indisponibilidad. No significa necesariamente que la venta haya fallado.

Una operación pendiente no debe enviarse automáticamente a cocina hasta recibir la confirmación de caja.

## 5. Comunicación REST

La API utilizará FastAPI.

### 5.1 Crear pedido

**Método:** POST

**Endpoint:** /pedidos

**Cabecera obligatoria:**

Idempotency-Key: identificador único de la solicitud del estudiante.

**Códigos de respuesta propuestos:**

- 201 Created: pedido creado y operación de caja confirmada.
- 202 Accepted: pedido registrado, pero la operación de caja sigue pendiente.
- 400 Bad Request: falta la clave de idempotencia.
- 409 Conflict: misma clave utilizada con contenido diferente.
- 422 Unprocessable Entity: datos inválidos.

Las respuestas incluirán pedido_id, estado y los datos principales del pedido.

### 5.2 Consultar pedido

**Método:** GET

**Endpoint:** /pedidos/{pedido_id}

Respuestas:

- 200 OK: pedido encontrado.
- 404 Not Found: pedido inexistente.

La respuesta incluirá el estado actualizado y los datos del pedido.

### 5.3 Consultar estadísticas

**Método:** GET

**Endpoint:** /reportes/ventas

La API generará estadísticas utilizando los pedidos y ventas almacenados en memoria.

Se podrán incluir filtros de fecha mediante los parámetros desde y hasta.

Los reportes contabilizarán las ventas confirmadas, evitando incluir pedidos rechazados o pendientes.

## 6. Comunicación mediante Sockets TCP

Responsable del módulo: Josué.

El servidor TCP de caja y facturación escuchará en un puerto configurable.

### 6.1 Formato del protocolo

- Codificación UTF-8.
- Mensajes en formato JSON.
- Cada mensaje terminará con un salto de línea (\n).
- Se enviará una solicitud por conexión y se devolverá una respuesta.
- Se utilizará un timeout para evitar esperas indefinidas.

### 6.2 Solicitud de registro de venta

```json

{
  "producto_id": "CAF-001",
  "nombre": "Café americano",
  "cantidad": 2,
  "precio_unitario": "1.50",
  "subtotal": "3.00"
}
```

### 6.3 Respuesta exitosa

```json
{
  "ok": true,
  "tipo": "VENTA_CONFIRMADA",
  "operacion_id": "VENTA-550e8400-e29b-41d4-a716-446655440000",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "venta_id": "VENTA-001",
  "comprobante": {
    "numero": "COMP-001",
    "total_centavos": 3.00,
    "moneda": "USD"
  }
}
```

### 6.4 Respuesta de error

```json
{
  "ok": false,
  "tipo": "ERROR_CAJA",
  "operacion_id": "VENTA-550e8400-e29b-41d4-a716-446655440000",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {
    "codigo": "VENTA_RECHAZADA",
    "mensaje": "No se pudo registrar la venta",
    "reintentable": false
  }
}
```

### 6.5 Idempotencia

Caja mantendrá un registro en memoria de las operaciones procesadas.

Si recibe nuevamente una operación con el mismo operacion_id, devolverá el resultado original sin registrar otra venta ni generar otro comprobante.

Si una solicitud termina en timeout, la API podrá reintentar utilizando el mismo operacion_id.

## 7. Comunicación RPC con cocina

Responsable del módulo: Sebastián.

Se utilizará XML-RPC para las llamadas remotas entre la API y el servidor de cocina.

### 7.1 Función remota

preparar_pedido(pedido_id, productos)

Parámetros:

- pedido_id: UUID del pedido.
- productos: lista de productos, cantidades e identificadores.

Ejemplo conceptual:

```python
preparar_pedido(
    "550e8400-e29b-41d4-a716-446655440000",
    [
        {
            "producto_id": "CAF-001",
            "nombre": "Café americano",
            "cantidad": 2
        }
    ]
)
```

### 7.2 Respuesta exitosa

```python
{
    "ok": True,
    "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
    "estado": "LISTO",
    "mensaje": "Pedido preparado correctamente"
}
```

### 7.3 Respuesta de error

```python
{
    "ok": False,
    "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
    "estado": "ERROR_COCINA",
    "mensaje": "No fue posible preparar el pedido"
}
```

### 7.4 Reglas de procesamiento

- La API iniciará la llamada RPC mediante un worker en segundo plano.
- La llamada será síncrona desde el worker, sin bloquear innecesariamente las solicitudes REST.
- Cocina devolverá el resultado mediante la misma llamada RPC.
- Cocina deberá reconocer los pedidos previamente procesados para evitar repetir su preparación.
- Se utilizará el mismo pedido_id en los reintentos.

## 8. Comunicación WebSocket

Responsable del módulo: Bryan.

### 8.1 Endpoint

/ws/pedidos/{pedido_id}

El estudiante establecerá una conexión para recibir actualizaciones de su pedido.

### 8.2 Formato de los eventos

```json
{
  "tipo": "estado_actualizado",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "EN_PREPARACION",
  "mensaje": "Tu pedido está siendo preparado",
  "fecha": "2026-11-14T19:05:00Z"
}
```

### 8.3 Notificación de pedido listo

```json
{
  "tipo": "estado_actualizado",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "LISTO",
  "mensaje": "Tu pedido está listo",
  "fecha": "2026-11-14T19:10:00Z"
}
```

### 8.4 Reglas

- La API será responsable de mantener el estado oficial.
- Las notificaciones se enviarán después de actualizar el estado.
- La desconexión del estudiante no eliminará el pedido.
- El estudiante podrá recuperar su estado mediante GET /pedidos/{pedido_id}.
- El cliente podrá reconectar al endpoint WebSocket.

## 9. Formato general de errores

Los errores REST utilizarán una estructura uniforme:

```json
{
  "error": {
    "codigo": "PEDIDO_NO_ENCONTRADO",
    "mensaje": "No existe un pedido con ese identificador",
    "detalles": null
  }
}
```

Los códigos HTTP se utilizarán según el tipo de error:

| Código | Significado |
|---|---|
| 400 | Solicitud incorrecta. |
| 404 | Recurso inexistente. |
| 409 | Conflicto de idempotencia. |
| 422 | Datos inválidos. |
| 502 | Error de comunicación con un servicio interno cuando no se puede conservar una operación pendiente. |
| 503 | Servicio temporalmente no disponible. |
| 500 | Error interno no previsto. |

Los errores de TCP y RPC también devolverán códigos y mensajes comprensibles para la API.

No se expondrán trazas internas ni información sensible al estudiante.

## 10. Idempotencia

### 10.1 REST

El estudiante enviará la cabecera Idempotency-Key al crear un pedido.

Reglas:

- Misma clave y mismo contenido: devolver el pedido original.
- Misma clave y contenido diferente: responder 409 Conflict.
- Clave nueva: procesar una nueva solicitud.

La API conservará la relación entre la clave y el pedido en memoria.

### 10.2 TCP

La API utilizará un operacion_id estable para identificar la venta.

Los reintentos conservarán el mismo valor.

### 10.3 RPC

Cocina utilizará pedido_id como identificador de la operación de preparación.

Una solicitud repetida no deberá iniciar una segunda preparación del mismo pedido.

## 11. Tiempos de espera y reintentos

Valores iniciales propuestos, pendientes de pruebas y aprobación:

| Comunicación | Timeout propuesto | Política |
|---|---|---|
| API hacia TCP | 3 segundos por intento | Un reintento con el mismo operacion_id. |
| API hacia RPC | 15 segundos | Ejecutar en worker y conservar el pedido en preparación si el resultado queda pendiente. |
| WebSocket | Reconexión ante desconexión | Recuperar el estado mediante REST. |

### 11.1 Indisponibilidad de caja

Si Caja no responde después del intento y su reintento:

- La API conservará el pedido.
- El estado será PENDIENTE_CAJA.
- No iniciará la preparación.
- No generará una segunda venta con otro operacion_id.

### 11.2 Indisponibilidad de cocina

Si la llamada RPC no devuelve una respuesta dentro del timeout:

- La API conservará el pedido en EN_PREPARACION.
- Registrará el error de comunicación.
- No asumirá que la preparación falló definitivamente.
- Se evitarán reintentos que puedan duplicar la preparación.

### 11.3 Desconexión del estudiante

La desconexión del cliente no interrumpirá el procesamiento del pedido.

El estado permanecerá almacenado y podrá consultarse mediante REST.

## 12. Flujo general acordado como propuesta

1. El estudiante crea el pedido mediante REST.
2. La API valida los datos, verifica la clave de idempotencia y registra el pedido.
3. La API envía la venta a Caja mediante TCP.
4. Caja valida los importes y responde con la confirmación o un error.
5. Si la venta se confirma, la API actualiza el estado a VENTA_CONFIRMADA.
6. La API actualiza el estado a EN_PREPARACION e inicia la llamada RPC en segundo plano.
7. Cocina procesa el pedido y devuelve el resultado por la misma llamada RPC.
8. La API actualiza el estado a LISTO o ERROR_COCINA.
9. La API comunica los cambios mediante WebSockets.
10. Administración consulta las estadísticas generadas desde los datos almacenados en memoria.


## 14. Publicación de eventos hacia WebSockets

### 14.1 Comunicación interna

La API REST publicará los cambios de estado mediante una conexión WebSocket hacia el servicio de notificaciones.

Endpoint interno propuesto:

ws://127.0.0.1:9003/ws/interno/notificaciones

Este endpoint será utilizado por la API y no por los estudiantes.

La API abrirá una conexión, enviará un evento JSON y cerrará la conexión.

El servicio de notificaciones recibirá el evento y lo distribuirá a los estudiantes conectados al pedido correspondiente.

### 14.2 Comunicación con estudiantes

Los estudiantes se conectarán al siguiente endpoint:

/ws/pedidos/{pedido_id}

El servicio de notificaciones gestionará las conexiones activas y entregará las actualizaciones correspondientes.

### 14.3 Formato del evento

{
  "tipo": "estado_actualizado",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "EN_PREPARACION",
  "mensaje": "Tu pedido está siendo preparado.",
  "fecha": "2026-11-14T19:05:00Z"
}

### 14.4 Manejo de errores

- La API será responsable del estado oficial del pedido.
- Una falla de WebSockets no deberá interrumpir el procesamiento.
- Los errores de notificación se registrarán en los logs.
- El estudiante podrá consultar el estado actualizado mediante REST.
- La URL y el endpoint interno son propuestas pendientes de revisión con el responsable de WebSockets.
