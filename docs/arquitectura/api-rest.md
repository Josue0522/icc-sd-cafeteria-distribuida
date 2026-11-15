
# Documentación del módulo API REST

**Proyecto:** Sistema Distribuido de Gestión de Pedidos para una Cafetería Universitaria.

**Responsable:** Mateo.

**Tecnología:** Python y FastAPI.

**Versión de la API:** 0.2.0.

**Estado:** Implementación inicial desarrollada. Integración real con los servicios externos pendiente.

---

## 1. Objetivo del módulo

El módulo API REST es el componente central encargado de recibir y gestionar los pedidos realizados por los estudiantes.

También coordina la comunicación con los servicios internos de caja y facturación, cocina y notificaciones.

La API mantiene el estado oficial de cada pedido y proporciona endpoints para que los estudiantes y la administración consulten la información.

Los datos se almacenan temporalmente en memoria, sin utilizar una base de datos externa.

## 2. Tecnologías utilizadas

| Tecnología | Utilización |
|---|---|
| Python 3.14.2 | Lenguaje de programación. |
| FastAPI | Desarrollo de la API REST. |
| Uvicorn | Servidor de ejecución ASGI. |
| Pydantic | Validación y definición de modelos de datos. |
| Decimal | Manejo preciso de valores monetarios. |
| Pytest | Pruebas automatizadas. |
| HTTPX2 | Compatibilidad con las pruebas de FastAPI. |
| WebSockets | Cliente para publicar notificaciones. |
| XML-RPC | Cliente para comunicarse con cocina. |
| Socket | Cliente TCP para caja y facturación. |

## 3. Estructura del módulo

La carpeta `api/` contiene los siguientes archivos:

| Archivo | Responsabilidad |
|---|---|
| `__init__.py` | Identifica la carpeta como paquete Python. |
| `main.py` | Inicializa FastAPI y define los endpoints REST. |
| `modelos.py` | Define los modelos Pydantic, estados y estructuras de respuesta. |
| `almacen.py` | Administra el catálogo, pedidos, idempotencia y estadísticas en memoria. |
| `configuracion.py` | Centraliza direcciones, puertos y tiempos de espera. |
| `servicios.py` | Implementa los clientes TCP y XML-RPC. |
| `coordinador.py` | Coordina el procesamiento y la recuperación de pedidos. |
| `notificaciones_cliente.py` | Publica los cambios de estado mediante WebSockets. |

## 4. Endpoints REST

### 4.1 Página principal

**Método:** GET

**Ruta:** `/`

Permite comprobar que el servicio REST está funcionando.

### 4.2 Estado del servicio

**Método:** GET

**Ruta:** `/health`

Permite verificar la disponibilidad de la API.

### 4.3 Crear pedidos

**Método:** POST

**Ruta:** `/pedidos`

Recibe los datos de un pedido, valida sus productos y cantidades, calcula los importes utilizando el catálogo y registra el pedido en memoria.

Requiere la cabecera:

`Idempotency-Key`

Ejemplo de solicitud:

```json
{
  "estudiante_id": "EST-001",
  "items": [
    {
      "producto_id": "CAF-001",
      "cantidad": 2
    }
  ],
  "observaciones": "Sin azúcar"
}
```

El estudiante no puede establecer directamente los precios. La API obtiene los valores desde su catálogo.

Respuestas principales:

| Código HTTP | Descripción |
|---|---|
| 202 | Pedido nuevo registrado y procesamiento programado. |
| 200 | Solicitud repetida que devuelve el pedido original. |
| 400 | Falta la clave de idempotencia o existe otro error de solicitud. |
| 409 | La clave de idempotencia fue utilizada con datos diferentes. |
| 422 | Los datos no superan las validaciones o el producto no existe. |

### 4.4 Consultar pedidos

**Método:** GET

**Ruta:** `/pedidos/{pedido_id}`

Permite consultar un pedido mediante su identificador UUID.

Respuestas:

- 200: pedido encontrado.
- 404: pedido inexistente.
- 422: identificador UUID inválido.

### 4.5 Consultar estadísticas

**Método:** GET

**Ruta:** `/reportes/ventas`

Permite consultar las estadísticas de pedidos y ventas.

