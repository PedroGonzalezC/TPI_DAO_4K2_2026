"""Capa de Persistencia (DAO): clases encargadas del acceso a la base de datos."""

from .ejemplar_dao import EjemplarDAO
from .evento_remito_dao import EventoRemitoDAO
from .material_dao import LibroDAO, MaterialDAO
from .prestamo_dao import PrestamoDAO
from .remito_dao import RemitoDAO
from .reserva_dao import ReservaDAO
from .sede_dao import SedeDAO
from .socio_dao import SocioDAO
from .solicitud_dao import SolicitudDAO

__all__ = [
    "EjemplarDAO",
    "EventoRemitoDAO",
    "LibroDAO",
    "MaterialDAO",
    "PrestamoDAO",
    "RemitoDAO",
    "ReservaDAO",
    "SedeDAO",
    "SocioDAO",
    "SolicitudDAO",
]
