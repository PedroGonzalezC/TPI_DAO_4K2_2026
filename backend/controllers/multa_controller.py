"""Controller de Multas: endpoints FastAPI para consultar y pagar multas de socios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.multa_service import MultaService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    UsuarioActual,
    obtener_multa_service,
    requerir_autorizacion,
)

router = APIRouter(prefix="/api/multas", tags=["Multas"])


@router.get("")
def listar_multas(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[MultaService, Depends(obtener_multa_service)],
):
    return servicio.listar_multas()


@router.post("/{multa_id}/pagar")
def pagar_multa(
    multa_id: Annotated[int, PathParam(gt=0)],
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[MultaService, Depends(obtener_multa_service)],
):
    servicio.pagar_multa(multa_id)
    return {"resultado": "ok"}
