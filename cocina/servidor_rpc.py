import argparse
import json
import logging
import threading
import time
from socketserver import ThreadingMixIn
from uuid import UUID
from xmlrpc.server import SimpleXMLRPCServer

LOG = logging.getLogger("cocina.rpc")


class ServicioCocina:
    """Prepara cada pedido una sola vez mientras el proceso esté activo."""

    def __init__(self, segundos_preparacion: float = 2.0, simular_error: bool = False):
        if segundos_preparacion < 0:
            raise ValueError("El tiempo de preparación no puede ser negativo")
        self.segundos_preparacion = segundos_preparacion
        self.simular_error = simular_error
        self._pedidos: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.preparaciones_iniciadas = 0  # Métrica para las pruebas de duplicados.

    def ping(self) -> dict:
        """Método remoto para comprobar disponibilidad del servidor."""
        return {"ok": True, "servicio": "cocina-rpc"}

    @staticmethod
    def _validar(pedido_id, productos) -> str | None:
        if not isinstance(pedido_id, str):
            return "pedido_id debe ser un UUID representado como texto"
        try:
            UUID(pedido_id)
        except (ValueError, AttributeError):
            return "pedido_id no es un UUID válido"

        if not isinstance(productos, list) or not productos:
            return "productos debe ser una lista no vacía"
        for producto in productos:
            if not isinstance(producto, dict):
                return "Cada producto debe ser un objeto"
            if not isinstance(producto.get("producto_id"), str) or not producto["producto_id"].strip():
                return "Falta producto_id válido"
            if not isinstance(producto.get("nombre"), str) or not producto["nombre"].strip():
                return "Falta nombre válido"
            cantidad = producto.get("cantidad")
            if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
                return "cantidad debe ser un entero positivo"
        return None

    @staticmethod
    def _respuesta_error(pedido_id, mensaje: str, codigo: str) -> dict:
        return {
            "ok": False,
            "pedido_id": str(pedido_id),
            "estado": "ERROR_COCINA",
            "mensaje": mensaje,
            "codigo": codigo,
        }

    def preparar_pedido(self, pedido_id: str, productos: list[dict]) -> dict:
        """Operación RPC requerida por api.servicios.preparar_pedido_rpc.

        Si se repite el mismo UUID con el mismo contenido, espera/reutiliza
        el resultado original; no simula una segunda preparación.
        """
        error = self._validar(pedido_id, productos)
        if error:
            return self._respuesta_error(pedido_id, error, "PEDIDO_INVALIDO")

        clave = str(UUID(pedido_id))
        # Solo los campos enviados por Mateo forman la huella de idempotencia.
        datos = [
            {"producto_id": p["producto_id"], "nombre": p["nombre"], "cantidad": p["cantidad"]}
            for p in productos
        ]
        huella = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

        with self._lock:
            registro = self._pedidos.get(clave)
            es_nuevo = registro is None
            if es_nuevo:
                registro = {
                    "huella": huella,
                    "estado": "EN_PREPARACION",
                    "mensaje": "Pedido en preparación",
                    "terminado": threading.Event(),
                }
                self._pedidos[clave] = registro
                self.preparaciones_iniciadas += 1
            elif registro["huella"] != huella:
                return self._respuesta_error(
                    pedido_id,
                    "El pedido ya se registró con productos diferentes",
                    "PEDIDO_INCONSISTENTE",
                )

        if es_nuevo:
            LOG.info("Iniciando preparación %s", clave)
            try:
                time.sleep(self.segundos_preparacion)
                if self.simular_error:
                    raise RuntimeError("Fallo simulado de preparación")
                estado = "LISTO"
                mensaje = "Pedido preparado correctamente"
            except Exception:
                LOG.exception("No se pudo preparar el pedido %s", clave)
                estado = "ERROR_COCINA"
                mensaje = "No fue posible preparar el pedido"
            finally:
                with self._lock:
                    registro["estado"] = estado
                    registro["mensaje"] = mensaje
                    registro["terminado"].set()
            LOG.info("Pedido %s: %s", clave, estado)
        else:
            # ThreadingMixIn permite que un reintento espere sin bloquear
            # las solicitudes de otros pedidos.
            registro["terminado"].wait()

        with self._lock:
            return {
                "ok": registro["estado"] == "LISTO",
                "pedido_id": pedido_id,
                "estado": registro["estado"],
                "mensaje": registro["mensaje"],
                "duplicado": not es_nuevo,
            }

    def consultar_pedido(self, pedido_id: str) -> dict:
        """Método adicional útil si la API perdió la respuesta RPC."""
        if not isinstance(pedido_id, str):
            return self._respuesta_error(pedido_id, "UUID inválido", "PEDIDO_INVALIDO")
        try:
            clave = str(UUID(pedido_id))
        except ValueError:
            return self._respuesta_error(pedido_id, "UUID inválido", "PEDIDO_INVALIDO")
        with self._lock:
            registro = self._pedidos.get(clave)
            if registro is None:
                return self._respuesta_error(pedido_id, "Pedido no encontrado", "NO_ENCONTRADO")
            return {
                "ok": registro["estado"] != "ERROR_COCINA",
                "pedido_id": pedido_id,
                "estado": registro["estado"],
                "mensaje": registro["mensaje"],
            }


class ServidorXMLRPC(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True
    allow_reuse_address = True


def crear_servidor(
    host: str = "127.0.0.1",
    puerto: int = 9002,
    segundos_preparacion: float = 2.0,
    simular_error: bool = False,
):
    """Devuelve servidor y servicio para facilitar pruebas sin puertos fijos."""
    cocina = ServicioCocina(segundos_preparacion, simular_error)
    servidor = ServidorXMLRPC((host, puerto), allow_none=False, logRequests=False)
    servidor.register_function(cocina.ping, "ping")
    servidor.register_function(cocina.preparar_pedido, "preparar_pedido")
    servidor.register_function(cocina.consultar_pedido, "consultar_pedido")
    return servidor, cocina


def main():
    parser = argparse.ArgumentParser(description="Servicio de cocina XML-RPC")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--puerto", type=int, default=9002)
    parser.add_argument("--segundos", type=float, default=2.0)
    parser.add_argument("--simular-error", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    servidor, _ = crear_servidor(args.host, args.puerto, args.segundos, args.simular_error)
    print(f"[COCINA] Escuchando XML-RPC en http://{args.host}:{args.puerto}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[COCINA] Apagando servicio", flush=True)
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
