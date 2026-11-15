# Cafetería Distribuida

**Proyecto académico — Sistemas Distribuidos**

Sistema distribuido para la gestión de pedidos de una cafetería universitaria, desarrollado principalmente en Python mediante cuatro mecanismos de comunicación: **REST, XML-RPC, Sockets TCP y WebSockets**.

## 1. Descripción del proyecto

Este proyecto corresponde a una práctica de la asignatura Sistemas Distribuidos.

Su objetivo es implementar un sistema que permita a los estudiantes realizar pedidos desde una aplicación web, consultar su estado y recibir notificaciones cuando estén listos para retirarlos.

La solución utiliza una arquitectura distribuida en la que distintos componentes se encargan de recibir pedidos, procesar ventas, preparar productos y notificar cambios de estado.

Los mecanismos seleccionados son:

| Mecanismo | Componente | Responsabilidad |
|---|---|---|
| REST | API principal | Crear, validar, consultar y gestionar pedidos. |
| XML-RPC | Cocina | Procesar solicitudes remotas de preparación. |
| Sockets TCP | Caja y facturación | Registrar ventas y generar comprobantes simulados. |
| WebSockets | Notificaciones | Informar cambios de estado en tiempo real. |

El sistema utiliza almacenamiento en memoria y no requiere una base de datos externa. No se utiliza Kafka.

## 2. Equipo de desarrollo

| Integrante | Responsabilidad | Rama de desarrollo |
|---|---|---|
| Mateo | API REST y coordinación de pedidos | `feature/rest-pedidos` |
| Sebastián | Servidor de cocina mediante XML-RPC | `feature/rpc-cocina` |
| Josué | Caja y facturación mediante Sockets TCP | `feature/tcp-caja` |
| Bryan | Notificaciones WebSocket e interfaz web | `feature/websocket-notificaciones` |

Cada integrante desarrolla principalmente su mecanismo de comunicación y participa en las actividades de integración, documentación y pruebas.

## 3. Arquitectura del sistema

La arquitectura está organizada alrededor de una API REST principal que mantiene el estado oficial de los pedidos y coordina la comunicación con los demás servicios.

El flujo previsto es:

1. El estudiante crea un pedido mediante una solicitud REST.
2. La API valida los productos, cantidades y datos recibidos.
3. El pedido se registra en memoria, evitando duplicados.
4. La API solicita a caja y facturación el procesamiento de la venta mediante Sockets TCP.
5. Cuando la venta se confirma, la API solicita a cocina la preparación mediante XML-RPC.
6. Cocina procesa el pedido y devuelve el resultado.
7. La API actualiza el estado oficial del pedido.
8. El módulo WebSocket informa al estudiante cuando cambia el estado del pedido.

**Estado de integración:** la coordinación REST y la comunicación XML-RPC de cocina ya cuentan con pruebas exitosas. La integración completa con servidores TCP y WebSockets reales continúa pendiente.

### Estados del pedido

El flujo principal contempla los siguientes estados:

`RECIBIDO → VENTA_CONFIRMADA → EN_PREPARACION → LISTO`

También se consideran estados de error, incluyendo:

- `ERROR_CAJA`
- `ERROR_COCINA`

La API principal es responsable de mantener la consistencia de los estados del pedido.

## 4. Estructura del proyecto

