# ADR-004: Mecanismo de comunicación WebSockets para notificaciones

## Estado

Propuesto.

## Contexto

El sistema de la cafetería universitaria necesita un sistema para informar a los estudiantes sobre los cambios de estado de sus pedidos. 

El objetivo está en seleccionar un mecanismo que permita enviar notificaciones de manera automática. Así el estudiante no tiene que consultar constantemente el servidor.

## Alternativas evaluadas

| Alternativa | Contexto | Ventajas | Desventajas |
|---|---|---|---|
| REST | Consultar periódicamente el estado de los pedidos mediante HTTP. | Implementación sencilla y amplia compatibilidad con navegadores. | Requiere consultas repetidas para detectar cambios por lo que puede generar solicitudes innecesarias. |
| Sockets TCP | Establece comunicación directa entre procesos mediante una conexión TCP. | Comunicación bidireccional y baja latencia. | No puede utilizarse directamente como socket TCP tradicional desde el navegador. |
| RPC/gRPC | Invoca operaciones remotas entre componentes del sistema. | Facilita la comunicación entre servicios. | No es la alternativa más sencilla para notificaciones directas al navegador. |
| WebSockets | Mantiene una conexión persistente entre el servidor y el navegador. | Comunicación bidireccional y notificaciones en tiempo real. | Las desconexiones necesitan tratamiento especial. |

## Decisión

Se propone utilizar WebSockets como mecanismo para el servicio de notificaciones de la cafetería.

Este mecanismo otorgará la capacidad de manetener una conexión entre el navegador del cliente y el servidor de notificacoines, de tal manera que los cambios de estado de los pedidos se enviarán de manera automática.

El servicio establece conexiones con los estudiantes mediante la ruta:

/ws/pedidos/{pedido_id}

Además, recibe los eventos enviados por la API REST mediante:

/ws/interno/notificaciones

## Justificación

Consideramos adecuado utilizar WebSockets porque permite que el servidor envíe información al estudiante sin la necesidad de esperar una nueva solicitud HTTP. Como en el caso de REST que necesita consultas periódicas.

También, cada conexión se relaciona con un identificador de pedido, lo que permite enviar notificaciones independientes a los estudiantes correspondientes.

Además cuando el servicio WebSocket pierde su información al reiniciarse, puede consultar el estado oficial mediante GET /pedidos/{pedido_id} de la API REST, siempre que el pedido continúe disponible.


### Atributos de calidad beneficiados

**Rendimiento:** reduce las consultas HTTP para verificar cambios de estado.

**Latencia:** envía las notificaciones cuando el servidor recibe una actualización.

**Disponibilidad:** es capaz de recuperar el último estado registrado cuando un estudiante vuelve a conectarse.

## Consecuencias

### Consecuencias positivas

1. Los estudiantes reciben notificaciones automáticamente.
2. Comunicación bidireccional entre cliente y servidor.
3. Se reduce la necesidad de utilizar consultas HTTP periódicas.

### Consecuencias negativas

1. Los mensajes no se entregan en ese instante cuando el estudiante está desconectado.
2. Como los estados se almacenan en memoria. Es posible perderlos si el servidor llegará a caerse. 
3. Se requiere una implementación de autenticación y autorización para restringir que un estudiante consulte pedidos ajenos.
