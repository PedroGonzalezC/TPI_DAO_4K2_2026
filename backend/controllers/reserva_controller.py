"""Controller de Reservas: endpoints FastAPI para creación, consulta y cancelación de reservas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.reserva_service import ReservaService
from .dependencias import (
    ROLES_LECTURA,
    ROLES_OPERACION_SOCIO,
    UsuarioActual,
    obtener_reserva_service,
    requerir_autorizacion,
)
from .schemas import ReservaCrearRequest

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])


@router.get("")
def listar_reservas(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[ReservaService, Depends(obtener_reserva_service)],
):
    return servicio.listar_reservas()


@router.post("", status_code=201)
def crear_reserva(
    datos: ReservaCrearRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_OPERACION_SOCIO))],
    servicio: Annotated[ReservaService, Depends(obtener_reserva_service)],
):
    nuevo_id = servicio.reservar(datos.socio_id, datos.libro_id, datos.sede_id)
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.post("/{reserva_id}/cancelar")
@router.delete("/{reserva_id}")
def cancelar_reserva(
    reserva_id: Annotated[int, PathParam(gt=0)],
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_OPERACION_SOCIO))],
    servicio: Annotated[ReservaService, Depends(obtener_reserva_service)],
):
    servicio.cancelar_reserva(reserva_id)
    return {"resultado": "ok"}