Admite dos parámetros opcionales:

- `desde`: fecha inicial.
- `hasta`: fecha final.

Las estadísticas se calculan directamente desde los pedidos almacenados en memoria.

Se contabilizan como ventas confirmadas los pedidos en los estados VENTA_CONFIRMADA, EN_PREPARACION, LISTO y ERROR_COCINA.

Los pedidos pendientes o rechazados por caja no se incluyen en los ingresos.

## 5. Modelos y estados de los pedidos

Los pedidos utilizan identificadores UUID.

Los importes monetarios se representan mediante Decimal en Python y cadenas decimales en los mensajes JSON, utilizando USD.

Ejemplo:

- Precio unitario: `"1.50"`.
- Subtotal: `"3.00"`.
- Total: `"3.00"`.

### Estados disponibles

| Estado | Descripción |
|---|---|
| RECIBIDO | La API recibió y registró el pedido. |
| PENDIENTE_CAJA | No se pudo confirmar el resultado de caja. |
| VENTA_CONFIRMADA | Caja confirmó la venta. |
| EN_PREPARACION | Cocina está preparando el pedido. |
| LISTO | Cocina terminó la preparación. |
| ERROR_CAJA | Caja rechazó definitivamente la venta. |
| ERROR_COCINA | Cocina no pudo completar la preparación. |

Las transiciones están controladas para impedir saltos de estado no permitidos.

El servidor REST es la fuente oficial del estado de los pedidos.

## 6. Almacenamiento en memoria

El módulo utiliza diccionarios de Python protegidos mediante un bloqueo de concurrencia.

Se almacenan:

- Pedidos registrados.
- Catálogo provisional de productos.
- Claves de idempotencia.
- Relación entre las claves y los pedidos originales.

No se utiliza una base de datos externa.

Al reiniciar el proceso del servidor, los datos almacenados se pierden.

## 7. Mecanismo de idempotencia

La API utiliza la cabecera `Idempotency-Key` al recibir solicitudes de creación de pedidos.

Se calcula una huella del contenido de la solicitud para detectar si una clave está siendo reutilizada con datos diferentes.

Comportamiento:

- Misma clave y mismo contenido: se devuelve el pedido original.
- Misma clave y contenido diferente: se devuelve 409 Conflict.
- Clave nueva: se registra un nuevo pedido.

Para las operaciones internas de caja se utiliza un identificador estable:

`VENTA-{pedido_id}`

De esta forma, los reintentos conservan el mismo identificador de operación.

## 8. Coordinación de servicios internos

El procesamiento se realiza mediante tareas en segundo plano de FastAPI.

### 8.1 Comunicación con caja mediante TCP

La API construye un mensaje JSON y lo envía al servidor TCP de caja y facturación.

Características:

- Codificación UTF-8.
- Mensajes JSON delimitados por salto de línea.
- Una solicitud por conexión.
- Timeout inicial de 3 segundos por intento.
- Máximo de dos intentos.
- Mismo `operacion_id` durante los reintentos.

Si caja confirma la venta, el pedido continúa hacia cocina.

Si no se obtiene una respuesta después de los intentos, el pedido queda en PENDIENTE_CAJA.

### 8.2 Comunicación con cocina mediante XML-RPC

Después de confirmar la venta, la API solicita la preparación mediante:

`preparar_pedido(pedido_id, productos)`

El timeout inicial configurado es de 15 segundos.

Cocina devuelve el resultado por la misma llamada RPC.

Si la operación termina correctamente, la API registra LISTO.

Si cocina devuelve un error de preparación, registra ERROR_COCINA.

Si se pierde la respuesta por un timeout, el estado permanece EN_PREPARACION, porque no se puede asegurar que la preparación haya fallado.

### 8.3 Notificaciones mediante WebSockets

La API utiliza un cliente WebSocket para publicar los cambios de estado en el servicio de notificaciones.

Endpoint interno propuesto:

`ws://127.0.0.1:9003/ws/interno/notificaciones`

Los eventos incluyen:

- tipo
- pedido_id
- estado
- mensaje
- fecha

El servicio de notificaciones será responsable de distribuir los eventos a los estudiantes conectados.

