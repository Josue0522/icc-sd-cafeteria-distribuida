# Bitácora de uso de IA

Se documentan las interacciones con herramientas de IA que afecten el proyecto. La tabla inicial queda disponible para futuras consultas del equipo.

| Fecha | Integrante | Herramienta de IA | Consulta realizada | Respuesta recibida | Decisión del equipo | Archivos o fragmentos afectados |
|---|---|---|---|---|---|---|
| 2026-11-12 | Codex | Codex | Preparar la estructura inicial, revisar `.gitignore`, dependencias y documentación; registrar esta intervención sin implementar los servicios. | Se revisó el estado del repositorio y se prepararon README, dependencias y documentación inicial; los cuatro mecanismos siguen pendientes. | Pendiente de revisión por el equipo antes del primer commit. | `README.md`, `requirements.txt`, `docs/arquitectura/README.md`, `docs/adr/README.md`, `docs/pruebas/README.md`, `docs/bitacora_ia.md` |


| 2026-11-14 | Mateo | ChatGPT | Apoyo para diseñar e implementar el módulo REST, pruebas y documentación. | Se proporcionaron explicaciones, propuestas de código, procedimientos de configuración y casos de prueba. También se analizaron y corrigieron errores encontrados durante el desarrollo. | El integrante revisó e incorporó las propuestas, ejecutó las pruebas localmente y comprobó los resultados. Se reportaron 29 pruebas PASSED. La integración real con los servicios externos permanece pendiente. | `api/main.py`, `api/modelos.py`, `api/almacen.py`, `api/configuracion.py`, `api/servicios.py`, `api/coordinador.py`, `api/notificaciones_cliente.py`, `pruebas/`, `docs/arquitectura/api-rest.md`, `docs/pruebas/README.md` |

