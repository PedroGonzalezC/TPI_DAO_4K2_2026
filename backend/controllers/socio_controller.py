"""Controller de Socios: endpoints FastAPI para gestionar el padrón de socios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.socio_service import SocioService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    UsuarioActual,
    obtener_socio_service,
    requerir_autorizacion,
)
from .schemas import SocioActualizarRequest, SocioCrearRequest

router = APIRouter(prefix="/api/socios", tags=["Socios"])


@router.get("")
def listar_socios(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[SocioService, Depends(obtener_socio_service)],
):
    return servicio.listar_socios()


@router.post("", status_code=201)
def crear_socio(
    datos: SocioCrearRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[SocioService, Depends(obtener_socio_service)],
):
    nuevo_id = servicio.crear_socio(datos.documento, datos.nombre, datos.email)
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.patch("/{socio_id}")
def actualizar_socio(
    socio_id: Annotated[int, PathParam(gt=0)],
    datos: SocioActualizarRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[SocioService, Depends(obtener_socio_service)],
):
    servicio.actualizar_socio(
        socio_id,
        nombre=datos.nombre,
        email=datos.email,
        habilitado=datos.habilitado,
    )
    return {"resultado": "ok"}


@router.delete("/{socio_id}")
def eliminar_socio(
    socio_id: Annotated[int, PathParam(gt=0)],
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[SocioService, Depends(obtener_socio_service)],
):
    accion = servicio.eliminar_socio(socio_id)
    return {"resultado": accion}