Una falla de notificación no debe modificar el estado oficial del pedido ni detener su procesamiento.

## 9. Recuperación de pedidos

El coordinador contempla la recuperación de pedidos que quedaron pendientes.

Comportamiento:

| Estado | Recuperación |
|---|---|
| PENDIENTE_CAJA | Reintentar TCP con el mismo operacion_id. |
| VENTA_CONFIRMADA | Continuar hacia preparación. |
| EN_PREPARACION | Reintentar la consulta de preparación mediante RPC con el mismo pedido_id. |
| LISTO | No volver a procesar. |
| ERROR_CAJA | No volver a procesar. |
| ERROR_COCINA | No volver a procesar automáticamente. |

Se utiliza un conjunto protegido mediante un bloqueo para impedir que dos workers del coordinador procesen simultáneamente el mismo pedido.

La recuperación se encuentra disponible mediante funciones internas del módulo. Todavía no existe un proceso automático periódico de recuperación.

## 10. Configuración

Los valores predeterminados para desarrollo local son:

| Parámetro | Valor |
|---|---|
| TCP_HOST | 127.0.0.1 |
| TCP_PORT | 9001 |
| TCP_TIMEOUT_SECONDS | 3 |
| RPC_URL | http://127.0.0.1:9002 |
| RPC_TIMEOUT_SECONDS | 15 |
| TCP_MAX_MESSAGE_BYTES | 65536 |
| NOTIFICACIONES_WS_URL | ws://127.0.0.1:9003/ws/interno/notificaciones |
| NOTIFICACIONES_WS_TIMEOUT_SECONDS | 3 |

Los valores pueden modificarse mediante variables de entorno.

Los puertos son provisionales (IMPORTANTE).

## 11. Ejecución del servicio

Desde la carpeta principal del repositorio, activar primero el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Iniciar FastAPI:

```powershell
python -m uvicorn api.main:app --reload
```

Direcciones disponibles:

- Página principal: `http://127.0.0.1:8000/`
- Estado del servicio: `http://127.0.0.1:8000/health`
- Documentación interactiva: `http://127.0.0.1:8000/docs`

## 12. Pruebas automatizadas

Las pruebas se encuentran en la carpeta `pruebas/`.

Archivos:

- `test_api_rest.py`
- `test_coordinador.py`
- `test_notificaciones_cliente.py`

Ejecutar todas las pruebas:

```powershell
python -m pytest pruebas/ -v
```

En la última ejecución se obtuvieron 29 pruebas aprobadas.

Distribución:

| Archivo | Pruebas aprobadas |
|---|---:|
| test_api_rest.py | 15 |
| test_coordinador.py | 11 |
| test_notificaciones_cliente.py | 3 |
| Total | 29 |

Las pruebas de coordinación y notificaciones utilizan servicios simulados. Por tanto, estos resultados no representan todavía una integración real con los servidores TCP, XML-RPC y WebSocket de los otros integrantes.

## 13. Limitaciones actuales

La implementación tiene las siguientes limitaciones:

1. El almacenamiento en memoria pierde los datos al reiniciar el servidor.
2. Las tareas BackgroundTasks no constituyen una cola persistente.
3. No se implementa autenticación ni autorización de estudiantes y administradores.
4. No se realizan pagos bancarios ni facturación tributaria real.
5. El catálogo actual contiene productos provisionales.
6. La recuperación de pedidos debe solicitarse desde el código; todavía no existe una tarea automática de reconciliación.
7. Los clientes TCP, XML-RPC y WebSocket han sido preparados y probados mediante simulaciones, pero la conexión real depende de los servidores de los otros integrantes.
8. Los contratos y las direcciones de comunicación deben mantenerse coordinados con los responsables de cada mecanismo.

## 14. Estado del desarrollo

La API REST cuenta con endpoints para crear y consultar pedidos, generar estadísticas, controlar la idempotencia y mantener los estados oficiales.

También dispone de clientes de comunicación para TCP, XML-RPC y WebSockets, además de un coordinador que organiza el procesamiento en segundo plano.

La implementación inicial ha sido sometida a pruebas automatizadas. La integración distribuida completa queda pendiente de la disponibilidad y validación de los otros servicios del equipo.
