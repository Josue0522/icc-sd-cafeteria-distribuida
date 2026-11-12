# Cafetería distribuida

Este proyecto es una práctica de Sistemas Distribuidos. La idea es que un estudiante pueda hacer un pedido desde una página web y consultar cómo avanza.

La aplicación se dividirá en estos componentes:

- `api/`: crear y consultar pedidos mediante REST con FastAPI.
- `caja_facturacion/`: procesar la venta usando sockets TCP.
- `cocina/`: recibir solicitudes de preparación por XML-RPC.
- `notificaciones/` y `web/`: enviar avisos por WebSockets y mostrar la interfaz.

Los datos podrán mantenerse en memoria. No se utilizará Kafka ni una base de datos externa.

## Equipo

- Mateo: API REST (`feature/rest-pedidos`).
- Sebastián: cocina y XML-RPC (`feature/rpc-cocina`).
- Josué: caja y sockets TCP (`feature/tcp-caja`).
- Bryan: WebSockets e interfaz (`feature/websocket-notificaciones`).

## Carpetas

```text
api/                  API REST
caja_facturacion/     Caja y facturación
cocina/               Servicio de cocina
notificaciones/       Avisos en tiempo real
web/                  Interfaz web
pruebas/              Pruebas
docs/                 Documentación del proyecto
```

## Estado

Por ahora está preparada la estructura y la documentación inicial. Los servicios y las pruebas todavía no están implementados.
