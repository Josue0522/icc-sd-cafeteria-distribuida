# Mecanismo WebSocket — Notificaciones de pedidos

## 1. Objetivo

El servicio de notificaciones WebSocket permite informar a los estudiantes sobre los cambios de estado de sus pedidos en la cafetería universitaria.

Su función principal es establecer una comunicación bidireccional y persistente entre el servidor de notificaciones y el navegador.

## 2. Tecnologías utilizadas

- **Python:** lenguaje utilizado para implementar el servidor.
- **FastAPI:** framework que permite gestionar conexiones WebSocket.
- **WebSockets:** mecanismo de comunicación en tiempo real.
- **JavaScript:** permite establecer conexiones WebSocket desde el navegador.
- **JSON:** formato utilizado para intercambiar las notificaciones.
- **Uvicorn:** servidor utilizado para ejecutar la aplicación FastAPI.

## 3. Arquitectura del servicio

El sistema utiliza dos conexiones WebSocket:

**Comunicación interna: API REST → WebSocket**

La API envía eventos cuando se actualiza el estado oficial de un pedido.

Endpoint:

`ws://127.0.0.1:9003/ws/interno/notificaciones`

**Comunicación externa: WebSocket → Estudiante**

El estudiante establece una conexión utilizando el UUID de su pedido.

Endpoint:

`ws://127.0.0.1:9003/ws/pedidos/{pedido_id}`

El servidor organiza las conexiones por identificador de pedido, permitiendo enviar actualizaciones a los clientes asociados.

## 4. Formato de los eventos

Los mensajes se transmiten mediante JSON y contienen la información necesaria para identificar el pedido y mostrar su estado.

Ejemplo:

```json
{
  "tipo": "estado_actualizado",
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "LISTO",
  "mensaje": "¡Tu pedido está listo!",
  "fecha": "2026-11-15T21:00:00Z"
}
```

## 5. Funcionamiento

1. El estudiante crea un pedido mediante la API REST.
2. La API registra el pedido y coordina las operaciones de caja y cocina.
3. Cuando cambia el estado del pedido, la API construye un evento JSON.
4. La API envía el evento al servidor WebSocket mediante la conexión interna.
5. WebSocket identifica las conexiones asociadas al UUID del pedido.
6. El servidor envía la notificación a los estudiantes conectados a ese pedido.
7. La interfaz web muestra el mensaje recibido.

Los estados utilizados incluyen `RECIBIDO`, `PENDIENTE_CAJA`, `VENTA_CONFIRMADA`, `EN_PREPARACION`, `LISTO`, `ERROR_CAJA` y `ERROR_COCINA`.

## 6. Manejo de conexiones

El servidor utiliza un diccionario para organizar los estudiantes conectados según su identificador de pedido.

Cada pedido puede tener varias conexiones activas.

Cuando un estudiante se desconecta, el servidor retira su conexión de la lista correspondiente sin eliminar el pedido registrado por REST.

Si ocurre un error al enviar una notificación, el servidor intenta retirar la conexión afectada.

## 7. Reconexión y recuperación de estados

El servicio conserva temporalmente el último evento recibido de cada pedido en memoria.

Cuando un estudiante vuelve a conectarse, WebSocket puede enviar el último evento almacenado.

Si el servidor perdió esa información al reiniciarse, consulta el estado oficial mediante:

`GET http://127.0.0.1:8000/pedidos/{pedido_id}`

La respuesta de REST se transforma al formato del evento WebSocket y se envía al estudiante.

Esta recuperación depende de que REST esté disponible y conserve el pedido. Si ambas aplicaciones se reinician, los datos almacenados únicamente en memoria pueden perderse.

## 8. Ejecución del servicio

Desde la raíz del proyecto y con el entorno virtual activado:

```powershell
python -m uvicorn notificaciones.main:app --reload --port 9003
```

Para utilizar la interfaz del estudiante, abrir `web/index.html` mediante un servidor web local e introducir el UUID de un pedido existente.

La API REST utiliza el puerto `8000` en el entorno de pruebas.


## 9. Conclusión

La implementación de WebSockets permite entregar notificaciones sobre los pedidos.

Las pruebas realizadas demostraron que el servidor puede atender conexiones simultáneas, recibir eventos de la API, detectar desconexiones y recuperar el estado oficial del pedido después de reiniciar el servicio de notificaciones.
