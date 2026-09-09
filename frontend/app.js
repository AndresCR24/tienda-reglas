/* Cliente de la API. El frontend no replica ninguna regla de precio:
   todos los totales que muestra vienen calculados por el dominio del backend. */

const $ = (sel) => document.querySelector(sel);

const dinero = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const ETIQUETAS = {
  ReglaPrecioNormal: { texto: "Normal", clase: "t-normal", tipo: "tipo-normal" },
  ReglaPrecioPorPeso: { texto: "Por peso", clase: "t-peso", tipo: "tipo-peso" },
  ReglaPrecioEspecial: { texto: "Especial", clase: "t-especial", tipo: "tipo-especial" },
};
const ETIQUETA_OTRA = { texto: "Otro", clase: "t-otro", tipo: "tipo-otro" };

const usuarioActual = () => $("#usuario").value.trim() || "demo";

async function api(ruta, opciones = {}) {
  const respuesta = await fetch(`/api${ruta}`, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      "X-Usuario": usuarioActual(),
      ...(opciones.headers || {}),
    },
  });
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const detalle = cuerpo.detail;
    throw new Error(
      typeof detalle === "string" ? detalle : "No se pudo completar la operación"
    );
  }
  return cuerpo;
}

let temporizadorAviso;
function avisar(mensaje, tipo = "") {
  const aviso = $("#aviso");
  aviso.textContent = mensaje;
  aviso.hidden = true; // reinicia la animación de entrada si ya estaba visible
  void aviso.offsetWidth;
  aviso.className = `aviso ${tipo}`;
  aviso.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => (aviso.hidden = true), 3500);
}

/** Anima un importe cuando cambia de valor. */
function actualizarImporte(elemento, valor) {
  const texto = dinero.format(valor);
  if (elemento.textContent === texto) return;
  elemento.textContent = texto;
  elemento.classList.remove("late");
  void elemento.offsetWidth;
  elemento.classList.add("late");
}

function etiquetaDe(tipo) {
  return ETIQUETAS[tipo] || ETIQUETA_OTRA;
}

function pintarProductos(productos) {
  const contenedor = $("#productos");
  contenedor.innerHTML = "";

  productos.forEach((p, indice) => {
    const etiqueta = etiquetaDe(p.tipo);
    const esPeso = p.tipo === "ReglaPrecioPorPeso";
    const agotado = p.unidades_disponibles === 0;

    const tarjeta = document.createElement("article");
    tarjeta.className = `tarjeta ${etiqueta.tipo}${agotado ? " sin-stock" : ""}`;
    tarjeta.dataset.sku = p.sku;
    tarjeta.style.setProperty("--i", indice);
    tarjeta.innerHTML = `
      <div class="tarjeta-figura${tieneFoto(p) ? " con-foto" : ""}">
        ${ilustracionDe(p)}
        <span class="etiqueta etiqueta-figura ${etiqueta.clase}"
              title="${p.regla}">${etiqueta.texto}</span>
        <div class="confirmacion" aria-hidden="true">
          <svg class="chulo" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="23"/>
            <path d="M15 26.5l7.5 7.5L37.5 19"/>
          </svg>
          <span class="confirmacion-texto">Agregado al carrito</span>
        </div>
      </div>
      <div class="tarjeta-cuerpo">
        <div class="sku">${p.sku}</div>
        <div class="nombre">${p.nombre}</div>
        <div class="descripcion">${p.descripcion}</div>
        <div class="tarjeta-pie">
          <div class="precio">
            ${dinero.format(p.precio_unitario)}
            <small>${esPeso ? "por gramo" : "por unidad"}</small>
          </div>
          <div class="existencias ${agotado ? "agotado" : ""}">
            ${agotado
              ? "Agotado"
              : `${p.unidades_disponibles}<br>${esPeso ? "kg disponibles" : "unidades"}`}
          </div>
        </div>
        <div class="fila-agregar">
          <input type="number" min="1" step="1" value="1"
                 max="${p.unidades_disponibles}"
                 aria-label="Cantidad de ${p.nombre}" ${agotado ? "disabled" : ""}>
          <button class="btn btn-plano" type="button" ${agotado ? "disabled" : ""}>
            Agregar
          </button>
        </div>
      </div>
    `;

    // Sin conexion la foto no llega: se cambia por la ilustracion SVG.
    const foto = tarjeta.querySelector(".foto");
    if (foto) {
      foto.addEventListener("error", () => {
        const figura = tarjeta.querySelector(".tarjeta-figura");
        figura.classList.remove("con-foto");
        figura.innerHTML = svgDe(p) + figura.querySelector(".etiqueta").outerHTML;
      }, { once: true });
    }

    const entrada = tarjeta.querySelector("input");
    const boton = tarjeta.querySelector(".fila-agregar button");
    boton.addEventListener("click", () => agregar(p.sku, entrada));
    entrada.addEventListener("keydown", (e) => {
      if (e.key === "Enter") agregar(p.sku, entrada);
    });

    contenedor.appendChild(tarjeta);
  });
}

