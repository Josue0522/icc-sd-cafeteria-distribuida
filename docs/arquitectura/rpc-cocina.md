# Servicio de cocina mediante XML-RPC

**Responsable:** Sebastián Alvarado  
**Mecanismo de comunicación:** RPC (Remote Procedure Call)  
**Tecnología:** Python y biblioteca estándar `xmlrpc`  
**Estado:** Implementado y probado. Integración completa del sistema pendiente.

## 1. Descripción general

El servicio de cocina es un componente independiente del sistema distribuido de gestión de pedidos de la cafetería universitaria.

Su responsabilidad es recibir solicitudes de preparación enviadas por la API REST, validar los datos de los pedidos, simular su preparación y devolver los resultados mediante XML-RPC.

Este mecanismo permite que la API principal ejecute operaciones en otro proceso sin acceder directamente a su implementación interna.

El servicio fue desarrollado considerando el contrato establecido por el módulo REST de Mateo.

## 2. Arquitectura y comunicación

La comunicación se realiza entre dos componentes:

- **Cliente RPC:** implementado en `api/servicios.py`, dentro del módulo REST de Mateo.
- **Servidor RPC:** implementado en `cocina/servidor_rpc.py`, dentro del módulo de cocina de Sebastián.

La API invoca remotamente la operación `preparar_pedido(pedido_id, productos)`.

El servidor procesa la solicitud y devuelve un resultado indicando si el pedido fue preparado correctamente.

**Configuración de comunicación:**

- Protocolo: XML-RPC sobre HTTP.
- Dirección local: `127.0.0.1`.
- Puerto: `9002`.
- URL: `http://127.0.0.1:9002`.
- Tiempo máximo de espera configurado en el cliente REST: 15 segundos.
- Tiempo de preparación simulado por defecto: 2 segundos.

El servidor de cocina no modifica directamente los estados almacenados en la API. La API REST mantiene la responsabilidad sobre el estado oficial del pedido.

## 3. Métodos RPC implementados

### preparar_pedido(pedido_id, productos)

Recibe un identificador de pedido y una lista de productos.

Realiza las siguientes operaciones:

1. Valida el identificador UUID.
2. Comprueba que existan productos válidos.
3. Verifica si el pedido fue procesado anteriormente.
4. Registra el pedido en memoria si es nuevo.
5. Simula el tiempo de preparación.
6. Devuelve el resultado al cliente RPC.

**Ejemplo de solicitud:**

```python
preparar_pedido(
    "550e8400-e29b-41d4-a716-446655440000",
    [
        {
            "producto_id": "CAF-001",
            "nombre": "Café americano",
            "cantidad": 2
        }
    ]
)
```

**Ejemplo de respuesta exitosa:**

```json
{
  "ok": true,
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "LISTO",
  "mensaje": "Pedido preparado correctamente",
  "duplicado": false
}
```

### consultar_pedido(pedido_id)

Permite consultar el estado de un pedido registrado en el servidor de cocina.

Es útil para comprobar el resultado de una preparación cuando se pierde una respuesta RPC.

Actualmente, este método está implementado en cocina, pero el cliente REST de Mateo todavía no lo utiliza para recuperar operaciones.

### ping()

Permite comprobar si el servidor RPC está disponible.

Devuelve una respuesta indicando que el servicio de cocina se encuentra activo.

## 4. Idempotencia y concurrencia

El servidor implementa un mecanismo de idempotencia para evitar preparar el mismo pedido varias veces.

Si recibe nuevamente el mismo UUID con los mismos productos, reutiliza el resultado de la operación original.

Si el mismo identificador contiene productos diferentes, devuelve un error de inconsistencia.

Para controlar solicitudes simultáneas se utilizan:

- `threading.Lock`: protege el acceso a los registros compartidos.
- `threading.Event`: permite que las solicitudes duplicadas esperen el resultado de la preparación original.
- `ThreadingMixIn`: permite atender varias conexiones RPC concurrentes.

Los registros permanecen almacenados en memoria mientras el servidor se mantiene en ejecución.

