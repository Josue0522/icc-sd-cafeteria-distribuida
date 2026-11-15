# Bitácora de uso de IA

Este documento registra las consultas y el trabajo realizado con apoyo de herramientas de inteligencia artificial durante la práctica de Sistemas Distribuidos. El equipo es responsable de revisar y validar las decisiones y el código antes de integrarlos.

## Registro de intervenciones

| Fecha | Integrante | Herramienta de IA | Consulta realizada | Respuesta recibida | Decisión del equipo | Archivos o fragmentos afectados |
|---|---|---|---|---|---|---|
| 2026-11-12 | Codex | Codex | Preparar la estructura inicial, revisar `.gitignore`, dependencias y documentación; registrar esta intervención sin implementar los servicios. | Se revisó el estado del repositorio y se prepararon README, dependencias y documentación inicial; los cuatro mecanismos siguen pendientes. | Pendiente de revisión por el equipo antes del primer commit. | `README.md`, `requirements.txt`, `docs/arquitectura/README.md`, `docs/adr/README.md`, `docs/pruebas/README.md`, `docs/bitacora_ia.md` |
| 2026-11-14 | Mateo | ChatGPT | Apoyo para diseñar e implementar el módulo REST, pruebas y documentación. | Se proporcionaron explicaciones, propuestas de código, procedimientos de configuración y casos de prueba. También se analizaron y corrigieron errores encontrados durante el desarrollo. | El integrante revisó e incorporó las propuestas, ejecutó las pruebas localmente y comprobó los resultados. Se reportaron 29 pruebas PASSED. La integración real con los servicios externos permanece pendiente. | `api/main.py`, `api/modelos.py`, `api/almacen.py`, `api/configuracion.py`, `api/servicios.py`, `api/coordinador.py`, `api/notificaciones_cliente.py`, `pruebas/`, `docs/arquitectura/api-rest.md`, `docs/pruebas/README.md` |
| 2026-11-15 | Sebastián | ChatGPT | Consulta sobre el manejo de concurrencia e idempotencia en la librería xmlrpc.server de Python, manteniendo el estándar de UUIDs. | Documentación técnica resumida sobre el manejo de estados y excepciones en XML-RPC. | Se construyó la lógica del servidor RPC aplicando las prácticas recomendadas. Se pasaron 17 pruebas locales del módulo. | `cocina/servidor_rpc.py`, `cocina/cliente_rpc.py`, `pruebas/test_rpc_cocina.py` |
| 2026-11-15 | Sebastián | ChatGPT | Depuración de un error ModuleNotFoundError con FastAPI/Pydantic al ejecutar las pruebas en pytest en entorno Windows. | Diagnóstico del aislamiento del entorno virtual e instrucciones para regenerar el .venv. | Se purgó y reconfiguró el entorno virtual local. Las 46 pruebas generales ejecutaron exitosamente. | Entorno virtual local `.venv/`, guía para realización de pruebas del proyecto. |
| 2026-11-15 | Josué | ChatGPT | Revisar las ramas y usar el mensaje REST existente como referencia para proponer el protocolo TCP, sus validaciones y casos de prueba. | Codex preparó una primera propuesta para `protocolo.py`, `comprobantes.py`, `servidor_tcp.py`. | La propuesta usa el formato que construye `api/servicios.py`. | `docs/arquitectura/contratos-comunicacion.md`, `docs/arquitectura/tcp-caja.md`, `docs/pruebas/tcp-2026-11-15.md` |

## Consideraciones sobre el uso de IA

- Apoyo de desarrollo: Usamos la IA para aclarar dudas, preparar código y documentación. Cada integrante debe revisar lo que afecta a su módulo antes de integrarlo.

- Pruebas en local: Se registran los resultados observados y quién ejecutó cada comando. Las pruebas de componentes no sustituyen una prueba de integración con los cuatro servicios activos.

- Arquitectura: El equipo acuerda los contratos y valida las decisiones. Las propuestas y el código preparados con IA quedan sujetos a esa revisión.

