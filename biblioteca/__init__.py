"""Sistema de préstamos interbibliotecarios de la red de bibliotecas."""

from .aplicacion.biblioteca import Biblioteca
from .dominio.regla_negocio import ReglaNegocio

__all__ = ["Biblioteca", "ReglaNegocio"]
