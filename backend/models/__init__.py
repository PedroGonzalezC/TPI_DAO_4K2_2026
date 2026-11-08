"""Capa de Dominio (Models): entidades y patrones del sistema."""

from .ejemplar import Ejemplar
from .evento_remito import EventoRemito
from .excepciones import (
    NoAutorizadoError,
    NoEncontradoError,
    ReglaNegocio,
    normalizar_fecha,
    validar_texto_obligatorio,
)
from .fabrica_prestamos import FabricaPrestamos
from .material import Libro, Material
from .observador_remito import ObservadorRemito
from .prestamo import (
    Prestamo,
    PrestamoInterbibliotecario,
    PrestamoLocal,
    SolicitudPrestamo,
)
from .remito import Remito
from .reserva import Reserva
from .sede import Sede
from .socio import Socio

__all__ = [
    "Ejemplar",
    "EventoRemito",
    "FabricaPrestamos",
    "Libro",
    "Material",
    "NoAutorizadoError",
    "NoEncontradoError",
    "ObservadorRemito",
    "Prestamo",
    "PrestamoInterbibliotecario",
    "PrestamoLocal",
    "ReglaNegocio",
    "Remito",
    "Reserva",
    "Sede",
    "Socio",
    "SolicitudPrestamo",
    "normalizar_fecha",
    "validar_texto_obligatorio",
]
