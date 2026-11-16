
const API_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:9003";

// 1. Precios de los productos
const PRECIO_CAFE = 1.50;
const PRECIO_SANDWICH = 2.75;

// 2. Elementos de la interfaz
const cantidadCafe = document.getElementById("cantidadCafe");
const cantidadSandwich = document.getElementById("cantidadSandwich");
const totalPedido = document.getElementById("totalPedido");
const btnRealizarPedido = document.getElementById("btnRealizarPedido");

const estudianteId = document.getElementById("estudianteId");
const observaciones = document.getElementById("observaciones");
const pedidoId = document.getElementById("pedidoId");
const estadoPedido = document.getElementById("estadoPedido");
const conexion = document.getElementById("conexion");
const mensajeNotificacion = document.getElementById("mensajeNotificacion");

let socket = null;
let enviando = false;


// 3. Calcular el total del pedido
function calcularTotal() {
    const cafe = Number(cantidadCafe.value);
    const sandwich = Number(cantidadSandwich.value);

    const cantidadesValidas =
        Number.isInteger(cafe) &&
        Number.isInteger(sandwich) &&
        cafe >= 0 && cafe <= 20 &&
        sandwich >= 0 && sandwich <= 20;

    const total = cantidadesValidas
        ? cafe * PRECIO_CAFE + sandwich * PRECIO_SANDWICH
        : 0;

    totalPedido.textContent = `$${total.toFixed(2)}`;

    btnRealizarPedido.disabled =
        enviando || !cantidadesValidas || (cafe + sandwich === 0);
}


// 4. Conectar WebSocket al pedido registrado
function conectarWebSocket(id) {

    if (socket !== null) {
        socket.close();
    }

    const nuevaConexion = new WebSocket(
        `${WS_URL}/ws/pedidos/${id}`
    );

    socket = nuevaConexion;
    conexion.textContent = "Conectando WebSocket...";

    nuevaConexion.onopen = function() {
        if (socket !== nuevaConexion) return;

        conexion.textContent = "WebSocket conectado";
    };

    nuevaConexion.onmessage = function(event) {
        if (socket !== nuevaConexion) return;

        try {
            const datos = JSON.parse(event.data);

            if (datos.pedido_id !== id) {
                return;
            }

            estadoPedido.textContent = datos.estado;
            mensajeNotificacion.textContent = datos.mensaje;

        } catch (error) {
            console.error("Error al leer la notificación:", error);
        }
    };

    nuevaConexion.onclose = function() {
        if (socket !== nuevaConexion) return;

        conexion.textContent = "WebSocket desconectado";
    };

    nuevaConexion.onerror = function() {
        if (socket !== nuevaConexion) return;

        conexion.textContent = "Error de conexión WebSocket";
    };
}


// 5. Crear el pedido utilizando REST
async function realizarPedido() {

    if (enviando || btnRealizarPedido.disabled) {
        return;
    }

    const estudiante = estudianteId.value.trim();
    const cafe = Number(cantidadCafe.value);
    const sandwich = Number(cantidadSandwich.value);

    if (!estudiante || estudiante.length > 50) {
        alert("Ingresa un identificador de estudiante válido.");
        return;
    }

    if (observaciones.value.length > 300) {
        alert("Las observaciones no pueden superar 300 caracteres.");
        return;
    }

    const items = [];

    if (cafe > 0) {
        items.push({
            producto_id: "CAF-001",
            cantidad: cafe
        });
    }

    if (sandwich > 0) {
        items.push({
            producto_id: "SAN-001",
            cantidad: sandwich
        });
    }

    const datosPedido = {
        estudiante_id: estudiante,
        items: items,
        observaciones: observaciones.value.trim()
    };

    // Clave única para evitar duplicados por reenvío accidental
    const claveIdempotencia = crypto.randomUUID();

    enviando = true;
    calcularTotal();

    btnRealizarPedido.textContent = "Registrando pedido...";
    mensajeNotificacion.textContent = "Enviando pedido a REST...";

    try {
        const respuesta = await fetch(`${API_URL}/pedidos`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Idempotency-Key": claveIdempotencia
            },
            body: JSON.stringify(datosPedido)
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            const mensajeError =
                datos.error?.mensaje || "No se pudo crear el pedido.";

            throw new Error(mensajeError);
        }

        // Mostrar el pedido registrado
        pedidoId.textContent = datos.pedido_id;
        estadoPedido.textContent = datos.estado;
        mensajeNotificacion.textContent =
            "Pedido registrado. Esperando actualizaciones...";

        // Conectar automáticamente las notificaciones
        conectarWebSocket(datos.pedido_id);

        console.log("Pedido creado:", datos);

    } catch (error) {
        console.error("Error al crear el pedido:", error);

        mensajeNotificacion.textContent =
            "No se pudo confirmar el registro: " + error.message;

        // Si se pierde la respuesta de REST, no debemos
        // asumir que el pedido no fue creado.
    } finally {
        enviando = false;
        btnRealizarPedido.textContent = "Realizar pedido";
        calcularTotal();
    }
}


// 6. Eventos de la interfaz
cantidadCafe.addEventListener("input", calcularTotal);
cantidadSandwich.addEventListener("input", calcularTotal);

btnRealizarPedido.addEventListener("click", realizarPedido);

// Calcular el total inicial
calcularTotal();
