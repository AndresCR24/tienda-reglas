"""Usuario de la tienda; cada uno tiene su propio carrito."""
from .carrito import Carrito
from .item import Item
from .producto import Producto


class Usuario:
    def __init__(self, identificador: str, nombre: str = "") -> None:
        self._identificador = identificador
        self._nombre = nombre or identificador
        self._carrito = Carrito()

    @property
    def identificador(self) -> str:
        return self._identificador

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def carrito(self) -> Carrito:
        return self._carrito

    def agregar_item_a_carrito(self, producto: Producto, cantidad: int) -> Item:
        return self._carrito.agregar_item(producto, cantidad)

    def borrar_item_de_carrito(self, item: Item) -> None:
        self._carrito.borrar_item(item)
