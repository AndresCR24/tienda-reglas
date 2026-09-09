"""Tienda: fachada del dominio, coordina productos, usuarios y ventas."""
from .item import Item
from .producto import Producto, ProductoSinUnidadesError
from .usuario import Usuario


class ProductoNoEncontradoError(Exception):
    """No existe un producto con ese SKU en la tienda."""


class UsuarioNoEncontradoError(Exception):
    """No existe un usuario con ese identificador."""


class CarritoVacioError(Exception):
    """No se puede finalizar una compra sin items."""


class Tienda:
    """Punto de entrada del dominio (Facade): la API solo habla con la Tienda."""

    def __init__(self, nombre: str = "Tienda") -> None:
        self._nombre = nombre
        self._total_ventas: float = 0.0
        self._productos: dict[str, Producto] = {}
        self._usuarios: dict[str, Usuario] = {}

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def total_ventas(self) -> float:
        return self._total_ventas

    # --- Productos -----------------------------------------------------
    def agregar_producto(self, producto: Producto) -> None:
        self._productos[producto.sku] = producto

    def productos(self) -> list[Producto]:
        return list(self._productos.values())

    def obtener_producto(self, sku: str) -> Producto:
        producto = self._productos.get(sku)
        if producto is None:
            raise ProductoNoEncontradoError(f"No existe el producto {sku}")
        return producto

    # --- Usuarios ------------------------------------------------------
    def registrar_usuario(self, usuario: Usuario) -> Usuario:
        self._usuarios[usuario.identificador] = usuario
        return usuario

    def obtener_usuario(self, identificador: str) -> Usuario:
        usuario = self._usuarios.get(identificador)
        if usuario is None:
            raise UsuarioNoEncontradoError(f"No existe el usuario {identificador}")
        return usuario

    def obtener_o_crear_usuario(self, identificador: str) -> Usuario:
        if identificador not in self._usuarios:
            self.registrar_usuario(Usuario(identificador))
        return self._usuarios[identificador]

    # --- Operaciones de compra ------------------------------------------
    def agregar_producto_a_carrito(self, usuario: Usuario, producto: Producto, cantidad: int) -> Item:
        """Verifica disponibilidad contra lo que el usuario ya tiene reservado."""
        en_carrito = usuario.carrito.buscar_item(producto.sku)
        ya_reservadas = en_carrito.cantidad if en_carrito is not None else 0
        if not producto.tiene_unidades(ya_reservadas + cantidad):
            detalle = f" y ya tiene {ya_reservadas} en el carrito" if ya_reservadas else ""
            raise ProductoSinUnidadesError(
                f"Solo hay {producto.unidades_disponibles} unidades de {producto.sku}{detalle}"
            )
        return usuario.agregar_item_a_carrito(producto, cantidad)

    def eliminar_item_de_carrito(self, usuario: Usuario, item: Item) -> None:
        usuario.borrar_item_de_carrito(item)

    def finalizar_compra(self, usuario: Usuario) -> float:
        """Acumula la venta, descuenta unidades y vacia el carrito."""
        carrito = usuario.carrito
        if carrito.esta_vacio():
            raise CarritoVacioError("El carrito esta vacio")

        # Se valida todo antes de modificar nada (evita compras a medias).
        for item in carrito.items:
            if not item.producto.tiene_unidades(item.cantidad):
                raise ProductoSinUnidadesError(
                    f"El producto {item.producto.sku} ya no tiene {item.cantidad} unidades disponibles"
                )

        total = carrito.calcular_total()
        for item in carrito.items:
            item.producto.descontar_unidades(item.cantidad)
        self._total_ventas += total
        carrito.vaciar()
        return total
