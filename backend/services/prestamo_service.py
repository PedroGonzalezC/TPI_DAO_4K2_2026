"""Servicio de negocio para solicitudes, préstamos y devoluciones."""

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.multa_dao import MultaDAO
from ..daos.prestamo_dao import PrestamoDAO
from ..daos.remito_dao import RemitoDAO
from ..daos.reserva_dao import ReservaDAO
from ..daos.socio_dao import SocioDAO
from ..daos.solicitud_dao import SolicitudDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, ReglaNegocio, normalizar_fecha
from ..models.fabrica_prestamos import FabricaPrestamos
from ..models.multa import Multa
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
        plazo_dias: int | None = None,
        fecha=None,
    ) -> int:
        ahora = normalizar_fecha(fecha)
        plazo = self.plazo_dias if plazo_dias is None else int(plazo_dias)
        if plazo <= 0:
            raise ReglaNegocio("La duración del préstamo debe ser mayor a cero días")
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
            else:
                reserva_socio = reserva_dao.obtener_activa_por_socio_libro_sede(
                    socio_id, ejemplar.libro_id, sede_destino_id
                )
                if reserva_socio is not None:
                    ejemplar_anterior_id = reserva_socio.ejemplar_id
                    reserva_socio.estado = "CUMPLIDA"
                    reserva_dao.actualizar(reserva_socio)
                    if ejemplar_anterior_id is not None and ejemplar_anterior_id != ejemplar_id:
                        ejemplar_anterior = ejemplar_dao.obtener_por_id(ejemplar_anterior_id)
                        if ejemplar_anterior is not None and ejemplar_anterior.estado == "RESERVADO":
                            ejemplar_anterior.liberar()
                            ejemplar_dao.actualizar(ejemplar_anterior)
                            self.reserva_service.asignar_si_corresponde(con, ejemplar_anterior_id)

            solicitud = FabricaPrestamos.crear(
                socio_id,
                ejemplar_id,
                sede_origen_id,
                sede_destino_id,
                plazo_dias=plazo,
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

    def entregar_prestamo(
        self, prestamo_id: int, *, plazo_dias: int | None = None, fecha=None
    ) -> str:
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

            plazo = prestamo.plazo_dias if plazo_dias is None else int(plazo_dias)
            vence = prestamo.entregar(ahora, fecha_minima or ahora.isoformat(), plazo)
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

            if multa > 0:
                dias_atraso = max(1, multa // self.multa_diaria_centavos)
                nueva_multa = Multa(
                    prestamo_id=prestamo_id,
                    socio_id=prestamo.socio_id,
                    monto_centavos=multa,
                    dias_atraso=dias_atraso,
                    estado="PENDIENTE",
                    creada_en=ahora.isoformat(),
                )
                MultaDAO(con).crear(nueva_multa)
                socio = SocioService.obtener_existente(con, prestamo.socio_id)
                socio.actualizar(habilitado=False)
                SocioDAO(con).actualizar(socio)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, prestamo.ejemplar_id)
            ejemplar.estado = estado_ejemplar
            if prestamo.condicion_devolucion:
                ejemplar.condicion = prestamo.condicion_devolucion
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

    def cancelar_prestamo(self, prestamo_id: int) -> None:
        with self.db.conexion() as con:
            prestamo_dao = PrestamoDAO(con)
            ejemplar_dao = EjemplarDAO(con)
            remito_dao = RemitoDAO(con)

            prestamo = prestamo_dao.obtener_por_id(prestamo_id)
            if prestamo is None:
                raise NoEncontradoError(f"No existe prestamo con id {prestamo_id}")

            if prestamo.es_interbibliotecario:
                remito_ida = remito_dao.obtener_por_prestamo_y_tipo(prestamo_id, "IDA")
                if remito_ida is not None:
                    if remito_ida.estado != "CREADO":
                        raise ReglaNegocio(
                            "No se puede cancelar una solicitud cuyo remito ya fue preparado o despachado"
                        )
                    remito_dao.eliminar(remito_ida.id)

            prestamo.cancelar()
            prestamo_dao.actualizar(prestamo)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, prestamo.ejemplar_id)
            ejemplar.liberar()
            ejemplar_dao.actualizar(ejemplar)
            self.reserva_service.asignar_si_corresponde(con, prestamo.ejemplar_id)

    def listar_prestamos(self) -> list[dict]:
        with self.db.conexion() as con:
            return PrestamoDAO(con).listar()

    def listar_solicitudes(self) -> list[dict]:
        with self.db.conexion() as con:
            return SolicitudDAO(con).listar_pendientes()
