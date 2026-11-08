"""Controller de Remitos: endpoints FastAPI para logística y trazabilidad de traslados."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.remito_service import RemitoService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    UsuarioActual,
    obtener_remito_service,
    requerir_autorizacion,
)
from .schemas import RemitoAvanzarRequest

router = APIRouter(prefix="/api/remitos", tags=["Remitos"])


@router.get("")
def listar_remitos(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[RemitoService, Depends(obtener_remito_service)],
):
    return servicio.listar_remitos()


@router.post("/{remito_id}/avanzar")
def avanzar_remito(
    remito_id: Annotated[int, PathParam(gt=0)],
    datos: RemitoAvanzarRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[RemitoService, Depends(obtener_remito_service)],
):
    servicio.avanzar_remito(remito_id, datos.estado.upper(), detalle=datos.detalle)
    return {"resultado": "ok"}


@router.get("/{remito_id}/historial")
def historial_remito(
    remito_id: Annotated[int, PathParam(gt=0)],
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[RemitoService, Depends(obtener_remito_service)],
):
    return servicio.historial_remito(remito_id)
