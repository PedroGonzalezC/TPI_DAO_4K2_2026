"""Servicio de negocio para la gestión y cobro de multas."""

from ..daos.multa_dao import MultaDAO
from ..daos.socio_dao import SocioDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, normalizar_fecha
from .socio_service import SocioService


class MultaService:
    """Gestiona la consulta de multas por atraso y el pago con rehabilitación del socio."""

    def __init__(self, db: BaseDatos) -> None:
        self.db = db

    def listar_multas(self) -> list[dict]:
        with self.db.conexion() as con:
            return MultaDAO(con).listar()

    def pagar_multa(self, multa_id: int, *, fecha=None) -> None:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            multa_dao = MultaDAO(con)
            socio_dao = SocioDAO(con)

            multa = multa_dao.obtener_por_id(multa_id)
            if multa is None:
                raise NoEncontradoError(f"No existe multa con id {multa_id}")

            multa.pagar(ahora)
            multa_dao.actualizar(multa)

            if not multa_dao.tiene_pendientes_por_socio(multa.socio_id):
                socio = SocioService.obtener_existente(con, multa.socio_id)
                socio.actualizar(habilitado=True)
                socio_dao.actualizar(socio)
