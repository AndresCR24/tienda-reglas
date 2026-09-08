# Tienda — implementación del caso de estudio

Aplicación web (backend + frontend) que implementa el caso de estudio de la tienda
discutido en el OVA de principios de diseño de software, siguiendo el modelo de
diseño orientado a objetos definido en [`modelo.md`](modelo.md).

- **Backend:** Python 3.10+ con FastAPI. Contiene el modelo de dominio OO completo.
- **Frontend:** HTML + CSS + JavaScript sin framework ni paso de compilación.
- **Pruebas:** 37 pruebas con pytest (reglas de precio, dominio y API).

## Cómo ejecutar

La forma más corta (crea el entorno si hace falta, levanta el servidor y abre el
navegador):

```bash
./iniciar.sh
```

O paso a paso:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

`uvicorn` **no abre el navegador**: deja la terminal mostrando los logs del servidor
(eso es lo normal) y hay que abrir <http://127.0.0.1:8000> a mano. `Ctrl+C` lo detiene.
La documentación interactiva de la API queda en <http://127.0.0.1:8000/docs>.

Para ejecutar las pruebas:

```bash
pytest
```

## Estructura

```
backend/
  dominio/                      # Modelo de dominio: sin dependencias de HTTP ni de FastAPI
    producto.py                 # Producto
    item.py                     # Item
    carrito.py                  # Carrito
    usuario.py                  # Usuario
    tienda.py                   # Tienda (fachada del dominio)
    reglas/
      regla_precio.py           # ReglaPrecio (interfaz / ABC)
      regla_precio_normal.py    # SKU EA
      regla_precio_por_peso.py  # SKU WE
      regla_precio_especial.py  # SKU SP
      manejador_reglas.py       # ManejadorReglas (singleton) + regla por defecto
  api/
    main.py                     # Endpoints REST; traduce HTTP <-> dominio
    datos_iniciales.py          # Catálogo de ejemplo
frontend/
  index.html, styles.css, app.js
tests/
  test_reglas.py, test_dominio.py, test_api.py
```

## Reglas de precio

| Prefijo del SKU | Tipo | Cálculo |
|---|---|---|
| `EA` | Normal | `precio_unitario × cantidad` |
| `WE` | Peso | El precio unitario está dado **por gramo** y la cantidad en **kilogramos**: `precio × 1000 × kg` |
| `SP` | Descuento especial | 20 % de descuento por cada 3 unidades completas, con un tope de 50 % |
| otro | Por defecto | `precio_unitario × cantidad` (respaldo para SKUs sin regla definida) |

## Decisiones de implementación

**El diagrama se implementó tal cual.** Cada clase del modelo (`Tienda`, `Usuario`,
`Carrito`, `Item`, `Producto`, `ManejadorReglas`, `ReglaPrecio` y sus tres
implementaciones) existe como una clase Python con los mismos nombres, atributos y
métodos del diagrama. Las relaciones también se conservan: `Carrito` compone sus
`Item`, cada `Item` referencia un `Producto` y una `ReglaPrecio`, y obtiene esa regla
pidiéndosela al `ManejadorReglas`.

**El punto de extensión exigido por el enunciado.** El requisito de que las reglas de
precio puedan cambiar o agregarse «de forma desacoplada» se resuelve con el patrón
Strategy más un registro central:

- `Item.calcular_total()` delega en `self._regla_precio` y **no tiene ningún `if` sobre
  el tipo de SKU**. El dominio depende de la abstracción `ReglaPrecio`, no de las
  implementaciones concretas.
- Cada regla decide por sí misma si aplica (`es_aplicable(sku)`), así que el
  conocimiento del prefijo vive dentro de la regla y no se dispersa por la aplicación.
- Agregar una regla nueva = crear una subclase de `ReglaPrecio` y registrarla con
  `ManejadorReglas.registrar_regla(...)`. Ninguna clase existente se modifica.
  `tests/test_reglas.py::test_se_puede_agregar_una_regla_nueva_sin_tocar_las_existentes`
  demuestra esto agregando una regla «3x2» en tiempo de ejecución.

**El backend es la única fuente de verdad de los precios.** El frontend nunca calcula
un total: envía la operación y muestra el valor que devuelve el dominio. Así, cambiar
una regla no obliga a tocar el frontend.

