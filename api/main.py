
"""
API REST del Sistema Distribuido de Gestión de Pedidos
para una Cafetería Universitaria.

"""

from uuid import UUID
from datetime import date
from fastapi.middleware.cors import CORSMiddleware

from fastapi import (
    FastAPI,
    BackgroundTasks,
    Header,
    Response,
    status,
)

from fastapi.responses import JSONResponse

from .almacen import (
    crear_pedido,
    obtener_pedido,
    ProductoNoEncontrado,
    ClaveIdempotenciaEnConflicto,
    obtener_estadisticas,
)

from .modelos import (
    SolicitudCrearPedido,
    PedidoRespuesta,
    ReporteVentas,
)

from .coordinador import procesar_pedido
from .notificaciones_cliente import publicar_estado_pedido


# 1. Crear la aplicación FastAPI

app = FastAPI(
    title="API REST - Cafetería Universitaria",
    description=(
        "API encargada de gestionar los pedidos de la "
        "cafetería universitaria y coordinar los servicios internos."
    ),
    version="0.2.0"
)

# Permitir solicitudes desde la interfaz web local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)


# 2. Endpoint inicial

@app.get("/", tags=["Inicio"])
async def inicio():
    return {
        "mensaje": "Sistema de Cafetería Universitaria",
        "servicio": "API REST",
        "estado": "funcionando"
    }


# 3. Comprobar el estado de la API

@app.get("/health", tags=["Estado del servicio"])
async def verificar_estado():
    return {
        "status": "ok",
        "servicio": "api-rest"
    }


# 4. Crear un pedido


@app.post(
    "/pedidos",
    response_model=PedidoRespuesta,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "model": PedidoRespuesta,
            "description": "Se devuelve un pedido existente por idempotencia.",
        }
    },
    tags=["Pedidos"]
)
def crear_pedido_endpoint(
    solicitud: SolicitudCrearPedido,
    background_tasks: BackgroundTasks,
    response: Response,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key"
    )
):
    """
    Registra un pedido y programa su procesamiento
    mediante una tarea en segundo plano.
    """

    if idempotency_key is None or not idempotency_key.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "codigo": "CLAVE_IDEMPOTENCIA_REQUERIDA",
                    "mensaje": "Debe enviar la cabecera Idempotency-Key",
                    "detalles": None
                }
            }
        )

    try:
        pedido, es_nuevo = crear_pedido(
            solicitud,
            idempotency_key
        )

    except ClaveIdempotenciaEnConflicto:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "codigo": "CONFLICTO_IDEMPOTENCIA",
                    "mensaje": (
                        "La clave ya fue utilizada con "
                        "datos diferentes."
                    ),
                    "detalles": None
                }
            }
        )

    except ProductoNoEncontrado as error:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "codigo": "PRODUCTO_NO_ENCONTRADO",
                    "mensaje": str(error),
                    "detalles": None
                }
            }
        )

    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "codigo": "SOLICITUD_INVALIDA",
                    "mensaje": str(error),
                    "detalles": None
                }
            }
        )

    if es_nuevo:

        # Notificar la recepción inicial del pedido.
        background_tasks.add_task(
            publicar_estado_pedido,
            pedido,
        )

        # Procesar la venta y preparación en segundo plano.
        background_tasks.add_task(
            procesar_pedido,
            pedido.pedido_id,
        )

        response.status_code = status.HTTP_202_ACCEPTED

    else:

        # No programamos otra tarea para un pedido repetido.
        response.status_code = status.HTTP_200_OK

    return pedido



# 5. Consultar un pedido

@app.get(
    "/pedidos/{pedido_id}",
    response_model=PedidoRespuesta,
    tags=["Pedidos"]
)
def consultar_pedido(pedido_id: UUID):
    """
    Busca un pedido mediante su identificador UUID.
    """

    pedido = obtener_pedido(pedido_id)

    if pedido is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "codigo": "PEDIDO_NO_ENCONTRADO",
                    "mensaje": "No existe un pedido con ese identificador.",
                    "detalles": None
                }
            }
        )

    return pedido



# 6. Consultar estadísticas de ventas

@app.get(
    "/reportes/ventas",
    response_model=ReporteVentas,
    tags=["Reportes"]
)
def consultar_estadisticas(
    desde: date | None = None,
    hasta: date | None = None,
):
    """
    Genera estadísticas de los pedidos y las ventas
    almacenadas en memoria.

    Los parámetros desde y hasta filtran por fecha
    de creación del pedido.
    """

    # Validar que el rango de fechas sea correcto.
    if desde is not None and hasta is not None and desde > hasta:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "codigo": "RANGO_FECHAS_INVALIDO",
                    "mensaje": (
                        "La fecha inicial no puede ser "
                        "posterior a la fecha final."
                    ),
                    "detalles": None
                }
            }
        )

    return obtener_estadisticas(desde, hasta)

