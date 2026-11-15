import os
from xmlrpc.client import ServerProxy, Transport


class TransporteConTimeout(Transport):
    def __init__(self, segundos: float):
        super().__init__()
        self.segundos = segundos

    def make_connection(self, host):
        conexion = super().make_connection(host)
        conexion.timeout = self.segundos
        return conexion


def llamar_cocina(pedido_id: str, productos: list[dict], url: str | None = None, timeout: float = 15.0):
    url = url or os.getenv("RPC_URL", "http://127.0.0.1:9002")
    with ServerProxy(url, allow_none=False, transport=TransporteConTimeout(timeout)) as servidor:
        return servidor.preparar_pedido(pedido_id, productos)
