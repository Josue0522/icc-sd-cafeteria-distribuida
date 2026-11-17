# ADR-002: Comunicación XML-RPC para el servicio de cocina

**Proyecto:** Sistema Distribuido de Gestión de Pedidos para una Cafetería Universitaria.  
**Responsable:** Sebastián Alvarado.  
**Fecha:** 15/11/2026.

## Estado

Propuesto. El módulo está implementado y probado; la decisión queda sujeta a revisión del equipo y a la integración final del sistema.

## Contexto

La API REST debe enviar los pedidos aceptados al servicio de cocina para que se preparen y conocer el resultado de esa operación. Cocina se ejecuta como un proceso independiente, por lo que ambos módulos necesitan un mecanismo de comunicación remota.

El servicio debe validar los identificadores y productos recibidos, atender solicitudes concurrentes, evitar preparar dos veces un mismo pedido y comunicar los errores de preparación o conexión. La API REST conserva el estado oficial del pedido.

## Alternativas evaluadas

| Alternativa | Contexto | Ventajas | Desventajas |
|---|---|---|---|
| REST | La API enviaría el pedido a un endpoint HTTP de cocina. | Usa un protocolo conocido y es sencillo de inspeccionar. | Añadiría un servicio HTTP para una operación interna entre procesos. |
| Sockets TCP | La API intercambiaría mensajes mediante una conexión TCP directa con cocina. | Permite comunicación directa y control explícito del protocolo. | Requiere definir el formato y el manejo de mensajes, errores y conexiones. |
| XML-RPC | La API invoca métodos remotos publicados por el servidor de cocina sobre HTTP. | Expone operaciones con nombres y parámetros definidos y cuenta con soporte en la biblioteca estándar de Python. | Requiere que cliente y servidor mantengan compatibles los nombres y estructuras de los métodos. |
| WebSockets | API y cocina mantendrían una conexión bidireccional persistente. | Permite intercambiar información en tiempo real. | Mantener una conexión persistente no es necesario para solicitar la preparación puntual de un pedido. |

## Decisión

Se propone utilizar XML-RPC sobre HTTP para la comunicación entre la API REST y el servicio de cocina. El servidor escucha por defecto en `http://127.0.0.1:9002`.

La API invoca `preparar_pedido(pedido_id, productos)`. Cocina valida el UUID y los productos, registra la operación, simula la preparación y devuelve un resultado que incluye el identificador, estado y mensaje. También publica `consultar_pedido(pedido_id)` para consultar el resultado registrado y `ping()` para comprobar la disponibilidad del servicio.

El servicio atiende solicitudes concurrentes. Si se repite un UUID con los mismos productos, espera o reutiliza el resultado de la operación original. Si el mismo UUID llega con productos diferentes, devuelve un error de inconsistencia. La API REST mantiene la autoridad sobre el estado oficial del pedido.

## Justificación

XML-RPC permite a la API solicitar una operación concreta en el proceso de cocina sin compartir su implementación interna. La biblioteca estándar `xmlrpc` proporciona las herramientas de cliente y servidor necesarias en Python.

La idempotencia evita repetir la preparación cuando llega de nuevo una solicitud equivalente. El control de concurrencia protege los registros compartidos y permite atender pedidos distintos al mismo tiempo. El método de consulta ofrece una forma de recuperar el resultado si la API no recibió la respuesta inicial.

## Atributos de calidad beneficiados

**Interoperabilidad:** cliente y servidor se comunican mediante operaciones remotas y estructuras acordadas.

**Fiabilidad:** la validación y la idempotencia controlan datos inválidos y solicitudes repetidas.

**Concurrencia:** el servidor puede atender solicitudes de más de un cliente simultáneamente.

**Mantenibilidad:** las responsabilidades de API y cocina permanecen separadas.

## Consecuencias

### Consecuencias positivas

1. La API puede solicitar la preparación sin acceder directamente a los datos internos del módulo de cocina.
2. El servicio valida pedidos y productos antes de procesarlos.
3. Las solicitudes repetidas con el mismo contenido reutilizan el resultado original.
4. Los métodos `consultar_pedido()` y `ping()` permiten consultar una operación y comprobar la disponibilidad del servicio.
5. El servicio procesa solicitudes concurrentes.

### Consecuencias negativas y limitaciones

1. Los pedidos y sus resultados se almacenan en memoria y se pierden al reiniciar el servidor.
2. La preparación se simula mediante una espera configurable; no hay hardware de cocina conectado.
3. El cliente REST todavía no utiliza `consultar_pedido()` para recuperar operaciones cuya respuesta se perdió.
4. Un tiempo de espera o una caída de conexión puede dejar a la API sin conocer de inmediato el resultado; debe manejarse el error y, cuando corresponda, consultar la operación.
5. La integración completa con los otros mecanismos debe validarse en el sistema integrado.

## Validación

La ejecución documentada de `pruebas/test_rpc_cocina.py` obtuvo 17 pruebas aprobadas. Las pruebas cubren preparación, validación, idempotencia, concurrencia, consulta y errores de comunicación. Este resultado valida el módulo RPC; por sí solo no confirma la integración completa del sistema.

## Referencias

- Documentación del servicio de cocina: `docs/arquitectura/rpc-cocina.md`.
- Contratos entre servicios: `docs/arquitectura/contratos-comunicacion.md`.
- Implementación del servidor: `cocina/servidor_rpc.py`.
- Pruebas del módulo: `pruebas/test_rpc_cocina.py`.
