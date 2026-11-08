"""Controller de Sedes: endpoints FastAPI para gestionar sedes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.sede_service import SedeService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    UsuarioActual,
    obtener_sede_service,
    requerir_autorizacion,
)
from .schemas import SedeActualizarRequest, SedeCrearRequest

router = APIRouter(prefix="/api/sedes", tags=["Sedes"])


@router.get("")
def listar_sedes(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[SedeService, Depends(obtener_sede_service)],
):
    return servicio.listar_sedes()


@router.post("", status_code=201)
def crear_sede(
    datos: SedeCrearRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[SedeService, Depends(obtener_sede_service)],
):
    nuevo_id = servicio.crear_sede(
        datos.nombre, datos.direccion, datos.contacto, datos.horarios
    )
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.patch("/{sede_id}")
def actualizar_sede(
    sede_id: Annotated[int, PathParam(gt=0)],
    datos: SedeActualizarRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[SedeService, Depends(obtener_sede_service)],
):
    servicio.actualizar_sede(
        sede_id,
        direccion=datos.direccion,
        contacto=datos.contacto,
        horarios=datos.horarios,
        activa=datos.activa,
    )
    return {"resultado": "ok"}