## 5. Manejo de errores

El servicio contempla las siguientes situaciones:

| Situación | Comportamiento |
|---|---|
| UUID inválido | Rechaza la solicitud. |
| Productos inválidos | Devuelve un error controlado. |
| Pedido repetido | Reutiliza el resultado original. |
| Mismo UUID con distintos productos | Devuelve un error de inconsistencia. |
| Fallo durante la preparación | Devuelve `ERROR_COCINA`. |
| Servidor no disponible | El cliente RPC detecta un error de conexión. |
| Tiempo de espera superado | La API conserva el estado de preparación hasta determinar el resultado. |

Para simular un error de cocina se utiliza el argumento `--simular-error`.

## 6. Ejecución del servidor

Desde la raíz del repositorio, abrir una terminal de PowerShell y ejecutar:

```powershell
.\.venv\Scripts\python.exe -m cocina.servidor_rpc --puerto 9002 --segundos 2
```

El servidor queda disponible en:

`http://127.0.0.1:9002`

Para simular un fallo controlado:

```powershell
.\.venv\Scripts\python.exe -m cocina.servidor_rpc --puerto 9002 --segundos 2 --simular-error
```

## 7. Pruebas manuales

Con el servidor en ejecución, abrir una segunda terminal y enviar un pedido:

```powershell
.\.venv\Scripts\python.exe -m cocina.cliente_prueba --id 550e8400-e29b-41d4-a716-446655440000
```

Si el pedido es válido, el servidor devuelve el estado `LISTO`.

Al repetir el mismo identificador y los mismos productos, la respuesta incluye `duplicado: true`, demostrando que no se realiza una segunda preparación.

## 8. Pruebas automatizadas

Las pruebas específicas del mecanismo RPC están implementadas en:

`pruebas/test_rpc_cocina.py`

Para ejecutarlas:

```powershell
.\.venv\Scripts\python.exe -m pytest pruebas/test_rpc_cocina.py -v
```

**Resultado obtenido:** 17 pruebas aprobadas.

Se verificaron, entre otros casos:

- Preparación exitosa.
- Idempotencia secuencial.
- Validación de pedidos y productos.
- Detección de inconsistencias.
- Solicitudes concurrentes.
- Errores controlados.
- Consulta del estado de cocina.
- Comunicación RPC por red local.
- Compatibilidad con el cliente REST de Mateo.
- Integración con el coordinador de pedidos.
- Servicio RPC no disponible.

También se ejecutó la suite completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Resultado obtenido:** 46 pruebas aprobadas, sin fallos.

Durante la ejecución se presentó una advertencia de deprecación relacionada con Starlette y su cliente de pruebas. Esta advertencia no impidió la ejecución correcta de las pruebas.

## 9. Limitaciones conocidas

- Los pedidos se almacenan únicamente en memoria y se pierden cuando se reinicia el servidor.
- La preparación es simulada mediante `time.sleep`.
- No se implementa una cocina física ni equipamiento real.
- El servicio utiliza comunicación local para las pruebas.
- El método `consultar_pedido` todavía no está integrado en la recuperación de estados del cliente REST.
- La ejecución exitosa de las pruebas RPC no demuestra que los cuatro mecanismos del sistema completo estén integrados.
- La integración real con Sockets TCP y WebSockets debe comprobarse cuando los módulos correspondientes estén disponibles.

## 10. Conclusión del módulo

Se implementó un servidor XML-RPC independiente y compatible con el contrato de comunicación establecido por el módulo REST.

Las pruebas realizadas comprobaron la preparación simulada de pedidos, la validación de solicitudes, el control de duplicados, la concurrencia y el manejo de errores.

El módulo RPC se encuentra preparado para su incorporación al proyecto compartido, sujeto a revisión del equipo y a las pruebas finales de integración.

**Uso de inteligencia artificial:** sugerencias de código, guía para ejecutar las pruebas correspondientes y la documentación se desarrollaron con asistencia de ChatGPT. Su utilización se registra en el archivo `docs/bitacora_ia.md`.