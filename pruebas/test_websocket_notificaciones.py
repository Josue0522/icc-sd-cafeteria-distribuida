
import asyncio
import json
import unittest
from uuid import uuid4
from unittest.mock import patch

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


    def test_recuperar_estado_desde_rest(self):

        # Crear un identificador de pedido
        pedido_id = str(uuid4())

        # Simular que REST tiene el pedido en estado LISTO
        evento_rest = {
            "tipo": "estado_actualizado",
            "pedido_id": pedido_id,
            "estado": "LISTO",
            "mensaje": "¡Tu pedido está listo!",
            "fecha": "2026-11-15T21:00:00Z"
        }

        # Importar el almacenamiento del servidor
        from notificaciones.main import pedidos

        # Simular pérdida de memoria de WebSocket
        pedidos.pop(pedido_id, None)

        # Simular la respuesta de la consulta a REST
        with patch(
            "notificaciones.main.consultar_estado_rest",
            return_value=evento_rest
        ) as consulta_rest:

            with TestClient(app) as cliente:

                # El estudiante se conecta después del reinicio
                with cliente.websocket_connect(
                    f"/ws/pedidos/{pedido_id}"
                ) as estudiante:

                    respuesta = estudiante.receive_json()

                    # Comprobar el identificador
                    self.assertEqual(
                        respuesta["pedido_id"],
                        pedido_id
                    )

                    # Comprobar el estado recuperado
                    self.assertEqual(
                        respuesta["estado"],
                        "LISTO"
                    )

                    # Comprobar el mensaje
                    self.assertEqual(
                        respuesta["mensaje"],
                        "¡Tu pedido está listo!"
                    )

            # Comprobar que se consultó REST
            consulta_rest.assert_called_once_with(pedido_id)

        # Limpiar los datos de prueba
        pedidos.pop(pedido_id, None)



if __name__ == "__main__":
    unittest.main()
