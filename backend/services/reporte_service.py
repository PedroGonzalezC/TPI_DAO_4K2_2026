"""Servicio de negocio para reportes de circulación, catálogo y logística."""

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.prestamo_dao import PrestamoDAO
from ..daos.remito_dao import RemitoDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import ReglaNegocio, normalizar_fecha
from .prestamo_service import PrestamoService


class ReporteService:
    """Genera los seis reportes analíticos consultando los DAOs correspondientes."""

    NOMBRES_VALIDOS = (
        "activos_transito",
        "vencidos_multas",
        "mas_solicitados",
        "disponibilidad",
        "logistica",
        "movimientos",
    )

    def __init__(
        self,
        db: BaseDatos,
        *,
        multa_diaria_centavos: int = PrestamoService.MULTA_DIARIA_CENTAVOS,
    ) -> None:
        self.db = db
        self.multa_diaria_centavos = multa_diaria_centavos

    def generar(self, nombre: str, *, fecha=None) -> list[dict]:
        if nombre not in self.NOMBRES_VALIDOS:
            raise ReglaNegocio(f"Reporte desconocido: {nombre}")
        hoy = normalizar_fecha(fecha).date().isoformat()
        with self.db.conexion() as con:
            prestamo_dao = PrestamoDAO(con)
            ejemplar_dao = EjemplarDAO(con)
            remito_dao = RemitoDAO(con)
            if nombre == "activos_transito":
                return prestamo_dao.reporte_activos_transito()
            if nombre == "vencidos_multas":
                return prestamo_dao.reporte_vencidos_multas(hoy, self.multa_diaria_centavos)
            if nombre == "mas_solicitados":
                return prestamo_dao.reporte_mas_solicitados()
            if nombre == "disponibilidad":
                return ejemplar_dao.reporte_disponibilidad()
            if nombre == "logistica":
                return remito_dao.reporte_logistica()
            return remito_dao.reporte_movimientos()

    def todos(self, *, fecha=None) -> dict[str, list[dict]]:
        return {nombre: self.generar(nombre, fecha=fecha) for nombre in self.NOMBRES_VALIDOS}
