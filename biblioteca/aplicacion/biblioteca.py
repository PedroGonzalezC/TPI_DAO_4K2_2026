"""Casos de uso y reglas de negocio de la biblioteca."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from ..persistencia.base_datos import BaseDatos
from ..persistencia.historial_remito import HistorialRemito
from ..config import BASE_PREDETERMINADA
from ..persistencia.reportes_dao import ReportesDAO
from ..persistencia.catalogo_dao import CatalogoDAO
from ..persistencia.circulacion_dao import CirculacionDAO
from ..dominio.fabrica_prestamos import FabricaPrestamos
from ..dominio.regla_negocio import ReglaNegocio
from ..dominio.remito import Remito


class Biblioteca:
    PLAZO_DIAS = 14
    MULTA_DIARIA_CENTAVOS = 10000  # $100 por día de atraso; decisión configurable.

    def __init__(self, ruta_db: str | Path = BASE_PREDETERMINADA):
        self.db = BaseDatos(ruta_db)
        self.reportes_dao = ReportesDAO(self.db)

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

    @staticmethod
    def _fila(con, tabla: str, id_: int):
        return CatalogoDAO.obtener(con, tabla, id_)

    @classmethod
    def _sede_activa(cls, con, id_: int):
        sede = cls._fila(con, "sedes", id_)
        if not sede["activa"]:
            raise ReglaNegocio(f"La sede {id_} está dada de baja")
        return sede

    @classmethod
    def _socio_habilitado(cls, con, id_: int):
        socio = cls._fila(con, "socios", id_)
        if not socio["habilitado"]:
            raise ReglaNegocio(f"El socio {id_} está inhabilitado")
        return socio

    @staticmethod
    def _crear_unico(operacion, mensaje):
        try:
            return operacion()
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    # Altas, modificaciones y bajas lógicas de datos maestros.
    def crear_sede(self, nombre, direccion, contacto, horarios):
        valores = tuple(self._texto(v, n) for v, n in zip(
            (nombre, direccion, contacto, horarios),
            ("Nombre", "Dirección", "Contacto", "Horarios"),
        ))
        with self.db.conexion() as con:
            return self._crear_unico(lambda: CatalogoDAO.crear_sede(con, valores),
                                     "Ya existe una sede con ese nombre")

    def actualizar_sede(self, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None):
        if activa is not None and activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        with self.db.conexion() as con:
            sede = self._fila(con, "sedes", sede_id)
            CatalogoDAO.actualizar_sede(con, sede_id,
                self._texto(direccion, "Dirección") if direccion is not None else sede["direccion"],
                self._texto(contacto, "Contacto") if contacto is not None else sede["contacto"],
                self._texto(horarios, "Horarios") if horarios is not None else sede["horarios"],
                int(activa) if activa is not None else sede["activa"])

    def crear_socio(self, documento, nombre, email):
        valores = (self._texto(documento, "Documento"), self._texto(nombre, "Nombre"),
                   self._texto(email, "Email"))
        with self.db.conexion() as con:
            return self._crear_unico(lambda: CatalogoDAO.crear_socio(con, valores),
                                     "Ya existe un socio con ese documento")

    def actualizar_socio(self, socio_id, *, nombre=None, email=None, habilitado=None):
        if habilitado is not None and habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        with self.db.conexion() as con:
            socio = self._fila(con, "socios", socio_id)
            CatalogoDAO.actualizar_socio(con, socio_id,
                self._texto(nombre, "Nombre") if nombre is not None else socio["nombre"],
                self._texto(email, "Email") if email is not None else socio["email"],
                int(habilitado) if habilitado is not None else socio["habilitado"])

    def crear_libro(self, isbn, titulo, autor, anio=None):
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        valores = (self._texto(isbn, "ISBN"), self._texto(titulo, "Título"),
                   self._texto(autor, "Autor"), anio)
        with self.db.conexion() as con:
            return self._crear_unico(lambda: CatalogoDAO.crear_libro(con, valores),
                                     "Ya existe un libro con ese ISBN")

    def actualizar_libro(self, libro_id, *, titulo=None, autor=None, anio=None):
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        with self.db.conexion() as con:
            libro = self._fila(con, "libros", libro_id)
            CatalogoDAO.actualizar_libro(con, libro_id,
                self._texto(titulo, "Título") if titulo is not None else libro["titulo"],
                self._texto(autor, "Autor") if autor is not None else libro["autor"],
                anio if anio is not None else libro["anio"])

    def crear_ejemplar(self, codigo, libro_id, sede_id):
        with self.db.conexion() as con:
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            return self._crear_unico(lambda: CatalogoDAO.crear_ejemplar(
                con, self._texto(codigo, "Código"), libro_id, sede_id),
                "Ya existe un ejemplar con ese código")

    def listar(self, tabla: str):
        with self.db.conexion() as con:
            return CatalogoDAO.listar(con, tabla)

    def disponibilidad(self, sede_id=None):
        with self.db.conexion() as con:
            if sede_id is not None:
                self._fila(con, "sedes", sede_id)
            return CatalogoDAO.disponibilidad(con, sede_id)

    # Reserva en espera por libro y sede; la asignación respeta el orden de llegada.
    def reservar(self, socio_id, libro_id, sede_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            reserva_id = self._crear_unico(
                lambda: CirculacionDAO.crear_reserva(con, socio_id, libro_id, sede_id, ahora.isoformat()),
                "El socio ya tiene una reserva activa para ese libro y sede")
            disponible = CirculacionDAO.primer_ejemplar_disponible(con, libro_id, sede_id)
            if disponible:
                self._asignar_reserva(con, disponible["id"])
            return reserva_id

    def _asignar_reserva(self, con, ejemplar_id):
        ejemplar = self._fila(con, "ejemplares", ejemplar_id)
        if ejemplar["estado"] != "DISPONIBLE":
            return
        espera = CirculacionDAO.primera_reserva_en_espera(
            con, ejemplar["libro_id"], ejemplar["sede_actual_id"])
        if espera:
            CirculacionDAO.asignar_reserva(con, espera["id"], ejemplar_id)
            CirculacionDAO.cambiar_estado_ejemplar(con, ejemplar_id, "RESERVADO")

    def cancelar_reserva(self, reserva_id):
        with self.db.conexion() as con:
            reserva = self._fila(con, "reservas", reserva_id)
            if reserva["estado"] not in ("EN_ESPERA", "ASIGNADA"):
                raise ReglaNegocio("La reserva ya está cerrada")
            CirculacionDAO.cambiar_estado_reserva(con, reserva_id, "CANCELADA")
            if reserva["ejemplar_id"]:
                CirculacionDAO.cambiar_estado_ejemplar(con, reserva["ejemplar_id"], "DISPONIBLE")
                self._asignar_reserva(con, reserva["ejemplar_id"])

    def solicitar_prestamo(self, socio_id, ejemplar_id, sede_origen_id, sede_destino_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._sede_activa(con, sede_origen_id)
            self._sede_activa(con, sede_destino_id)
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            if ejemplar["sede_pertenencia_id"] != sede_origen_id or ejemplar["sede_actual_id"] != sede_origen_id:
                raise ReglaNegocio("El ejemplar no pertenece o no se encuentra en la sede de origen")
            if ejemplar["estado"] == "RESERVADO":
                reserva = CirculacionDAO.reserva_del_ejemplar(con, ejemplar_id)
                if reserva is None or reserva["socio_id"] != socio_id or reserva["sede_id"] != sede_destino_id:
                    raise ReglaNegocio("El ejemplar está reservado para otro socio o sede de retiro")
                CirculacionDAO.cambiar_estado_reserva(con, reserva["id"], "CUMPLIDA")
            elif ejemplar["estado"] != "DISPONIBLE":
                raise ReglaNegocio("El ejemplar no está disponible")
            prestamo = FabricaPrestamos.crear(socio_id, ejemplar_id, sede_origen_id, sede_destino_id)
            prestamo_id = CirculacionDAO.crear_prestamo(con, prestamo, ahora.isoformat())
            CirculacionDAO.cambiar_estado_ejemplar(con, ejemplar_id, "APARTADO")
            if prestamo.tipo == "INTERBIBLIOTECARIO":
                self._crear_remito(con, prestamo_id, ejemplar_id, "IDA", sede_origen_id,
                                   sede_destino_id, ahora)
            return prestamo_id

    @staticmethod
    def _crear_remito(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha):
        id_ = CirculacionDAO.crear_remito(
            con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha.isoformat())
        HistorialRemito(con).actualizar(id_, "CREADO", fecha.isoformat(), "Remito generado")
        return id_

    def avanzar_remito(self, remito_id, nuevo_estado, *, fecha=None, detalle=""):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            fila = self._fila(con, "remitos", remito_id)
            ultima = CirculacionDAO.ultima_fecha_remito(con, remito_id)
            if ahora < datetime.fromisoformat(ultima):
                raise ReglaNegocio("El evento no puede preceder al estado anterior del remito")
            if nuevo_estado in {"EMPAQUETADO", "DESPACHADO"}:
                self._sede_activa(con, fila["origen_id"])
                self._sede_activa(con, fila["destino_id"])
            remito = Remito(remito_id, fila["estado"])
            remito.suscribir(HistorialRemito(con))
            remito.avanzar(nuevo_estado, ahora, detalle)
            CirculacionDAO.avanzar_remito(
                con, remito_id, nuevo_estado,
                ahora.isoformat() if nuevo_estado == "RECIBIDO" else fila["recibido_en"])
            if nuevo_estado == "DESPACHADO":
                CirculacionDAO.cambiar_estado_ejemplar(con, fila["ejemplar_id"], "EN_TRANSITO")
                if fila["tipo"] == "IDA":
                    CirculacionDAO.cambiar_estado_prestamo(con, fila["prestamo_id"], "EN_TRANSITO")
            elif nuevo_estado == "RECIBIDO":
                CirculacionDAO.ubicar_ejemplar(con, fila["ejemplar_id"], fila["destino_id"])
                if fila["tipo"] == "IDA":
                    CirculacionDAO.cambiar_estado_ejemplar(con, fila["ejemplar_id"], "APARTADO")
                    CirculacionDAO.cambiar_estado_prestamo(con, fila["prestamo_id"], "LISTO")
                else:
                    prestamo = self._fila(con, "prestamos", fila["prestamo_id"])
                    estado = "DISPONIBLE" if prestamo["condicion_devolucion"] == "BUENO" else "EN_REVISION"
                    CirculacionDAO.cambiar_estado_ejemplar(con, fila["ejemplar_id"], estado)
                    if estado == "DISPONIBLE":
                        self._asignar_reserva(con, fila["ejemplar_id"])

    def entregar_prestamo(self, prestamo_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            requerido = "SOLICITADO" if prestamo["tipo"] == "LOCAL" else "LISTO"
            if prestamo["estado"] != requerido:
                raise ReglaNegocio(f"El préstamo debe estar en estado {requerido} para entregarlo")
            fecha_minima = prestamo["solicitado_en"]
            if prestamo["tipo"] == "INTERBIBLIOTECARIO":
                fecha_minima = CirculacionDAO.fecha_recepcion_ida(con, prestamo_id)
            if ahora < datetime.fromisoformat(fecha_minima):
                raise ReglaNegocio("La entrega no puede preceder a la solicitud o recepción")
            self._socio_habilitado(con, prestamo["socio_id"])
            self._sede_activa(con, prestamo["sede_destino_id"])
            vence = (ahora + timedelta(days=self.PLAZO_DIAS)).date().isoformat()
            CirculacionDAO.activar_prestamo(con, prestamo_id, ahora.isoformat(), vence)
            CirculacionDAO.cambiar_estado_ejemplar(con, prestamo["ejemplar_id"], "PRESTADO")
            return vence

    def devolver_prestamo(self, prestamo_id, condicion="BUENO", *, fecha=None):
        ahora = self._ahora(fecha)
        condicion = self._texto(condicion, "Condición").upper()
        if condicion not in {"BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"}:
            raise ReglaNegocio("Condición de devolución inválida")
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            if prestamo["estado"] != "ACTIVO":
                raise ReglaNegocio("Solo se puede devolver un préstamo activo")
            if ahora < datetime.fromisoformat(prestamo["entregado_en"]):
                raise ReglaNegocio("La devolución no puede preceder a la entrega")
            atraso = max(0, (ahora.date() - date.fromisoformat(prestamo["vence_en"])).days)
            multa = atraso * self.MULTA_DIARIA_CENTAVOS
            CirculacionDAO.devolver_prestamo(con, prestamo_id, ahora.isoformat(), condicion, multa)
            if condicion in {"DESTRUIDO", "EXTRAVIADO"}:
                estado = "BAJA"
            elif prestamo["tipo"] == "INTERBIBLIOTECARIO":
                estado = "POR_RETORNAR"
                self._crear_remito(con, prestamo_id, prestamo["ejemplar_id"], "REGRESO",
                                   prestamo["sede_destino_id"], prestamo["sede_origen_id"], ahora)
            else:
                estado = "DISPONIBLE" if condicion == "BUENO" else "EN_REVISION"
            CirculacionDAO.cambiar_estado_ejemplar(con, prestamo["ejemplar_id"], estado)
            if estado == "DISPONIBLE":
                self._asignar_reserva(con, prestamo["ejemplar_id"])
            return multa

    def cerrar_revision(self, ejemplar_id, apto: bool):
        with self.db.conexion() as con:
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            if ejemplar["estado"] != "EN_REVISION":
                raise ReglaNegocio("El ejemplar no está en revisión")
            estado = "DISPONIBLE" if apto else "BAJA"
            CirculacionDAO.cambiar_estado_ejemplar(con, ejemplar_id, estado)
            if apto:
                self._asignar_reserva(con, ejemplar_id)

    def historial_remito(self, remito_id):
        with self.db.conexion() as con:
            self._fila(con, "remitos", remito_id)
            return CirculacionDAO.historial_remito(con, remito_id)

    def reportes(self, nombre: str, *, fecha=None):
        hoy = self._ahora(fecha).date().isoformat()
        return self.reportes_dao.consultar(nombre, hoy, self.MULTA_DIARIA_CENTAVOS)
