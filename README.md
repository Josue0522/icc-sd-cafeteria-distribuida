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



## Estado del desarrollo

El proyecto cuenta con la estructura inicial y el desarrollo del módulo API REST.

### Implementado inicialmente

- API REST desarrollada con FastAPI.
- Modelos y validaciones mediante Pydantic.
- Almacenamiento temporal de pedidos y catálogo en memoria.
- Creación y consulta de pedidos.
- Control de idempotencia.
- Generación de estadísticas de ventas.
- Control de transiciones de estado.
- Coordinador de pedidos con procesamiento en segundo plano.
- Clientes preparados para comunicación TCP y XML-RPC.
- Cliente preparado para publicar notificaciones mediante WebSockets.
- Pruebas automatizadas de REST, coordinación y notificaciones.

### Pendiente

- Implementación de los servidores TCP, XML-RPC y WebSocket por sus respectivos responsables.
- Integración real entre los cuatro mecanismos.
- Pruebas de funcionamiento completo del sistema distribuido.
- Revisión y validación final de la arquitectura por el equipo.

El almacenamiento actual utiliza memoria y no una base de datos externa.



## Ejecución del módulo REST

Desde la carpeta principal del repositorio, activar el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Iniciar la API:

```powershell
python -m uvicorn api.main:app --reload
```

La documentación interactiva estará disponible en:

http://127.0.0.1:8000/docs

Para ejecutar las pruebas automatizadas:

```powershell
python -m pytest pruebas/ -v
```