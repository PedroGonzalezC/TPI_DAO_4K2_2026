"""Excepciones y validaciones transversales del dominio."""

from datetime import date, datetime


class ReglaNegocio(ValueError):
    """Una operación incumple una regla del dominio."""


class NoEncontradoError(ReglaNegocio):
    """No existe la entidad solicitada en el sistema."""


class NoAutorizadoError(PermissionError):
    """El usuario no posee permisos para ejecutar la operación."""


def validar_texto_obligatorio(valor: str, nombre: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ReglaNegocio(f"{nombre} es obligatorio")
    return valor.strip()


def normalizar_fecha(fecha: datetime | date | None = None) -> datetime:
    if fecha is None:
        return datetime.now().replace(microsecond=0)
    if isinstance(fecha, date) and not isinstance(fecha, datetime):
        return datetime.combine(fecha, datetime.min.time())
    if not isinstance(fecha, datetime):
        raise ReglaNegocio("La fecha debe ser date o datetime")
    return fecha.replace(microsecond=0)
