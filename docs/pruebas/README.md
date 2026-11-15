## Registro de pruebas — Módulo REST

**Fecha de ejecución:** 14/11/2026

**Responsable:** Mateo.

**Entorno:** Windows PowerShell, Python 3.14.2, entorno virtual `.venv`.

**Herramienta:** Pytest 9.2.0 y FastAPI TestClient.

### Comando ejecutado

```powershell
python -m pytest pruebas/ -v
```

### Resultados obtenidos

| Archivo | Pruebas aprobadas |
|---|---:|
| `test_api_rest.py` | 15 |
| `test_coordinador.py` | 11 |
| `test_notificaciones_cliente.py` | 3 |
| **Total** | **29** |

**Resultado observado:** las 29 pruebas finalizaron con estado PASSED.

### Funcionalidades verificadas

- Creación y consulta de pedidos.
- Validación de productos y cantidades.
- Idempotencia de solicitudes.
- Detección de conflictos de claves.
- Generación de estadísticas.
- Transiciones válidas de estados.
- Coordinación de caja y cocina mediante servicios simulados.
- Manejo de timeouts y errores de comunicación simulados.
- Recuperación de pedidos pendientes.
- Construcción y envío simulado de notificaciones WebSocket.

### Limitaciones de las pruebas

Las pruebas de TCP, XML-RPC y WebSockets utilizan servicios simulados para comprobar el comportamiento de la API.

Por tanto, los resultados no representan todavía una integración real entre los cuatro mecanismos.

La comunicación real deberá verificarse cuando estén disponibles los servidores implementados por los demás integrantes.

### Evidencia

La salida de Pytest obtenida en la terminal de Visual Studio Code constituye la evidencia de ejecución de estas pruebas.

## Otros registros

- [Resultados TCP y suite completa del 15/11/2026](tcp-2026-11-15.md)
