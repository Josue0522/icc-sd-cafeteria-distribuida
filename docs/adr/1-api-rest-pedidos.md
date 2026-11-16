# ADR-001: Selección de REST para la gestión de pedidos

**Proyecto:** Sistema Distribuido de Gestión de Pedidos para una Cafetería Universitaria.

**Responsable:** Mateo.

**Fecha:** 16/11/2026.

## 1. Contexto

La cafetería universitaria necesita un mecanismo de comunicación que permita a los estudiantes realizar pedidos desde una página web o aplicación móvil y consultar su estado.

Además, la administración necesita consultar estadísticas de ventas y pedidos.

El sistema debe comunicarse con otros componentes distribuidos: caja y facturación mediante Sockets TCP, cocina mediante XML-RPC y notificaciones mediante WebSockets.

Por tanto, se necesita un mecanismo que permita recibir solicitudes de los clientes, validar información, gestionar pedidos y coordinar las operaciones internas.

## 2. Decisión

Se seleccionó REST como mecanismo de comunicación entre los clientes y la API principal del sistema, utilizando Python y FastAPI.

La API REST será responsable de:

- Recibir y validar los pedidos.
- Registrar los pedidos en memoria.
- Evitar solicitudes duplicadas mediante claves de idempotencia.
- Mantener el estado oficial de los pedidos.
- Coordinar la comunicación con caja y cocina.
- Permitir la consulta de pedidos.
- Generar estadísticas para la administración.

Se establecieron los siguientes endpoints:

| Método | Endpoint | Función |
|---|---|---|
| POST | `/pedidos` | Crear un pedido. |
| GET | `/pedidos/{pedido_id}` | Consultar un pedido. |
| GET | `/reportes/ventas` | Consultar estadísticas. |
| GET | `/health` | Verificar disponibilidad de la API. |

Para evitar pedidos duplicados, el endpoint de creación utiliza la cabecera `Idempotency-Key`.

Cada pedido tendrá un identificador UUID y los valores monetarios se manejarán internamente mediante `Decimal`, utilizando cadenas decimales en los mensajes JSON.

El procesamiento se ejecutará mediante tareas en segundo plano de FastAPI, permitiendo que la API atienda nuevas solicitudes mientras coordina las operaciones internas.

## 3. Alternativas consideradas

**Sockets TCP**

Permiten establecer conexiones directas e intercambiar mensajes entre componentes. Sin embargo, requieren definir un protocolo propio y no son la opción más conveniente para exponer una API de pedidos a aplicaciones web y móviles.

**RPC/XML-RPC**

Permite invocar funciones remotas entre servicios, pero está más orientado a la comunicación interna entre componentes que a la exposición de operaciones HTTP para los clientes.

**gRPC**

Ofrece comunicación eficiente y contratos estructurados entre servicios. Sin embargo, supone una complejidad adicional para integrar directamente los clientes web y móviles en comparación con una API HTTP convencional.

**WebSockets**

Permite comunicación bidireccional en tiempo real, pero no es la alternativa más adecuada para operaciones habituales de creación y consulta de recursos.

Por estas razones, REST se considera la opción apropiada para la comunicación con estudiantes y administración, mientras que los otros mecanismos cumplen funciones específicas dentro de la arquitectura.

## 4. Consecuencias positivas

- Facilita la comunicación entre la aplicación web, el dispositivo móvil y el servidor.
- Permite utilizar métodos HTTP conocidos para gestionar pedidos.
- FastAPI proporciona validación de datos mediante Pydantic y documentación automática con Swagger UI.
- Facilita las pruebas automatizadas de los endpoints.
- Separa las solicitudes de los clientes del procesamiento interno de los pedidos.
- Permite integrar los mecanismos TCP, RPC y WebSockets sin exponer sus protocolos directamente a los estudiantes.

## 5. Consecuencias negativas y limitaciones

- El almacenamiento en memoria implica que los pedidos se pierden cuando se reinicia el servidor.
- Las tareas BackgroundTasks no constituyen una cola persistente; una interrupción del proceso puede provocar la pérdida de tareas pendientes.
- Los tiempos de espera de los servicios internos pueden generar operaciones cuyo resultado todavía es desconocido.
- La integración depende de la compatibilidad de los contratos con los otros microservicios.
- No se implementa autenticación ni autorización en esta versión inicial.
- La solución está preparada para ejecutarse localmente y no representa todavía un despliegue distribuido completo.

## 6. Relación con los otros mecanismos

REST funciona como punto de entrada y coordinador principal del sistema.

Su comunicación con los demás componentes se realizará de la siguiente manera:

- **Sockets TCP:** envío de solicitudes de registro de ventas a caja y facturación, utilizando `pedido_id` y `operacion_id` para controlar duplicados.
- **XML-RPC:** invocación de `preparar_pedido(pedido_id, productos)` en el servicio de cocina.
- **WebSockets:** publicación de eventos de actualización de estado al servicio de notificaciones.

La API será responsable de conservar el estado oficial de cada pedido.

Los contratos específicos se encuentran documentados en `docs/arquitectura/contratos-comunicacion.md`.

## 7. Validación

La implementación inicial utiliza Python, FastAPI, Pydantic y almacenamiento en memoria.

Se desarrollaron pruebas automatizadas para comprobar:

- Creación y consulta de pedidos.
- Validación de datos.
- Idempotencia.
- Control de transiciones de estado.
- Generación de estadísticas.
- Coordinación de los servicios mediante respuestas simuladas.
- Manejo de errores y tiempos de espera.
- Publicación simulada de notificaciones.

En la última ejecución reportada se obtuvieron 29 pruebas aprobadas.

Las pruebas de comunicación con TCP, XML-RPC y WebSockets utilizan servicios simulados. La integración real permanece pendiente de la implementación de los servidores de los demás integrantes.

## 8. Referencias

- Documentación oficial de FastAPI: https://fastapi.tiangolo.com/
- Documentación oficial de Pydantic: https://docs.pydantic.dev/
- Contratos de comunicación del proyecto: `docs/arquitectura/contratos-comunicacion.md`
- Implementación del módulo REST: `api/`
