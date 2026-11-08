"""Fachada de aplicación que coordina los servicios de negocio."""

from pathlib import Path

from ..database.conexion import BaseDatos
from ..models.excepciones import ReglaNegocio
from .catalogo_service import CatalogoService
from .multa_service import MultaService
from .prestamo_service import PrestamoService
from .remito_service import RemitoService
from .reporte_service import ReporteService
from .reserva_service import ReservaService
from .sede_service import SedeService
from .socio_service import SocioService


class Biblioteca:
    """Coordina todos los servicios de dominio sobre la base SQLite."""

    PLAZO_DIAS = PrestamoService.PLAZO_DIAS
    MULTA_DIARIA_CENTAVOS = PrestamoService.MULTA_DIARIA_CENTAVOS

    def __init__(self, ruta_db: str | Path = "biblioteca.db") -> None:
        self.db = BaseDatos(ruta_db)
        self.sedes = SedeService(self.db)
        self.socios = SocioService(self.db)
        self.reservas = ReservaService(self.db)
        self.catalogo = CatalogoService(self.db, self.reservas)
        self.prestamos = PrestamoService(
            self.db,
            self.reservas,
            plazo_dias=self.PLAZO_DIAS,
            multa_diaria_centavos=self.MULTA_DIARIA_CENTAVOS,
        )
        self.remitos = RemitoService(self.db, self.reservas)
        self.multas = MultaService(self.db)
        self.servicio_reportes = ReporteService(
            self.db, multa_diaria_centavos=self.MULTA_DIARIA_CENTAVOS
        )

    def crear_sede(self, nombre, direccion, contacto, horarios):
        return self.sedes.crear_sede(nombre, direccion, contacto, horarios)

    def actualizar_sede(
        self, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None
    ):
        return self.sedes.actualizar_sede(
            sede_id,
            direccion=direccion,
            contacto=contacto,
            horarios=horarios,
            activa=activa,
        )

    def crear_socio(self, documento, nombre, email):
        return self.socios.crear_socio(documento, nombre, email)

    def actualizar_socio(
        self, socio_id, *, nombre=None, email=None, habilitado=None
    ):
        return self.socios.actualizar_socio(
            socio_id, nombre=nombre, email=email, habilitado=habilitado
        )

    def crear_libro(self, isbn, titulo, autor, anio=None):
        return self.catalogo.crear_material(isbn, titulo, autor, anio)

    def actualizar_libro(self, libro_id, *, titulo=None, autor=None, anio=None):
        return self.catalogo.actualizar_material(
            libro_id, titulo=titulo, autor=autor, anio=anio
        )

    def crear_ejemplar(self, codigo, libro_id, sede_id, condicion="BUENO"):
        return self.catalogo.crear_ejemplar(codigo, libro_id, sede_id, condicion=condicion)

    def listar(self, tabla: str):
        listadores = {
            "sedes": self.sedes.listar_sedes,
            "socios": self.socios.listar_socios,
            "libros": self.catalogo.listar_materiales,
            "ejemplares": self.catalogo.listar_ejemplares,
            "reservas": self.reservas.listar_reservas,
            "prestamos": self.prestamos.listar_prestamos,
            "remitos": self.remitos.listar_remitos,
            "multas": self.multas.listar_multas,
        }
        if tabla not in listadores:
            raise ReglaNegocio("Listado desconocido")
        return listadores[tabla]()

    def disponibilidad(self, sede_id=None):
        return self.catalogo.disponibilidad(sede_id)

    def reservar(self, socio_id, libro_id, sede_id, *, fecha=None):
        return self.reservas.reservar(socio_id, libro_id, sede_id, fecha=fecha)

    def cancelar_reserva(self, reserva_id):
        return self.reservas.cancelar_reserva(reserva_id)

    def solicitar_prestamo(
        self,
        socio_id,
        ejemplar_id,
        sede_origen_id,
        sede_destino_id,
        *,
        plazo_dias=None,
        fecha=None,
    ):
        return self.prestamos.solicitar_prestamo(
            socio_id,
            ejemplar_id,
            sede_origen_id,
            sede_destino_id,
            plazo_dias=plazo_dias,
            fecha=fecha,
        )

    def avanzar_remito(self, remito_id, nuevo_estado, *, fecha=None, detalle=""):
        return self.remitos.avanzar_remito(
            remito_id, nuevo_estado, fecha=fecha, detalle=detalle
        )

    def entregar_prestamo(self, prestamo_id, *, plazo_dias=None, fecha=None):
        return self.prestamos.entregar_prestamo(
            prestamo_id, plazo_dias=plazo_dias, fecha=fecha
        )

    def devolver_prestamo(self, prestamo_id, condicion="BUENO", *, fecha=None):
        return self.prestamos.devolver_prestamo(prestamo_id, condicion, fecha=fecha)

    def pagar_multa(self, multa_id, *, fecha=None):
        return self.multas.pagar_multa(multa_id, fecha=fecha)

    def cerrar_revision(self, ejemplar_id, apto: bool):
        return self.catalogo.cerrar_revision(ejemplar_id, apto)

    def historial_remito(self, remito_id):
        return self.remitos.historial_remito(remito_id)

    def reportes(self, nombre: str, *, fecha=None):
        return self.servicio_reportes.generar(nombre, fecha=fecha)
