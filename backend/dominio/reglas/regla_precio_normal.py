"""Regla por defecto: productos normales (SKU que empieza por EA)."""
from .regla_precio import ReglaPrecio

PREFIJO = "EA"


class ReglaPrecioNormal(ReglaPrecio):
    """Se cobra el precio unitario por la cantidad."""

    nombre = "Producto normal (precio unitario x cantidad)"

    def es_aplicable(self, sku: str) -> bool:
        return sku.upper().startswith(PREFIJO)

    def calcular_total(self, cantidad: int, precio: float) -> float:
        return cantidad * precio
