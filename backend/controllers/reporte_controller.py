"""Controller de Reportes: endpoints FastAPI para consultas analíticas."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..services.reporte_service import ReporteService
from .dependencias import (
    ROLES_LECTURA,
    UsuarioActual,
    obtener_reporte_service,
    requerir_autorizacion,
)

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


@router.get("")
def obtener_todos_los_reportes(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[ReporteService, Depends(obtener_reporte_service)],
):
    return servicio.todos()


@router.get("/{nombre}")
def obtener_reporte(
    nombre: str,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[ReporteService, Depends(obtener_reporte_service)],
):
    return servicio.generar(nombre)