```text
icc-sd-cafeteria-distribuida/
│
├── api/                         API REST y coordinación - Mateo
│   ├── main.py
│   ├── modelos.py
│   ├── almacen.py
│   ├── configuracion.py
│   ├── servicios.py
│   ├── coordinador.py
│   └── notificaciones_cliente.py
│
├── cocina/                      Servidor XML-RPC - Sebastián
│   ├── __init__.py
│   ├── servidor_rpc.py
│   ├── cliente_rpc.py
│   └── cliente_prueba.py
│
├── caja_facturacion/            Servidor TCP - Josué
│
├── notificaciones/              Notificaciones WebSocket - Bryan
│
├── web/                         Interfaz del estudiante
│
├── pruebas/
│   ├── test_api_rest.py
│   ├── test_coordinador.py
│   ├── test_notificaciones_cliente.py
│   └── test_rpc_cocina.py
│
├── docs/
│   ├── arquitectura/
│   │   ├── contratos-comunicacion.md
│   │   ├── api-rest.md
│   │   └── rpc-cocina.md
│   ├── adr/
│   ├── pruebas/
│   └── bitacora_ia.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

Las carpetas de los mecanismos pendientes se completarán conforme avance la implementación de los respectivos integrantes.

## 5. Tecnologías utilizadas

- Python 3.
- FastAPI para la API REST.
- Pydantic para la validación de datos.
- Uvicorn para ejecutar el servidor HTTP.
- XML-RPC mediante bibliotecas estándar de Python.
- Sockets TCP mediante la biblioteca estándar `socket` (previsto).
- WebSockets para las notificaciones en tiempo real (previsto).
- Pytest para las pruebas automatizadas.
- HTML, CSS y JavaScript para la interfaz web (previsto).
- Git y GitHub para el control de versiones.

## 6. Estado actual del desarrollo

**Última actualización: 15 de noviembre de 2026.**

### 6.1. Módulo REST — Mateo

**Estado: implementado y probado.**

Se desarrollaron las siguientes funcionalidades:

- API REST mediante FastAPI.
- Modelos y validaciones con Pydantic.
- Almacenamiento en memoria de pedidos y catálogo.
- Creación y consulta de pedidos.
- Control de idempotencia para evitar duplicados.
- Consulta de estadísticas.
- Validación de transiciones de estado.
- Coordinador de pedidos con procesamiento en segundo plano.
- Clientes preparados para comunicación TCP y XML-RPC.
- Cliente preparado para publicar notificaciones WebSocket.
- Pruebas automatizadas de REST y coordinación.

La API mantiene el estado oficial de los pedidos y coordina la comunicación con los servicios internos.

### 6.2. Módulo XML-RPC — Sebastián

**Estado: implementado y probado.**

Se desarrolló un servidor de cocina independiente utilizando XML-RPC.

Funcionalidades implementadas:

- Servidor XML-RPC que escucha solicitudes remotas.
- Método `preparar_pedido(pedido_id, productos)`.
- Validación de identificadores UUID.
- Validación de productos y cantidades.
- Simulación del proceso de preparación.
- Respuestas compatibles con el cliente REST de Mateo.
- Control de pedidos duplicados mediante idempotencia.
- Detección de solicitudes inconsistentes.
- Manejo de solicitudes concurrentes.
- Manejo de errores de preparación.
- Consulta del estado de preparación.
- Verificación de disponibilidad del servicio.
- Cliente RPC auxiliar para pruebas manuales.
- Pruebas automatizadas de funcionamiento e integración.

El servidor utiliza almacenamiento en memoria para mantener el registro de los pedidos procesados.

Se implementaron controles de concurrencia mediante `threading.Lock` y `threading.Event`, evitando que solicitudes simultáneas con el mismo identificador generen preparaciones duplicadas.

**Configuración:**

- Protocolo: XML-RPC sobre HTTP.
- Dirección: `127.0.0.1`.
- Puerto: `9002`.
- Tiempo de preparación simulado por defecto: 2 segundos.

La comunicación RPC fue comprobada utilizando el cliente real del módulo REST.

### 6.3. Módulo TCP — Josué

**Estado: pendiente de implementación e integración real.**

Su responsabilidad será:

- Crear un servidor TCP independiente.
- Recibir los datos de pedidos enviados por la API.
- Validar los importes.
- Registrar ventas simuladas.
- Generar comprobantes.
- Devolver confirmaciones.
- Manejar desconexiones y tiempos de espera.

### 6.4. Módulo WebSockets — Bryan

**Estado: pendiente de implementación e integración real.**

Su responsabilidad será:

- Gestionar conexiones WebSocket.
- Notificar cambios de estado de los pedidos.
- Informar cuando un pedido esté listo.
- Detectar desconexiones de clientes.
- Permitir la reconexión.
- Implementar la interfaz web del estudiante.

La API ya dispone de un cliente preparado para enviar notificaciones, pero falta comprobar su funcionamiento con el servidor WebSocket real.

## 7. Instalación y configuración

### 7.1. Requisitos previos

Se necesita:

- Python 3.
- Visual Studio Code u otro editor.
- Git.
- Acceso al repositorio del proyecto.

### 7.2. Crear un entorno virtual

Desde la carpeta principal del proyecto, ejecutar en PowerShell:

```powershell
python -m venv .venv
```

### 7.3. Instalar dependencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Todas las dependencias externas necesarias se encuentran declaradas en `requirements.txt`.

Las bibliotecas `xmlrpc`, `socket` y `threading` forman parte de la biblioteca estándar de Python.

## 8. Ejecución del módulo REST

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

La API estará disponible en:

http://127.0.0.1:8000

La documentación interactiva de FastAPI se encuentra en:

http://127.0.0.1:8000/docs

Desde esta interfaz es posible consultar y probar los endpoints REST disponibles.

## 9. Ejecución del módulo XML-RPC

Para ejecutar el servidor de cocina, abrir una terminal independiente:

```powershell
.\.venv\Scripts\python.exe -m cocina.servidor_rpc --puerto 9002 --segundos 2
```

El servidor escuchará en:

`http://127.0.0.1:9002`

