# Cafetería distribuida

Práctica de Sistemas Distribuidos para gestionar pedidos de una cafetería universitaria. La API registra los pedidos y coordina caja, cocina y las notificaciones.

## Componentes

- `api/`: API REST con FastAPI.
- `cocina/`: servidor de preparación por XML-RPC.
- `caja_facturacion/`: caja y comprobantes simulados por sockets TCP.
- `notificaciones/`: servicio WebSocket para comunicar cambios de estado.
- `web/`: interfaz web para crear y consultar pedidos.

Los datos se guardan en memoria. Al reiniciar los servicios, los registros se pierden.

## Equipo

- Mateo: REST (`feature/rest-pedidos`).
- Sebastián: cocina/RPC (`feature/rpc-cocina`).
- Josué: caja/TCP (`branchJosue`).
- Bryan: WebSockets e interfaz (`feature/websocket-notificaciones`).

## Estado

Los módulos REST, XML-RPC, TCP, WebSocket y la interfaz web están incorporados al repositorio. Las instrucciones siguientes permiten iniciar los servicios localmente para probar el recorrido de un pedido.

## Preparar el entorno en Windows

Desde la raíz del repositorio, crea y activa el entorno virtual e instala las dependencias:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, permite la ejecución solo para la terminal actual y vuelve a activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

## Iniciar el sistema completo

Cada componente debe ejecutarse en una terminal distinta. Abre cinco terminales en la raíz del repositorio y activa `.venv` en cada una con:

```powershell
.venv\Scripts\Activate.ps1
```

**Terminal 1 - API REST** (puerto 8000):

```powershell
python -m uvicorn api.main:app --reload
```

La documentación de la API estará en `http://127.0.0.1:8000/docs`.

**Terminal 2 - Cocina XML-RPC** (puerto 9002):

```powershell
python -m cocina.servidor_rpc --puerto 9002 --segundos 2
```

**Terminal 3 - Caja TCP** (puerto 9001):

```powershell
python -m caja_facturacion.servidor_tcp
```

**Terminal 4 - Notificaciones WebSocket** (puerto 9003):

```powershell
python -m uvicorn notificaciones.main:app --reload --port 9003
```

**Terminal 5 - Interfaz web** (puerto 3000):

```powershell
python -m http.server 3000 --directory web
```

Abre `http://localhost:3000` en el navegador. La API permite solicitudes de la interfaz en ese puerto. Completa los datos del estudiante, selecciona al menos un producto y pulsa el botón para crear el pedido. La página mostrará su identificador y estado; las notificaciones aparecerán cuando cambie el estado.

Para detener cada servicio, vuelve a su terminal y pulsa `Ctrl+C`.

## Pruebas

Con el entorno virtual activo, ejecuta toda la suite:

```powershell
python -m pytest pruebas/ -v
```

Para ejecutar solamente las pruebas de caja TCP:

```powershell
python -m pytest pruebas/test_caja_tcp.py -v
```

Los resultados deben registrarse después de ejecutar las pruebas en el entorno local.
