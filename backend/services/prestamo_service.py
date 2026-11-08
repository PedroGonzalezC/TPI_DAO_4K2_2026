"""Servicio de negocio para solicitudes, préstamos y devoluciones."""

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.prestamo_dao import PrestamoDAO
from ..daos.remito_dao import RemitoDAO
from ..daos.reserva_dao import ReservaDAO
from ..daos.solicitud_dao import SolicitudDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, ReglaNegocio, normalizar_fecha
from ..models.fabrica_prestamos import FabricaPrestamos
from .catalogo_service import CatalogoService
from .remito_service import RemitoService
from .reserva_service import ReservaService
from .sede_service import SedeService
from .socio_service import SocioService


class PrestamoService:
    """Gestiona solicitudes de préstamo, entregas, devoluciones y cálculo de multas."""

    PLAZO_DIAS = 14
    MULTA_DIARIA_CENTAVOS = 10000

    def __init__(
        self,
        db: BaseDatos,
        reserva_service: ReservaService,
        *,
        plazo_dias: int = PLAZO_DIAS,
        multa_diaria_centavos: int = MULTA_DIARIA_CENTAVOS,
    ) -> None:
        self.db = db
        self.reserva_service = reserva_service
        self.plazo_dias = plazo_dias
        self.multa_diaria_centavos = multa_diaria_centavos

    def solicitar_prestamo(
        self,
        socio_id: int,
        ejemplar_id: int,
        sede_origen_id: int,
        sede_destino_id: int,
        *,
        fecha=None,
    ) -> int:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            SocioService.obtener_habilitado(con, socio_id)
            SedeService.obtener_activa(con, sede_origen_id)
            SedeService.obtener_activa(con, sede_destino_id)

            ejemplar_dao = EjemplarDAO(con)
            reserva_dao = ReservaDAO(con)
            solicitud_dao = SolicitudDAO(con)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, ejemplar_id)
            ejemplar.asegurar_en_sede_origen(sede_origen_id)

            if ejemplar.estado == "RESERVADO":
                reserva = reserva_dao.obtener_asignada_por_ejemplar(ejemplar_id)
                if reserva is None:
                    raise ReglaNegocio(
                        "El ejemplar está reservado para otro socio o sede de retiro"
                    )
                reserva.asegurar_corresponde_a_solicitud(socio_id, sede_destino_id)
                reserva.cumplir()
                reserva_dao.actualizar(reserva)
            elif not ejemplar.esta_disponible:
                raise ReglaNegocio("El ejemplar no está disponible")

            solicitud = FabricaPrestamos.crear(
                socio_id,
                ejemplar_id,
                sede_origen_id,
                sede_destino_id,
                solicitado_en=ahora.isoformat(),
            )
            prestamo_id = solicitud_dao.crear(solicitud)
            ejemplar.apartar()
            ejemplar_dao.actualizar(ejemplar)

            if solicitud.requiere_remito:
                RemitoService.crear_remito_con_evento_inicial(
                    con,
                    prestamo_id=prestamo_id,
                    ejemplar_id=ejemplar_id,
                    tipo="IDA",
                    origen_id=sede_origen_id,
                    destino_id=sede_destino_id,
                    fecha=ahora,
                )
            return prestamo_id

    def entregar_prestamo(self, prestamo_id: int, *, fecha=None) -> str:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            prestamo_dao = PrestamoDAO(con)
            ejemplar_dao = EjemplarDAO(con)
            remito_dao = RemitoDAO(con)

            prestamo = prestamo_dao.obtener_por_id(prestamo_id)
            if prestamo is None:
                raise NoEncontradoError(f"No existe prestamo con id {prestamo_id}")

            fecha_minima = prestamo.solicitado_en
            if prestamo.es_interbibliotecario:
                remito_ida = remito_dao.obtener_por_prestamo_y_tipo(prestamo_id, "IDA")
                if remito_ida is not None and remito_ida.recibido_en is not None:
                    fecha_minima = remito_ida.recibido_en

            vence = prestamo.entregar(ahora, fecha_minima or ahora.isoformat(), self.plazo_dias)
            SocioService.obtener_habilitado(con, prestamo.socio_id)
            SedeService.obtener_activa(con, prestamo.sede_destino_id)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, prestamo.ejemplar_id)
            ejemplar.prestar()

            prestamo_dao.actualizar(prestamo)
            ejemplar_dao.actualizar(ejemplar)
            return vence

    def devolver_prestamo(
        self, prestamo_id: int, condicion: str = "BUENO", *, fecha=None
    ) -> int:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            prestamo_dao = PrestamoDAO(con)
            ejemplar_dao = EjemplarDAO(con)

            prestamo = prestamo_dao.obtener_por_id(prestamo_id)
            if prestamo is None:
                raise NoEncontradoError(f"No existe prestamo con id {prestamo_id}")

            multa, estado_ejemplar = prestamo.devolver(
                ahora, condicion, self.multa_diaria_centavos
            )
            prestamo_dao.actualizar(prestamo)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, prestamo.ejemplar_id)
            ejemplar.estado = estado_ejemplar
            ejemplar_dao.actualizar(ejemplar)

            if estado_ejemplar == "POR_RETORNAR":
                RemitoService.crear_remito_con_evento_inicial(
                    con,
                    prestamo_id=prestamo_id,
                    ejemplar_id=prestamo.ejemplar_id,
                    tipo="REGRESO",
                    origen_id=prestamo.sede_destino_id,
                    destino_id=prestamo.sede_origen_id,
                    fecha=ahora,
                )
            elif estado_ejemplar == "DISPONIBLE":
                self.reserva_service.asignar_si_corresponde(con, prestamo.ejemplar_id)

            return multa

    def listar_prestamos(self) -> list[dict]:
        with self.db.conexion() as con:
            return PrestamoDAO(con).listar()

    def listar_solicitudes(self) -> list[dict]:
        with self.db.conexion() as con:
            return SolicitudDAO(con).listar_pendientes()