### Prueba manual de preparación

Con el servidor en ejecución, abrir otra terminal:

```powershell
.\.venv\Scripts\python.exe -m cocina.cliente_prueba --id 550e8400-e29b-41d4-a716-446655440000
```

Si la solicitud es válida, el servidor devuelve una respuesta que incluye:

```json
{
  "ok": true,
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "LISTO",
  "mensaje": "Pedido preparado correctamente",
  "duplicado": false
}
```

Al enviar nuevamente el mismo pedido con los mismos productos, el servidor reconoce el identificador y devuelve `duplicado: true`.

Esto permite demostrar que no se realiza nuevamente la preparación durante la misma ejecución del servidor.

## 10. Pruebas automatizadas

El proyecto utiliza Pytest para verificar el funcionamiento de sus componentes.

### Ejecutar las pruebas RPC

```powershell
.\.venv\Scripts\python.exe -m pytest pruebas/test_rpc_cocina.py -v
```

**Resultado registrado: 17 pruebas aprobadas.**

Las pruebas incluyen:

- Preparación exitosa.
- Idempotencia secuencial.
- Validación de productos.
- Validación de UUID.
- Detección de pedidos inconsistentes.
- Concurrencia.
- Errores controlados.
- Consulta de estados.
- Comunicación RPC mediante red local.
- Integración con el cliente RPC de Mateo.
- Integración con el coordinador REST.
- Comportamiento ante servicio no disponible.

### Ejecutar todas las pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Último resultado registrado:**

```text
46 passed, 1 warning
```

La advertencia corresponde a una deprecación relacionada con Starlette y su cliente de pruebas; no produjo fallos en las pruebas.

Las pruebas automatizadas incluyen componentes simulados para evaluar algunas interacciones. Por tanto, estos resultados no demuestran todavía una integración completa con los cuatro servidores reales.

## 11. Manejo de fallos y confiabilidad

El sistema contempla escenarios relacionados con la confiabilidad y la disponibilidad.

Entre los mecanismos ya desarrollados se incluyen:

- Control de pedidos duplicados en REST.
- Idempotencia en el servidor RPC de cocina.
- Validación de solicitudes inválidas.
- Detección de inconsistencias entre solicitudes.
- Manejo de excepciones.
- Control de concurrencia.
- Tiempos de espera en llamadas remotas.
- Conservación de estados de pedidos en la API.

Una limitación conocida es que el almacenamiento en memoria no conserva la información después de reiniciar los procesos.

Las pruebas definitivas de desconexión de clientes WebSocket y fallos del servidor TCP se realizarán durante la integración final.

## 12. Documentación

La documentación del proyecto se organiza en la carpeta `docs/`.

Incluye:

- Diagramas y contratos de arquitectura.
- Documentación del módulo REST.
- Documentación del módulo XML-RPC.
- Registros de decisiones arquitectónicas (ADR).
- Resultados y evidencias de pruebas.
- Bitácora de uso de inteligencia artificial.

La bitácora `docs/bitacora_ia.md` registra las intervenciones de herramientas de IA utilizadas durante el desarrollo, incluyendo las relacionadas con REST y RPC.

## 13. Trabajo pendiente

Para completar la práctica todavía se requiere:

1. Implementar el servidor TCP de caja y facturación.
2. Implementar el servidor WebSocket y la interfaz web.
3. Integrar los cuatro mecanismos dentro del mismo flujo de pedido.
4. Ejecutar pruebas con los cuatro servicios reales.
5. Registrar las evidencias de los escenarios de fallos.
6. Revisar y completar los documentos ADR.
7. Validar la arquitectura final con los cuatro integrantes.
8. Preparar el video demostrativo y la defensa individual.

## 14. Estado general

El proyecto cuenta actualmente con una API REST funcional y un servidor XML-RPC de cocina implementado y probado.

Se ha comprobado la compatibilidad entre el cliente RPC de Mateo y el servidor desarrollado por Sebastián mediante pruebas automatizadas y comunicación real por red local.

**El desarrollo continúa en progreso.** El sistema distribuido completo quedará finalizado cuando se integren los módulos TCP y WebSockets y se verifique el recorrido de un pedido a través de los cuatro mecanismos.

---

**Asignatura:** Sistemas Distribuidos  
**Proyecto:** Cafetería Distribuida  
**Equipo:** Mateo, Sebastián, Josué y Bryan