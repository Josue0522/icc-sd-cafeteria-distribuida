# Cafetería distribuida

Práctica de Sistemas Distribuidos para gestionar pedidos de una cafetería universitaria. La API registra los pedidos y coordina caja, cocina y las notificaciones.

## Componentes

- `api/`: API REST con FastAPI.
- `cocina/`: servidor de preparación por XML-RPC.
- `caja_facturacion/`: caja y comprobantes por sockets TCP.
- `notificaciones/` y `web/`: avisos y página para el estudiante.

Los datos se guardan en memoria. No usamos una base de datos externa ni Kafka.

## Equipo

- Mateo: REST (`feature/rest-pedidos`).
- Sebastián: cocina/RPC (`feature/rpc-cocina`).
- Josué: caja/TCP (`branchJosue`).
- Bryan: WebSockets e interfaz (`feature/websocket-notificaciones`).

## Estado

En esta rama están los módulos REST y RPC. Caja TCP y WebSockets todavía están pendientes de integración. Aún falta comprobar el recorrido completo de un pedido con todos los servicios activos.

## Preparar el entorno en Windows

Desde la raíz del repositorio:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Iniciar la API:

```powershell
python -m uvicorn api.main:app --reload
```

La documentación de FastAPI estará en `http://127.0.0.1:8000/docs`.

Iniciar cocina en otra terminal:

```powershell
python -m cocina.servidor_rpc --puerto 9002 --segundos 2
```

Para ejecutar las pruebas:

```powershell
python -m pytest pruebas/ -v
```

Los resultados deben registrarse después de ejecutar las pruebas en el entorno local.
