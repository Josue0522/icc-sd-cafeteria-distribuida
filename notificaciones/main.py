
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI()

# Clientes conectados por número de pedido
conexiones = {}

# Estados de los pedidos
pedidos = {}

class EstadoPedido(BaseModel):
    estado: str


@app.websocket("/ws/{pedido_id}")
async def conectar_cliente(websocket: WebSocket, pedido_id: int):

    await websocket.accept()

    if pedido_id not in conexiones:
        conexiones[pedido_id] = []

    conexiones[pedido_id].append(websocket)

    print(f"Cliente conectado al pedido {pedido_id}")

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"Cliente desconectado del pedido {pedido_id}")

    finally:
        conexiones[pedido_id].remove(websocket)

        if not conexiones[pedido_id]:
            del conexiones[pedido_id]


@app.post("/pedidos/{pedido_id}/estado")
async def actualizar_estado(pedido_id: int, datos: EstadoPedido):

    pedidos[pedido_id] = datos.estado

    mensaje = {
        "pedido_id": pedido_id,
        "estado": datos.estado,
        "mensaje": f"Tu pedido está {datos.estado}"
    }

    for websocket in conexiones.get(pedido_id, [])[:]:
        try:
            await websocket.send_json(mensaje)
        except Exception:
            if websocket in conexiones.get(pedido_id, []):
                conexiones[pedido_id].remove(websocket)

    return mensaje