**Validación de disponibilidad en dos momentos.** Al agregar al carrito se verifica
contra las unidades disponibles *teniendo en cuenta lo que el usuario ya tiene
reservado* de ese producto. Al finalizar la compra se vuelve a validar **todo el
carrito antes de modificar nada**, para no dejar una compra aplicada a medias si un
producto se quedó sin existencias entretanto.

**Adiciones mínimas sobre el diagrama**, todas justificadas por la implementación web:

| Adición | Motivo |
|---|---|
| `Carrito.buscar_item(sku)`, `vaciar()`, `esta_vacio()` | Consultas que el diagrama daba por supuestas; necesarias para HTTP (`DELETE /carrito/items/{sku}` identifica el item por SKU, no por referencia de objeto). |
| `Item.cambiar_cantidad()` | Agregar dos veces el mismo producto acumula la cantidad en un solo item, que es el comportamiento esperado de un carrito. |
| `ManejadorReglas.registrar_regla()` | Hace explícito y utilizable el punto de extensión. |
| `ReglaPrecioPorDefecto` | Evita que un SKU con prefijo desconocido rompa la aplicación. |
| Excepciones propias del dominio | El dominio reporta errores en sus propios términos y la capa API los traduce a códigos HTTP (404, 409, 400). |
| `Tienda.obtener_o_crear_usuario()` | La web necesita materializar un usuario a partir de la cabecera `X-Usuario`. |

**La cantidad se mantiene como entero, incluso para los productos de peso.** El
diagrama define `Item.cantidad: int` y `Producto.unidades_disponibles: int`, y la
implementación respeta ese tipo: para un producto `WE` la cantidad son kilogramos
enteros. Es una decisión consciente, no un descuido.

Se consideró permitir decimales (comprar 1.2 kg de café), pero se descartó por dos
razones. La primera es de fidelidad: el propósito de la actividad es evaluar si el
modelo de diseño dado alcanza para implementar la aplicación, y cambiar el tipo de un
atributo del diagrama sería evaluar otro modelo. La segunda es que el enunciado pide
explícitamente no hacer suposiciones sobre funcionalidades adicionales que aplicarían
a un producto de software real; la venta fraccionada es precisamente una de esas
suposiciones.

Vale aclarar por qué la cantidad va en kilogramos y no en gramos, que sería la otra
forma de representar 1.2 kg sin decimales (1200 g). Si la cantidad viniera en gramos,
el cálculo sería `gramos × precio_por_gramo`, es decir, idéntico al de la regla
normal, y `ReglaPrecioPorPeso` no tendría razón de existir. La regla existe justamente
porque hay una conversión de gramos a kilogramos, así que la cantidad se expresa en
kilogramos y la regla multiplica por 1000.

Si más adelante se quisiera vender peso fraccionado, el propio diseño indica dónde
tocarlo: la granularidad válida de una cantidad depende del tipo de producto, así que
sería una responsabilidad más de `ReglaPrecio` (por ejemplo, un método
`validar_cantidad`), no un `if` repartido por `Item` o `Tienda`.

**Estado en memoria.** No hay base de datos: la `Tienda` vive en el proceso del
servidor, según el enunciado, que pide no suponer requisitos adicionales. El endpoint
`POST /api/reiniciar` restablece el catálogo para poder repetir la demostración.

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/productos` | Catálogo con existencias y la regla que aplica a cada producto |
| `GET` | `/api/reglas` | Reglas de precio registradas |
| `GET` | `/api/tienda` | Nombre de la tienda y total acumulado de ventas |
| `GET` | `/api/carrito` | Items del carrito con su total y el total de la compra |
| `POST` | `/api/carrito/items` | Agrega un producto (`{"sku", "cantidad"}`); devuelve el total del item y el del carrito |
| `DELETE` | `/api/carrito/items/{sku}` | Elimina un item del carrito |
| `POST` | `/api/compra` | Finaliza la compra: acumula la venta y descuenta existencias |
| `POST` | `/api/reiniciar` | Restablece el estado de la tienda |

La cabecera opcional `X-Usuario` selecciona el carrito (por defecto `demo`), lo que
permite demostrar que cada `Usuario` tiene su propio `Carrito`.