/* Temporizador de respaldo por tarjeta, para no dejar estado en el DOM. */
const temporizadoresTarjeta = new WeakMap();

/** Muestra el chulo de confirmación sobre la tarjeta del producto agregado. */
function destacarTarjeta(sku) {
  const tarjeta = document.querySelector(`.tarjeta[data-sku="${sku}"]`);
  if (!tarjeta) return;

  clearTimeout(temporizadoresTarjeta.get(tarjeta));
  tarjeta.classList.remove("agregado");
  void tarjeta.offsetWidth; // reinicia la animación si se agrega dos veces seguidas
  tarjeta.classList.add("agregado");

  const limpiar = () => {
    clearTimeout(temporizadoresTarjeta.get(tarjeta));
    temporizadoresTarjeta.delete(tarjeta);
    tarjeta.removeEventListener("animationend", alTerminar);
    tarjeta.classList.remove("agregado");
  };
  function alTerminar(e) {
    // El trazo del chulo también burbujea hasta aquí; solo interesa el final.
    if (e.animationName === "mostrar-chulo") limpiar();
  }

  tarjeta.addEventListener("animationend", alTerminar);
  // Si el navegador no entrega animationend, la tarjeta no queda marcada.
  temporizadoresTarjeta.set(tarjeta, setTimeout(limpiar, 1500));
}

function pintarCarrito(carrito) {
  const contenedor = $("#items");
  contenedor.innerHTML = "";

  if (carrito.items.length === 0) {
    contenedor.innerHTML = `
      <p class="vacio">
        <span class="vacio-icono" aria-hidden="true">🛒</span>
        El carrito está vacío<br>Agrega productos para ver el total
      </p>`;
  } else {
    carrito.items.forEach((item, indice) => {
      const esPeso = item.tipo === "ReglaPrecioPorPeso";
      const unidad = esPeso ? "kg" : "u";
      const etiqueta = etiquetaDe(item.tipo);

      const fila = document.createElement("div");
      fila.className = "item";
      fila.style.setProperty("--i", indice);
      fila.innerHTML = `
        <div>
          <div class="nombre">${item.nombre}</div>
          <div class="item-detalle">
            ${item.cantidad} ${unidad} ·
            <span class="etiqueta ${etiqueta.clase}">${etiqueta.texto}</span>
          </div>
        </div>
        <div class="item-acciones">
          <span class="item-total">${dinero.format(item.total)}</span>
          <button class="btn-icono" type="button" title="Eliminar del carrito"
                  aria-label="Eliminar ${item.nombre}">&times;</button>
        </div>
      `;
      fila
        .querySelector("button")
        .addEventListener("click", () => eliminar(item.sku));
      contenedor.appendChild(fila);
    });
  }

  actualizarImporte($("#total-carrito"), carrito.total);
  $("#btn-comprar").disabled = carrito.items.length === 0;
}

async function refrescar() {
  const [productos, carrito, tienda] = await Promise.all([
    api("/productos"),
    api("/carrito"),
    api("/tienda"),
  ]);
  pintarProductos(productos);
  pintarCarrito(carrito);
  actualizarImporte($("#total-ventas"), tienda.total_ventas);
}

async function agregar(sku, entrada) {
  const cantidad = Number.parseInt(entrada.value, 10);
  if (!Number.isInteger(cantidad) || cantidad <= 0) {
    avisar("La cantidad debe ser un entero mayor que cero", "error");
    return;
  }
  try {
    const { item, carrito } = await api("/carrito/items", {
      method: "POST",
      body: JSON.stringify({ sku, cantidad }),
    });
    pintarCarrito(carrito);
    destacarTarjeta(sku);
    entrada.value = "1";
    avisar(
      `${item.nombre}: ${dinero.format(item.total)} · Total: ${dinero.format(carrito.total)}`,
      "exito"
    );
  } catch (error) {
    avisar(error.message, "error");
  }
}

async function eliminar(sku) {
  try {
    const { carrito } = await api(`/carrito/items/${sku}`, { method: "DELETE" });
    pintarCarrito(carrito);
    avisar("Producto eliminado del carrito");
  } catch (error) {
    avisar(error.message, "error");
  }
}

async function comprar() {
  try {
    const resultado = await api("/compra", { method: "POST" });
    await refrescar();
    avisar(`Compra realizada por ${dinero.format(resultado.total_compra)}`, "exito");
  } catch (error) {
    avisar(error.message, "error");
  }
}

async function reiniciar() {
  await api("/reiniciar", { method: "POST" });
  await refrescar();
  avisar("Tienda reiniciada");
}

$("#btn-comprar").addEventListener("click", comprar);
$("#btn-reiniciar").addEventListener("click", reiniciar);
$("#usuario").addEventListener("change", refrescar);

refrescar().catch((e) => avisar(e.message, "error"));
