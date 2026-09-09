"""Regla de descuento especial (SKU que empieza por SP)."""
from .regla_precio import ReglaPrecio

PREFIJO = "SP"
UNIDADES_POR_TRAMO = 3
DESCUENTO_POR_TRAMO = 0.20
DESCUENTO_MAXIMO = 0.50


class ReglaPrecioEspecial(ReglaPrecio):
    """20% de descuento por cada 3 unidades, con un tope del 50%."""

    nombre = "Descuento especial (20% por cada 3 unidades, maximo 50%)"

    def es_aplicable(self, sku: str) -> bool:
        return sku.upper().startswith(PREFIJO)

    def calcular_total(self, cantidad: int, precio: float) -> float:
        tramos = cantidad // UNIDADES_POR_TRAMO
        descuento = min(tramos * DESCUENTO_POR_TRAMO, DESCUENTO_MAXIMO)
        return cantidad * precio * (1 - descuento)
