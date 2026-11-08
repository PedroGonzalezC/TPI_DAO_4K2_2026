"""Identificación de usuario, autorización por rol e inyección de servicios en FastAPI."""

from typing import Annotated

from fastapi import Depends, Header, Request
from pydantic import BaseModel

from ..models.excepciones import NoAutorizadoError
from ..services import (
    Biblioteca,
    CatalogoService,
    PrestamoService,
    RemitoService,
    ReporteService,
    ReservaService,
    SedeService,
    SocioService,
)


class UsuarioActual(BaseModel):
    identificador: str
    rol: str


ROLES_LECTURA = ("BIBLIOTECARIO", "ADMIN", "SOCIO")
ROLES_OPERACION_SOCIO = ("BIBLIOTECARIO", "ADMIN", "SOCIO")
ROLES_GESTION = ("BIBLIOTECARIO", "ADMIN")


def identificar_usuario(
    x_usuario: Annotated[str | None, Header()] = "operador-local",
    x_rol: Annotated[str | None, Header()] = "BIBLIOTECARIO",
) -> UsuarioActual:
    """Identifica al usuario a partir de los encabezados HTTP."""
    identificador = (x_usuario or "").strip()
    rol = (x_rol or "").strip().upper()
    if not identificador:
        raise NoAutorizadoError("Debe identificarse un usuario válido")
    return UsuarioActual(identificador=identificador, rol=rol)


def requerir_autorizacion(*roles_permitidos: str):
    """Comprueba que el usuario identificado posea un rol autorizado."""

    def _verificar(
        usuario: Annotated[UsuarioActual, Depends(identificar_usuario)],
    ) -> UsuarioActual:
        if usuario.rol not in roles_permitidos:
            raise NoAutorizadoError(
                f"El rol '{usuario.rol}' no está autorizado para realizar esta operación"
            )
        return usuario

    return _verificar


def obtener_biblioteca(request: Request) -> Biblioteca:
    return request.app.state.biblioteca


def obtener_sede_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> SedeService:
    return b.sedes


def obtener_socio_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> SocioService:
    return b.socios


def obtener_catalogo_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> CatalogoService:
    return b.catalogo


def obtener_reserva_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> ReservaService:
    return b.reservas


def obtener_prestamo_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> PrestamoService:
    return b.prestamos


def obtener_remito_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> RemitoService:
    return b.remitos


def obtener_reporte_service(
    b: Annotated[Biblioteca, Depends(obtener_biblioteca)],
) -> ReporteService:
    return b.servicio_reportes
