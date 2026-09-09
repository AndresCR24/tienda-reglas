"""Producto de la tienda."""


class ProductoSinUnidadesError(Exception):
    """No hay unidades suficientes del producto."""


class Producto:
    def __init__(
        self,
        sku: str,
        nombre: str,
        descripcion: str,
        unidades_disponibles: int,
        precio_unitario: float,
    ) -> None:
        self._sku = sku
        self._nombre = nombre
        self._descripcion = descripcion
        self._unidades_disponibles = unidades_disponibles
        self._precio_unitario = precio_unitario

    @property
    def sku(self) -> str:
        return self._sku

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def unidades_disponibles(self) -> int:
        return self._unidades_disponibles

    @property
    def precio_unitario(self) -> float:
        return self._precio_unitario

    def tiene_unidades(self, cantidad: int) -> bool:
        return cantidad <= self._unidades_disponibles

    def descontar_unidades(self, cantidad: int) -> None:
        if not self.tiene_unidades(cantidad):
            raise ProductoSinUnidadesError(
                f"El producto {self._sku} solo tiene {self._unidades_disponibles} unidades disponibles"
            )
        self._unidades_disponibles -= cantidad
