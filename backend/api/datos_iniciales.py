"""Catalogo de ejemplo con los tres tipos de producto del caso de estudio."""
from ..dominio.producto import Producto
from ..dominio.tienda import Tienda

CATALOGO = [
    # SKU, nombre, descripcion, unidades, precio unitario
    ("EA-1001", "Camiseta basica", "Camiseta de algodon, talla M", 25, 45_000),
    ("EA-1002", "Termo 500 ml", "Termo de acero inoxidable", 12, 89_900),
    ("EA-1003", "Cuaderno argollado", "Cuaderno de 100 hojas cuadriculadas", 40, 12_500),
    ("WE-2001", "Cafe molido", "Precio por gramo; la cantidad se indica en kilogramos", 30, 38),
    ("WE-2002", "Arroz blanco", "Precio por gramo; la cantidad se indica en kilogramos", 50, 4),
    ("WE-2003", "Queso campesino", "Precio por gramo; la cantidad se indica en kilogramos", 15, 22),
    ("SP-3001", "Jabon en barra", "20% de descuento por cada 3 unidades (max. 50%)", 60, 6_800),
    ("SP-3002", "Bombillo LED", "20% de descuento por cada 3 unidades (max. 50%)", 36, 15_900),
    ("SP-3003", "Par de medias", "20% de descuento por cada 3 unidades (max. 50%)", 48, 9_500),
]


def construir_tienda() -> Tienda:
    tienda = Tienda("Tienda del caso de estudio")
    for sku, nombre, descripcion, unidades, precio in CATALOGO:
        tienda.agregar_producto(Producto(sku, nombre, descripcion, unidades, precio))
    tienda.obtener_o_crear_usuario("demo")
    return tienda
