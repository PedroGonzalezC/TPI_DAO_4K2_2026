"""Patrón Factory (fábrica simple): FabricaPrestamos.

Encapsula la elección entre PrestamoLocal y PrestamoInterbibliotecario para que
el caso de uso solicite un préstamo sin instanciar clases concretas.
"""

from .prestamo import Prestamo, PrestamoInterbibliotecario, PrestamoLocal


class FabricaPrestamos:
    """Factory: instancia el tipo de préstamo según las sedes de origen y destino."""

    @staticmethod
    def crear(
        socio_id: int,
        ejemplar_id: int,
        origen: int,
        destino: int,
        *,
        solicitado_en: str | None = None,
    ) -> Prestamo:
        clase = PrestamoLocal if origen == destino else PrestamoInterbibliotecario
        return clase(
            socio_id=socio_id,
            ejemplar_id=ejemplar_id,
            sede_origen_id=origen,
            sede_destino_id=destino,
            solicitado_en=solicitado_en,
        )

    @staticmethod
    def reconstruir(
        *,
        id: int,
        socio_id: int,
        ejemplar_id: int,
        sede_origen_id: int,
        sede_destino_id: int,
        tipo: str,
        estado: str,
        solicitado_en: str,
        entregado_en: str | None = None,
        vence_en: str | None = None,
        devuelto_en: str | None = None,
        condicion_devolucion: str | None = None,
        multa_centavos: int = 0,
    ) -> Prestamo:
        clase = PrestamoLocal if tipo == "LOCAL" else PrestamoInterbibliotecario
        return clase(
            id=id,
            socio_id=socio_id,
            ejemplar_id=ejemplar_id,
            sede_origen_id=sede_origen_id,
            sede_destino_id=sede_destino_id,
            estado=estado,
            solicitado_en=solicitado_en,
            entregado_en=entregado_en,
            vence_en=vence_en,
            devuelto_en=devuelto_en,
            condicion_devolucion=condicion_devolucion,
            multa_centavos=multa_centavos,
        )
