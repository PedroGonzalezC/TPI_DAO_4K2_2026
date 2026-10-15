"""Casos de uso y reglas de negocio de la biblioteca."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from ..persistencia.base_datos import BaseDatos
from ..persistencia.historial_remito import HistorialRemito
from ..config import BASE_PREDETERMINADA
from ..persistencia.reportes_dao import ReportesDAO
from ..persistencia.catalogo_dao import CatalogoDAO
from ..persistencia.ejemplar_dao import EjemplarDAO
from ..persistencia.libro_dao import LibroDAO
from ..persistencia.prestamo_dao import PrestamoDAO
from ..persistencia.remito_dao import RemitoDAO
from ..persistencia.reserva_dao import ReservaDAO
from ..persistencia.sede_dao import SedeDAO
from ..persistencia.socio_dao import SocioDAO
from ..dominio.catalogo.ejemplar import Ejemplar
from ..dominio.reservas.reserva import Reserva
from .servicio_catalogo import ServicioCatalogo
from .servicio_personas import ServicioPersonas
from ..dominio.regla_negocio import ReglaNegocio
from ..dominio.prestamos.fabrica_prestamos import FabricaPrestamos


class Biblioteca:
    PLAZO_DIAS = 14
    MULTA_DIARIA_CENTAVOS = 10000  # $100 por día de atraso; decisión configurable.

    def __init__(self, ruta_db: str | Path = BASE_PREDETERMINADA):
        self.db = BaseDatos(ruta_db)
        self.reportes_dao = ReportesDAO(self.db)
        self.catalogo = ServicioCatalogo()
        self.personas = ServicioPersonas()

    @staticmethod
    def _ahora(fecha=None) -> datetime:
        if fecha is None:
            return datetime.now().replace(microsecond=0)
        if isinstance(fecha, date) and not isinstance(fecha, datetime):
            return datetime.combine(fecha, datetime.min.time())
        if not isinstance(fecha, datetime):
            raise ReglaNegocio("La fecha debe ser date o datetime")
        return fecha.replace(microsecond=0)

    @staticmethod
    def _texto(valor, nombre: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocio(f"{nombre} es obligatorio")
        return valor.strip()

    @classmethod
    def _sede_activa(cls, con, id_: int):
        sede = SedeDAO.obtener(con, id_)
        sede.exigir_activa()
        return sede

    @classmethod
    def _socio_habilitado(cls, con, id_: int):
        socio = SocioDAO.obtener(con, id_)
        socio.exigir_habilitado()
        return socio

    @staticmethod
    def _crear_unico(operacion, mensaje):
        try:
            return operacion()
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    # Altas, modificaciones y bajas lógicas de datos maestros.
    def crear_sede(self, nombre, direccion, contacto, horarios):
        with self.db.conexion() as con:
            return self.personas.crear_sede(con, nombre, direccion, contacto, horarios)

    def actualizar_sede(self, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None):
        with self.db.conexion() as con:
            self.personas.actualizar_sede(
                con, sede_id, direccion=direccion, contacto=contacto, horarios=horarios, activa=activa
            )

    def crear_socio(self, documento, nombre, email):
        with self.db.conexion() as con:
            return self.personas.crear_socio(con, documento, nombre, email)

    def actualizar_socio(self, socio_id, *, nombre=None, email=None, habilitado=None):
        with self.db.conexion() as con:
            self.personas.actualizar_socio(con, socio_id, nombre=nombre, email=email, habilitado=habilitado)

    def crear_libro(self, isbn, titulo, autor, anio=None):
        with self.db.conexion() as con:
            return self.catalogo.crear_libro(con, isbn, titulo, autor, anio)

    def actualizar_libro(self, libro_id, *, titulo=None, autor=None, anio=None):
        with self.db.conexion() as con:
            self.catalogo.actualizar_libro(con, libro_id, titulo=titulo, autor=autor, anio=anio)

    def crear_ejemplar(self, codigo, libro_id, sede_id):
        with self.db.conexion() as con:
            return self.catalogo.crear_ejemplar(con, codigo, libro_id, sede_id)

    def listar(self, tabla: str):
        with self.db.conexion() as con:
            return CatalogoDAO.listar(con, tabla)

    def disponibilidad(self, sede_id=None):
        with self.db.conexion() as con:
            return self.catalogo.disponibilidad(con, sede_id)

    # Reserva en espera por libro y sede; la asignación respeta el orden de llegada.
    def reservar(self, socio_id, libro_id, sede_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            LibroDAO.obtener(con, libro_id)
            self._sede_activa(con, sede_id)
            reserva = Reserva(None, socio_id, libro_id, sede_id, ahora.isoformat())
            reserva_id = self._crear_unico(
                lambda: ReservaDAO.crear(con, reserva),
                "El socio ya tiene una reserva activa para ese libro y sede")
            disponible = EjemplarDAO.primero_disponible(con, libro_id, sede_id)
            if disponible:
                self._asignar_reserva(con, disponible.id)
            return reserva_id

    def _asignar_reserva(self, con, ejemplar_id):
        ejemplar = EjemplarDAO.obtener(con, ejemplar_id)
        if ejemplar.estado != "DISPONIBLE":
            return
        espera = ReservaDAO.primera_en_espera(con, ejemplar.libro_id, ejemplar.sede_actual_id)
        if espera:
            espera.asignar_ejemplar(ejemplar_id)
            ejemplar.avanzar("RESERVADO")
            ReservaDAO.guardar(con, espera)
            EjemplarDAO.guardar(con, ejemplar)

    def cancelar_reserva(self, reserva_id):
        with self.db.conexion() as con:
            reserva = ReservaDAO.obtener(con, reserva_id)
            if reserva.estado not in ("EN_ESPERA", "ASIGNADA"):
                raise ReglaNegocio("La reserva ya está cerrada")
            reserva.avanzar("CANCELADA")
            ReservaDAO.guardar(con, reserva)
            if reserva.ejemplar_id:
                ejemplar = EjemplarDAO.obtener(con, reserva.ejemplar_id)
                ejemplar.avanzar("DISPONIBLE")
                EjemplarDAO.guardar(con, ejemplar)
                self._asignar_reserva(con, reserva.ejemplar_id)

    def solicitar_prestamo(self, socio_id, ejemplar_id, sede_origen_id, sede_destino_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._sede_activa(con, sede_origen_id)
            self._sede_activa(con, sede_destino_id)
            ejemplar = EjemplarDAO.obtener(con, ejemplar_id)
            if ejemplar.sede_pertenencia_id != sede_origen_id or ejemplar.sede_actual_id != sede_origen_id:
                raise ReglaNegocio("El ejemplar no pertenece o no se encuentra en la sede de origen")
            if ejemplar.estado == "RESERVADO":
                reserva = ReservaDAO.asignada_del_ejemplar(con, ejemplar_id)
                if reserva is None or reserva.socio_id != socio_id or reserva.sede_id != sede_destino_id:
                    raise ReglaNegocio("El ejemplar está reservado para otro socio o sede de retiro")
                reserva.avanzar("CUMPLIDA")
                ReservaDAO.guardar(con, reserva)
            elif ejemplar.estado != "DISPONIBLE":
                raise ReglaNegocio("El ejemplar no está disponible")
            prestamo = FabricaPrestamos.crear(socio_id, ejemplar_id, sede_origen_id, sede_destino_id)
            prestamo_id = PrestamoDAO.crear(con, prestamo, ahora.isoformat())
            ejemplar.avanzar("APARTADO")
            EjemplarDAO.guardar(con, ejemplar)
            if prestamo.tipo == "INTERBIBLIOTECARIO":
                self._crear_remito(con, prestamo_id, ejemplar_id, "IDA", sede_origen_id,
                                   sede_destino_id, ahora)
            return prestamo_id

    @staticmethod
    def _crear_remito(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha):
        id_ = RemitoDAO.crear(
            con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha.isoformat())
        HistorialRemito(con).actualizar(id_, "CREADO", fecha.isoformat(), "Remito generado")
        return id_

    def avanzar_remito(self, remito_id, nuevo_estado, *, fecha=None, detalle=""):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            remito, fila = RemitoDAO.obtener(con, remito_id)
            ultima = RemitoDAO.ultima_fecha(con, remito_id)
            if ahora < datetime.fromisoformat(ultima):
                raise ReglaNegocio("El evento no puede preceder al estado anterior del remito")
            if nuevo_estado in {"EMPAQUETADO", "DESPACHADO"}:
                self._sede_activa(con, fila["origen_id"])
                self._sede_activa(con, fila["destino_id"])
            remito.suscribir(HistorialRemito(con))
            remito.avanzar(nuevo_estado, ahora, detalle)
            RemitoDAO.guardar(
                con, remito,
                ahora.isoformat() if nuevo_estado == "RECIBIDO" else fila["recibido_en"])
            if nuevo_estado == "DESPACHADO":
                ejemplar = EjemplarDAO.obtener(con, fila["ejemplar_id"])
                ejemplar.avanzar("EN_TRANSITO")
                EjemplarDAO.guardar(con, ejemplar)
                if fila["tipo"] == "IDA":
                    prestamo, _ = PrestamoDAO.obtener(con, fila["prestamo_id"])
                    prestamo.avanzar("EN_TRANSITO")
                    PrestamoDAO.guardar_estado(con, fila["prestamo_id"], prestamo)
            elif nuevo_estado == "RECIBIDO":
                ejemplar = EjemplarDAO.obtener(con, fila["ejemplar_id"])
                ejemplar.ubicar_en(fila["destino_id"])
                if fila["tipo"] == "IDA":
                    ejemplar.avanzar("APARTADO")
                    prestamo, _ = PrestamoDAO.obtener(con, fila["prestamo_id"])
                    prestamo.avanzar("LISTO")
                    PrestamoDAO.guardar_estado(con, fila["prestamo_id"], prestamo)
                else:
                    _, prestamo_fila = PrestamoDAO.obtener(con, fila["prestamo_id"])
                    estado = "DISPONIBLE" if prestamo_fila["condicion_devolucion"] == "BUENO" else "EN_REVISION"
                    ejemplar.avanzar(estado)
                    EjemplarDAO.guardar(con, ejemplar)
                    if ejemplar.estado == "DISPONIBLE":
                        self._asignar_reserva(con, fila["ejemplar_id"])
                if fila["tipo"] == "IDA":
                    EjemplarDAO.guardar(con, ejemplar)

    def entregar_prestamo(self, prestamo_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            prestamo, fila = PrestamoDAO.obtener(con, prestamo_id)
            requerido = "SOLICITADO" if prestamo.tipo == "LOCAL" else "LISTO"
            if prestamo.estado != requerido:
                raise ReglaNegocio(f"El préstamo debe estar en estado {requerido} para entregarlo")
            fecha_minima = fila["solicitado_en"]
            if prestamo.tipo == "INTERBIBLIOTECARIO":
                fecha_minima = RemitoDAO.fecha_recepcion_ida(con, prestamo_id)
            if ahora < datetime.fromisoformat(fecha_minima):
                raise ReglaNegocio("La entrega no puede preceder a la solicitud o recepción")
            self._socio_habilitado(con, prestamo.socio_id)
            self._sede_activa(con, prestamo.sede_destino_id)
            vence = (ahora + timedelta(days=self.PLAZO_DIAS)).date().isoformat()
            prestamo.avanzar("ACTIVO")
            PrestamoDAO.activar(con, prestamo_id, prestamo, ahora.isoformat(), vence)
            ejemplar = EjemplarDAO.obtener(con, prestamo.ejemplar_id)
            ejemplar.avanzar("PRESTADO")
            EjemplarDAO.guardar(con, ejemplar)
            return vence

    def devolver_prestamo(self, prestamo_id, condicion="BUENO", *, fecha=None):
        ahora = self._ahora(fecha)
        condicion = self._texto(condicion, "Condición").upper()
        if condicion not in {"BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"}:
            raise ReglaNegocio("Condición de devolución inválida")
        with self.db.conexion() as con:
            prestamo, fila = PrestamoDAO.obtener(con, prestamo_id)
            if prestamo.estado != "ACTIVO":
                raise ReglaNegocio("Solo se puede devolver un préstamo activo")
            if ahora < datetime.fromisoformat(fila["entregado_en"]):
                raise ReglaNegocio("La devolución no puede preceder a la entrega")
            atraso = max(0, (ahora.date() - date.fromisoformat(fila["vence_en"])).days)
            multa = atraso * self.MULTA_DIARIA_CENTAVOS
            prestamo.avanzar("DEVUELTO")
            PrestamoDAO.devolver(con, prestamo_id, prestamo, ahora.isoformat(), condicion, multa)
            ejemplar = EjemplarDAO.obtener(con, prestamo.ejemplar_id)
            if condicion in {"DESTRUIDO", "EXTRAVIADO"}:
                estado = "BAJA"
            elif prestamo.tipo == "INTERBIBLIOTECARIO":
                estado = "POR_RETORNAR"
                self._crear_remito(con, prestamo_id, prestamo.ejemplar_id, "REGRESO",
                                   prestamo.sede_destino_id, prestamo.sede_origen_id, ahora)
            else:
                estado = "DISPONIBLE" if condicion == "BUENO" else "EN_REVISION"
            ejemplar.avanzar(estado)
            EjemplarDAO.guardar(con, ejemplar)
            if estado == "DISPONIBLE":
                self._asignar_reserva(con, prestamo.ejemplar_id)
            return multa

    def cerrar_revision(self, ejemplar_id, apto: bool):
        with self.db.conexion() as con:
            ejemplar = EjemplarDAO.obtener(con, ejemplar_id)
            if ejemplar.estado != "EN_REVISION":
                raise ReglaNegocio("El ejemplar no está en revisión")
            estado = "DISPONIBLE" if apto else "BAJA"
            ejemplar.avanzar(estado)
            EjemplarDAO.guardar(con, ejemplar)
            if apto:
                self._asignar_reserva(con, ejemplar_id)

    def historial_remito(self, remito_id):
        with self.db.conexion() as con:
            RemitoDAO.obtener(con, remito_id)
            return RemitoDAO.historial(con, remito_id)

    def reportes(self, nombre: str, *, fecha=None):
        hoy = self._ahora(fecha).date().isoformat()
        return self.reportes_dao.consultar(nombre, hoy, self.MULTA_DIARIA_CENTAVOS)
