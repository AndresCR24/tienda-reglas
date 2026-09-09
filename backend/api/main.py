"""API REST sobre el modelo de dominio. Solo traduce HTTP <-> Tienda."""
from pathlib import Path

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..dominio.item import CantidadInvalidaError, Item
from ..dominio.carrito import Carrito
from ..dominio.producto import Producto, ProductoSinUnidadesError
from ..dominio.reglas.manejador_reglas import ManejadorReglas
from ..dominio.tienda import (
    CarritoVacioError,
    ProductoNoEncontradoError,
    Tienda,
)
from ..dominio.usuario import Usuario
from .datos_iniciales import construir_tienda

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="Tienda - caso de estudio",
    description="Implementacion del modelo de diseno OO del OVA de principios de diseno.",
    version="1.0.0",
)

# Estado en memoria: una sola Tienda viva mientras corre el proceso.
tienda: Tienda = construir_tienda()


def obtener_tienda() -> Tienda:
    return tienda


def obtener_usuario(
    x_usuario: str = Header(default="demo", alias="X-Usuario"),
    t: Tienda = Depends(obtener_tienda),
) -> Usuario:
    """Identifica al usuario por cabecera; permite varios carritos simultaneos."""
    return t.obtener_o_crear_usuario(x_usuario)


# --- Esquemas de entrada/salida (frontera HTTP, no son el dominio) ---------
class AgregarItemRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    cantidad: int = Field(..., gt=0)


def _producto_a_dict(producto: Producto) -> dict:
    regla = ManejadorReglas.obtener_instancia().obtener_regla(producto.sku)
    return {
        "sku": producto.sku,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "unidades_disponibles": producto.unidades_disponibles,
        "precio_unitario": producto.precio_unitario,
        "regla": regla.nombre,
        "tipo": type(regla).__name__,
    }


def _item_a_dict(item: Item) -> dict:
    return {
        "sku": item.producto.sku,
        "nombre": item.producto.nombre,
        "cantidad": item.cantidad,
        "precio_unitario": item.producto.precio_unitario,
        "regla": item.regla_precio.nombre,
        "tipo": type(item.regla_precio).__name__,
        "total": item.calcular_total(),
    }


def _carrito_a_dict(carrito: Carrito) -> dict:
    return {
        "items": [_item_a_dict(i) for i in carrito.items],
        "total": carrito.calcular_total(),
    }


# --- Endpoints ------------------------------------------------------------
@app.get("/api/productos")
def listar_productos(t: Tienda = Depends(obtener_tienda)):
    return [_producto_a_dict(p) for p in t.productos()]


@app.get("/api/reglas")
def listar_reglas():
    manejador = ManejadorReglas.obtener_instancia()
    return [{"clase": type(r).__name__, "nombre": r.nombre} for r in manejador.reglas()]


@app.get("/api/tienda")
def estado_tienda(t: Tienda = Depends(obtener_tienda)):
    return {"nombre": t.nombre, "total_ventas": t.total_ventas}


@app.get("/api/carrito")
def ver_carrito(usuario: Usuario = Depends(obtener_usuario)):
    return _carrito_a_dict(usuario.carrito)


@app.post("/api/carrito/items", status_code=201)
def agregar_item(
    datos: AgregarItemRequest = Body(...),
    t: Tienda = Depends(obtener_tienda),
    usuario: Usuario = Depends(obtener_usuario),
):
    try:
        producto = t.obtener_producto(datos.sku)
        item = t.agregar_producto_a_carrito(usuario, producto, datos.cantidad)
    except ProductoNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ProductoSinUnidadesError, CantidadInvalidaError) as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"item": _item_a_dict(item), "carrito": _carrito_a_dict(usuario.carrito)}


@app.delete("/api/carrito/items/{sku}")
def eliminar_item(
    sku: str,
    t: Tienda = Depends(obtener_tienda),
    usuario: Usuario = Depends(obtener_usuario),
):
    item = usuario.carrito.buscar_item(sku)
    if item is None:
        raise HTTPException(status_code=404, detail=f"El carrito no tiene el producto {sku}")
    t.eliminar_item_de_carrito(usuario, item)
    return {"carrito": _carrito_a_dict(usuario.carrito)}


@app.post("/api/compra")
def finalizar_compra(
    t: Tienda = Depends(obtener_tienda),
    usuario: Usuario = Depends(obtener_usuario),
):
    try:
        total = t.finalizar_compra(usuario)
    except CarritoVacioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProductoSinUnidadesError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "total_compra": total,
        "total_ventas_tienda": t.total_ventas,
        "carrito": _carrito_a_dict(usuario.carrito),
    }


@app.post("/api/reiniciar")
def reiniciar():
    """Restablece el catalogo y las ventas; util para demostrar la app."""
    global tienda
    tienda = construir_tienda()
    return {"mensaje": "Tienda reiniciada"}


# --- Frontend estatico ----------------------------------------------------
@app.middleware("http")
async def revalidar_estaticos(request, call_next):
    """Obliga al navegador a revalidar el frontend en cada carga.

    StaticFiles solo envia etag y last-modified. Sin Cache-Control el navegador
    aplica cache heuristica y puede seguir usando un archivo viejo despues de
    editarlo. Con no-cache sigue usando el etag, asi que la revalidacion cuesta
    un 304 y nunca se sirve una version obsoleta durante el desarrollo.
    """
    respuesta = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
