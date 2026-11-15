import argparse
import json
import os
from uuid import uuid4
from xmlrpc.client import Fault, ProtocolError

from cocina.cliente_rpc import llamar_cocina


def main():
    parser = argparse.ArgumentParser(description="Prueba manual del servidor XML-RPC")
    parser.add_argument("--id", default=None, help="UUID; omitir para generar uno nuevo")
    parser.add_argument("--url", default=os.getenv("RPC_URL", "http://127.0.0.1:9002"))
    args = parser.parse_args()
    pedido_id = args.id or str(uuid4())
    productos = [
        {"producto_id": "CAF-001", "nombre": "Café americano", "cantidad": 2},
        {"producto_id": "SAN-001", "nombre": "Sándwich", "cantidad": 1},
    ]
    try:
        respuesta = llamar_cocina(pedido_id, productos, url=args.url)
    except (OSError, TimeoutError, Fault, ProtocolError) as error:
        print(f"Error de conexión RPC: {error}")
        raise SystemExit(1) from error
    print(json.dumps(respuesta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
