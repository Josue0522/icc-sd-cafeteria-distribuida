# Pruebas del mecanismo WebSocket
 
**Mecanismo:** WebSockets  
**Tecnologías:** Python, FastAPI y JavaScript  
**Componente:** Servicio de notificaciones

## Casos de prueba

### 01. Conexión WebSocket

Ingresar un UUID de pedido válido en la interfaz web y establecer la conexión.

**Resultado esperado:** El navegador establece una conexión WebSocket con el servidor.

**Resultado obtenido:** La interfaz mostró el mensaje de conexión y el servidor registró la conexión del estudiante.


### 02. Integración con la API REST

Crear un pedido desde POST /pedidos y conectar la interfaz WebSocket utilizando el UUID generado.

**Resultado esperado:** El estudiante recibe los cambios de estado publicados por la API REST.

**Resultado obtenido:** Se recibieron notificaciones correspondientes a los estados del pedido, incluyendo PENDIENTE_CAJA y LISTO.

### 03. Reconexión del estudiante

Conectar un estudiante, cerrar la pestaña y volver a conectarse al mismo pedido sin reiniciar el servidor WebSocket.

**Resultado esperado:** El servidor envía el último estado almacenado.

**Resultado obtenido:** Se recuperó la notificación «¡Tu pedido está listo!».

### 04. Múltiples conexiones simultáneas

Crear dos pedidos diferentes y abrir dos pestañas del navegador, cada una conectada a su UUID.

**Resultado esperado:** El servidor acepta ambas conexiones y mantiene la asociación con sus pedidos.

**Resultado obtenido:** Ambas conexiones fueron aceptadas y cada interfaz mostró el estado de su pedido.

### 05. Prueba automatizada de enrutamiento

Ejecutar el comando:

`python -m unittest pruebas.test_websocket_notificaciones -v`

**Resultado esperado:** Los mensajes de prueba recibidos coinciden con el UUID y estado esperados.

**Resultado obtenido:** Se ejecutó una prueba automatizada sin errores, con resultado `OK`.

### 06. Fallo del servicio WebSocket

Detener el servidor WebSocket y crear un nuevo pedido mediante REST, manteniendo operativos los servicios de caja y cocina.

**Resultado esperado:** El procesamiento del pedido continúa aunque el servicio de notificaciones no esté disponible.

**Resultado obtenido:** El pedido fue procesado y alcanzó el estado `LISTO`.

### 07. Recuperación de estado desde REST

Crear un pedido, verificar que exista en REST, reiniciar únicamente WebSocket y reconectar la interfaz del estudiante utilizando su UUID.

**Resultado esperado:** WebSocket consulta el estado oficial desde REST y lo muestra al estudiante.

**Resultado obtenido:** REST respondió `200 OK` y la interfaz mostró «¡Tu pedido está listo!».

## Conclusión

Las pruebas realizadas demostraron que WebSockets permite recibir notificaciones de los pedidos de la cafetería y recuperar el último estado disponible.

La integración con REST permite recuperar el estado oficial después de reiniciar WebSocket, mejorando la recuperación ante fallos del sistema distribuido.