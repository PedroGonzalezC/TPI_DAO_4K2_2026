"""Controller de Solicitudes y Préstamos: endpoints FastAPI para circulación de ejemplares."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam

from ..services.prestamo_service import PrestamoService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    ROLES_OPERACION_SOCIO,
    UsuarioActual,
    obtener_prestamo_service,
    requerir_autorizacion,
)
from .schemas import DevolucionPrestamoRequest, SolicitudPrestamoRequest

router = APIRouter(prefix="/api", tags=["Solicitudes y Préstamos"])


@router.get("/solicitudes")
def listar_solicitudes(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[PrestamoService, Depends(obtener_prestamo_service)],
):
    return servicio.listar_solicitudes()


@router.get("/prestamos")
def listar_prestamos(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[PrestamoService, Depends(obtener_prestamo_service)],
):
    return servicio.listar_prestamos()


@router.post("/solicitudes", status_code=201)
@router.post("/prestamos", status_code=201)
def solicitar_prestamo(
    datos: SolicitudPrestamoRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_OPERACION_SOCIO))],
    servicio: Annotated[PrestamoService, Depends(obtener_prestamo_service)],
):
    nuevo_id = servicio.solicitar_prestamo(
        datos.socio_id,
        datos.ejemplar_id,
        datos.sede_origen_id,
        datos.sede_destino_id,
        plazo_dias=datos.plazo_dias,
    )
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.post("/prestamos/{prestamo_id}/entregar")
def entregar_prestamo(
    prestamo_id: Annotated[int, PathParam(gt=0)],
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[PrestamoService, Depends(obtener_prestamo_service)],
):
    vence_en = servicio.entregar_prestamo(prestamo_id)
    return {"vence_en": vence_en, "resultado": {"vence_en": vence_en}}


@router.post("/prestamos/{prestamo_id}/devolver")
def devolver_prestamo(
    prestamo_id: Annotated[int, PathParam(gt=0)],
    datos: DevolucionPrestamoRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[PrestamoService, Depends(obtener_prestamo_service)],
):
    multa = servicio.devolver_prestamo(prestamo_id, datos.condicion)
    return {"multa_centavos": multa, "resultado": {"multa_centavos": multa}}
