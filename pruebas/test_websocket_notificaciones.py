
import asyncio
import json
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from notificaciones.main import app


class PruebasWebSocket(unittest.TestCase):

    def test_notificaciones_por_pedido(self):

        pedido_1 = str(uuid4())
        pedido_2 = str(uuid4())

        with TestClient(app) as cliente:

            with cliente.websocket_connect(
                f"/ws/pedidos/{pedido_1}"
            ) as estudiante_1:

                with cliente.websocket_connect(
                    f"/ws/pedidos/{pedido_2}"
                ) as estudiante_2:

                    with cliente.websocket_connect(
                        "/ws/interno/notificaciones"
                    ) as api:

                        # Enviar una actualización al pedido 1
                        api.send_json({
                            "tipo": "estado_actualizado",
                            "pedido_id": pedido_1,
                            "estado": "LISTO",
                            "mensaje": "¡Tu pedido está listo!",
                            "fecha": "2026-11-15T20:00:00Z"
                        })

                        respuesta_1 = estudiante_1.receive_json()

                        self.assertEqual(
                            respuesta_1["pedido_id"],
                            pedido_1
                        )

                        self.assertEqual(
                            respuesta_1["estado"],
                            "LISTO"
                        )

                        # Enviar una actualización distinta al pedido 2
                        api.send_json({
                            "tipo": "estado_actualizado",
                            "pedido_id": pedido_2,
                            "estado": "EN_PREPARACION",
                            "mensaje": "Tu pedido está siendo preparado.",
                            "fecha": "2026-11-15T20:01:00Z"
                        })

                        respuesta_2 = estudiante_2.receive_json()

                        self.assertEqual(
                            respuesta_2["pedido_id"],
                            pedido_2
                        )

                        self.assertEqual(
                            respuesta_2["estado"],
                            "EN_PREPARACION"
                        )


if __name__ == "__main__":
    unittest.main()
