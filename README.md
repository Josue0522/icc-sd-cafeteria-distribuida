# Cafetería distribuida

Práctica de Sistemas Distribuidos para gestionar pedidos de una cafetería universitaria. Los pedidos se crean por REST; la API coordina caja, cocina y las notificaciones del estudiante.

## Componentes

- `api/`: API REST con FastAPI y coordinación de pedidos.
- `cocina/`: servidor de cocina por XML-RPC.
- `caja_facturacion/`: módulo de caja por sockets TCP.
- `notificaciones/` y `web/`: avisos WebSocket e interfaz.

Los datos se guardan en memoria. No usamos una base de datos externa ni Kafka.

## Responsables

- Mateo: REST (`feature/rest-pedidos`).
- Sebastián: cocina/RPC (`feature/rpc-cocina`).
- Josué: caja/TCP (`branchJosue`).
- Bryan: WebSockets e interfaz (`feature/websocket-notificaciones`).

## Estado de esta rama

Se integraron los cambios de REST. La integración con caja y notificaciones está pendiente; el sistema completo todavía no está probado.

## Ejecutar la API

Con Python instalado, desde la raíz del proyecto:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

La documentación interactiva de FastAPI se encuentra en `http://127.0.0.1:8000/docs`.

Para ejecutar las pruebas automatizadas:

```powershell
python -m pytest pruebas/ -v
```
