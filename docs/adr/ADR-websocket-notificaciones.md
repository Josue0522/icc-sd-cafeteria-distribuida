# ADR-003: Mecanismo de comunicación WebSockets para notificaciones

## Estado

Propuesto.

## Contexto

El sistema de la cafetería universitaria necesita un sistema para informar a los estudiantes sobre los cambios de estado de sus pedidos. 

El objetivo está en seleccionar un mecanismo que permita enviar notificaciones de manera automática. Así el estudiante no tiene que consultar constantemente el servidor.

## Alternativas evaluadas

| Alternativa | Contexto | Ventajas | Desventajas |
|---|---|---|---|
| REST | El estudiante consulta periódicamente el estado del pedido mediante solicitudes HTTP. | 1. Implementación sencilla. 2. Amplia compatibilidad con navegadores. | 1. Requiere consultas repetidas para detectar cambios. 2. Puede generar solicitudes innecesarias. |
| Sockets TCP | Establece comunicación directa entre procesos mediante una conexión TCP. | 1. Comunicación bidireccional. 2. Baja latencia. | 1. Requiere implementar más detalles del protocolo. 2. No puede utilizarse directamente como socket TCP tradicional desde el navegador. |
| RPC/gRPC | Permite invocar operaciones remotas entre componentes del sistema. | 1. Facilita la comunicación entre servicios. 2. Puede ofrecer buen rendimiento. | 1. No es la alternativa más sencilla para notificaciones directas al navegador. 2. Puede requerir herramientas adicionales. |
| WebSockets | Mantiene una conexión persistente entre el servidor y el navegador. | 1. Comunicación bidireccional. 2. Notificaciones en tiempo real. 3. Evita consultas periódicas. | 1. Requiere administrar conexiones activas. 2. Las desconexiones necesitan tratamiento especial. |

## Decisión

Se propone utilizar WebSockets como mecanismo para el servicio de notificaciones de la cafetería.

Este mecanismo otorgará la capacidad de manetener una conexión entre el navegador del cliente y el servidor de notificacoines, de tal manera que los cambios de estado de los pedidos se enviarán de manera automática.

## Justificación

Consideramos adecuado utilizar WebSockets porque permite que el servidor envíe información al estudiante sin la necesidad de esperar una nueva solicitud HTTP. En el caso de REST, necesita consultas periódicas.

Además, cada conexión se relaciona con un identificador de pedido, lo que permite enviar notificaciones independientes a los estudiantes correspondientes.

La implementación utiliza Python y FastAPI..

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
