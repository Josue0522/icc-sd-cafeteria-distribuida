# Bitácora de uso de IA

Este documento registra las consultas de apoyo realizadas a herramientas de inteligencia artificial durante el desarrollo de la práctica de Sistemas Distribuidos.

El objetivo es documentar las dudas de sintaxis, configuración de entorno y validación de errores que el equipo resolvió con asistencia de IA, acelerando el proceso de investigación. La arquitectura, lógica de negocio y validación del código fueron realizadas íntegramente por el equipo.

## Registro de intervenciones

| Fecha | Integrante | Herramienta de IA | Consulta realizada | Respuesta recibida | Decisión del equipo | Archivos o fragmentos afectados |
|---|---|---|---|---|---|---|
| 2026-11-12 | Codex | Codex | Preparar la estructura inicial, revisar `.gitignore`, dependencias y documentación; registrar esta intervención sin implementar los servicios. | Se revisó el estado del repositorio y se prepararon README, dependencias y documentación inicial; los cuatro mecanismos siguen pendientes. | Pendiente de revisión por el equipo antes del primer commit. | `README.md`, `requirements.txt`, `docs/arquitectura/README.md`, `docs/adr/README.md`, `docs/pruebas/README.md`, `docs/bitacora_ia.md` |
| 2026-11-14 | Mateo | ChatGPT | Apoyo para diseñar e implementar el módulo REST, pruebas y documentación. | Se proporcionaron explicaciones, propuestas de código, procedimientos de configuración y casos de prueba. También se analizaron y corrigieron errores encontrados durante el desarrollo. | El integrante revisó e incorporó las propuestas, ejecutó las pruebas localmente y comprobó los resultados. Se reportaron 29 pruebas PASSED. La integración real con los servicios externos permanece pendiente. | `api/main.py`, `api/modelos.py`, `api/almacen.py`, `api/configuracion.py`, `api/servicios.py`, `api/coordinador.py`, `api/notificaciones_cliente.py`, `pruebas/`, `docs/arquitectura/api-rest.md`, `docs/pruebas/README.md` |
| 2026-11-15 | Sebastián | ChatGPT | Consulta sobre el manejo de concurrencia e idempotencia en la librería xmlrpc.server de Python, manteniendo el estándar de UUIDs. | Documentación técnica resumida sobre el manejo de estados y excepciones en XML-RPC. | Se construyó la lógica del servidor RPC aplicando las prácticas recomendadas. Se pasaron 17 pruebas locales del módulo. | `cocina/servidor_rpc.py`, `cocina/cliente_rpc.py`, `pruebas/test_rpc_cocina.py` |
| 2026-11-15 | Sebastián | ChatGPT | Depuración de un error ModuleNotFoundError con FastAPI/Pydantic al ejecutar las pruebas en pytest en entorno Windows. | Diagnóstico del aislamiento del entorno virtual e instrucciones para regenerar el .venv. | Se purgó y reconfiguró el entorno virtual local. Las 46 pruebas generales ejecutaron exitosamente. | Entorno virtual local `.venv/`, guía para realización de pruebas del proyecto. |

## Consideraciones sobre el uso de IA

- Copiloto, no reemplazo: Usamos la IA para ahorrarnos tiempo con el código repetitivo, configurar el entorno y debuggear errores rápidos, pero la lógica final la revisó el responsable de cada módulo.

- Pruebas en local: Ningún código sugerido se dio por bueno a la primera. Todo se verificó corriendo `pytest` en nuestros entornos locales para probar el perfecto funcionamiento del proyecto antes de hacer los commits.

- Arquitectura: Las decisiones de cómo se comunican los servicios son nuestras; la IA solo nos dio ideas de cómo implementar los protocolos que ya habíamos decidido usar.