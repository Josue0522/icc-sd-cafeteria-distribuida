# Cafetería distribuida

Sistema distribuido para gestionar pedidos de una cafetería universitaria, desarrollado como práctica académica de Sistemas Distribuidos.

## Objetivo académico

Explorar e integrar distintos mecanismos de comunicación entre componentes independientes, documentando su arquitectura, colaboración y pruebas.

## Arquitectura propuesta

La solución se organizará en servicios especializados que colaborarán en el ciclo de vida de un pedido:

- **REST (`api/`)**: creación y consulta de pedidos.
- **RPC/XML-RPC (`cocina/`)**: comunicación con el servicio de cocina.
- **Sockets TCP (`caja_facturacion/`)**: caja y facturación.
- **WebSockets (`notificaciones/`, `web/`)**: notificaciones en tiempo real e interfaz web.

Los pedidos podrán almacenarse en memoria durante esta etapa. No se utilizará Kafka.

## Tecnologías previstas

Python, FastAPI, Uvicorn, bibliotecas estándar de Python, HTML, CSS y JavaScript. Para pruebas se prevén pytest y httpx.

## Organización del equipo

| Integrante | Responsabilidad | Carpeta | Rama propuesta |
|---|---|---|---|
| Mateo | REST | `api/` | `feature/rest-pedidos` |
| Sebastián | RPC | `cocina/` | `feature/rpc-cocina` |
| Josué | Sockets TCP | `caja_facturacion/` | `feature/tcp-caja` |
| Bryan | WebSockets e interfaz web | `notificaciones/`, `web/` | `feature/websocket-notificaciones` |

Las ramas son propuestas de trabajo; todavía no se han creado. Todo el equipo participará en pruebas y documentación.

## Estructura de directorios

```text
api/                    Servicio REST
cocina/                 Servicio RPC/XML-RPC
caja_facturacion/       Servicio TCP de caja y facturación
notificaciones/         Notificaciones WebSocket
web/                    Interfaz web
pruebas/                Pruebas del proyecto
docs/arquitectura/      Documentación de arquitectura
docs/adr/               Registros de decisiones arquitectónicas
docs/pruebas/           Evidencias y resultados reales de pruebas
docs/bitacora_ia.md     Registro de asistencia de herramientas de IA
```

## Requisitos previos

- Python 3.10 o posterior.
- Git.
- Windows PowerShell o una terminal compatible.

## Preparar el entorno en Windows

Desde la raíz del repositorio, crea y activa un entorno virtual:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, se puede ejecutar desde una terminal CMD:

```cmd
.venv\Scripts\activate.bat
```

Instala las dependencias declaradas con:

```powershell
python -m pip install -r requirements.txt
```

## Estado del desarrollo

**Preparación inicial:** estructura de carpetas y documentación base. Los servicios REST, RPC/XML-RPC, TCP y WebSocket todavía están pendientes de implementación; no se afirma que estén funcionando. Las pruebas de integración y sus resultados también están pendientes.
