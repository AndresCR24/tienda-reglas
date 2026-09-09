"""Punto unico de registro y resolucion de reglas de precio."""
from .regla_precio import ReglaPrecio
from .regla_precio_normal import ReglaPrecioNormal
from .regla_precio_por_peso import ReglaPrecioPorPeso
from .regla_precio_especial import ReglaPrecioEspecial


class ReglaPrecioPorDefecto(ReglaPrecio):
    """Respaldo para SKUs sin prefijo conocido: se cobra precio x cantidad.

    Evita que un SKU nuevo rompa la aplicacion mientras se define su regla.
    """

    nombre = "Sin regla especifica (precio unitario x cantidad)"

    def es_aplicable(self, sku: str) -> bool:
        return True

    def calcular_total(self, cantidad: int, precio: float) -> float:
        return cantidad * precio


class ManejadorReglas:
    """Singleton que conoce todas las reglas y resuelve cual aplica a un SKU.

    Es el unico lugar que se toca al agregar o cambiar una regla; el resto del
    dominio (Item, Carrito, Tienda) solo conoce la interfaz ReglaPrecio.
    """

    _instancia: "ManejadorReglas | None" = None

    def __init__(self) -> None:
        # Constructor privado por convencion: se debe usar obtener_instancia().
        if ManejadorReglas._instancia is not None:
            raise RuntimeError(
                "ManejadorReglas es un singleton: use ManejadorReglas.obtener_instancia()"
            )
        self._reglas: list[ReglaPrecio] = [
            ReglaPrecioNormal(),
            ReglaPrecioPorPeso(),
            ReglaPrecioEspecial(),
        ]
        self._regla_por_defecto: ReglaPrecio = ReglaPrecioPorDefecto()

    @classmethod
    def obtener_instancia(cls) -> "ManejadorReglas":
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def obtener_regla(self, sku: str) -> ReglaPrecio:
        """Devuelve la primera regla aplicable al SKU."""
        for regla in self._reglas:
            if regla.es_aplicable(sku):
                return regla
        return self._regla_por_defecto

    def registrar_regla(self, regla: ReglaPrecio) -> None:
        """Agrega una regla nueva sin modificar las existentes (OCP).

        Se inserta al inicio para que pueda especializar un prefijo ya cubierto.
        """
        self._reglas.insert(0, regla)

    def reglas(self) -> list[ReglaPrecio]:
        return list(self._reglas)
