
import json
import logging
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Servicio de Notificaciones WebSocket")

logger = logging.getLogger(__name__)

# Conexiones de estudiantes agrupadas por pedido
conexiones = {}

# Último evento recibido de cada pedido
pedidos = {}


# 1. Enviar una notificación a los estudiantes de un pedido
async def notificar_estudiantes(pedido_id, evento):

    for cliente in conexiones.get(pedido_id, [])[:]:
        try:
            await cliente.send_json(evento)

        except Exception:
            logger.warning(
                "No se pudo notificar al cliente del pedido %s",
                pedido_id
            )

            if cliente in conexiones.get(pedido_id, []):
                conexiones[pedido_id].remove(cliente)


# 2. Recibir los eventos enviados por la API REST
@app.websocket("/ws/interno/notificaciones")
async def recibir_notificacion(websocket: WebSocket):

    await websocket.accept()
    logger.info("API conectada al servicio de notificaciones")

    try:
        while True:

            mensaje = await websocket.receive_text()

            try:
                evento = json.loads(mensaje)

                if not isinstance(evento, dict):
                    raise ValueError("El evento debe ser un objeto JSON")

                if evento.get("tipo") != "estado_actualizado":
                    raise ValueError("Tipo de evento no válido")

                pedido_id = str(UUID(str(evento["pedido_id"])))

                if not isinstance(evento.get("estado"), str):
                    raise ValueError("Estado no válido")

                if not isinstance(evento.get("mensaje"), str):
                    raise ValueError("Mensaje no válido")

                if not isinstance(evento.get("fecha"), str):
                    raise ValueError("Fecha no válida")

            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                logger.warning("Se recibió un evento no válido")
                continue

            evento["pedido_id"] = pedido_id

            # Guardar el último estado recibido
            pedidos[pedido_id] = evento

            logger.info(
                "Pedido %s actualizado a %s",
                pedido_id,
                evento["estado"]
            )

            # Enviar a los estudiantes conectados
            await notificar_estudiantes(pedido_id, evento)

    except WebSocketDisconnect:
        logger.info("API desconectada del servicio de notificaciones")


# 3. Conectar al estudiante con su pedido
@app.websocket("/ws/pedidos/{pedido_id}")
async def conectar_estudiante(websocket: WebSocket, pedido_id: str):

    try:
        pedido_id = str(UUID(pedido_id))
    except ValueError:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    if pedido_id not in conexiones:
        conexiones[pedido_id] = []

    conexiones[pedido_id].append(websocket)

    logger.info("Estudiante conectado al pedido %s", pedido_id)

    try:

        # Recuperar el último evento al reconectarse
        if pedido_id in pedidos:
            await websocket.send_json(pedidos[pedido_id])

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("Estudiante desconectado del pedido %s", pedido_id)

    except Exception:
        logger.exception(
            "Error de conexión del pedido %s",
            pedido_id
        )

    finally:
        clientes = conexiones.get(pedido_id, [])

        if websocket in clientes:
            clientes.remove(websocket)

        if not clientes:
            conexiones.pop(pedido_id, None)
