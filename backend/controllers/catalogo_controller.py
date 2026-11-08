"""Controller de Catálogo: endpoints FastAPI para materiales (libros), ejemplares y disponibilidad."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path as PathParam, Query

from ..services.catalogo_service import CatalogoService
from .dependencias import (
    ROLES_GESTION,
    ROLES_LECTURA,
    UsuarioActual,
    obtener_catalogo_service,
    requerir_autorizacion,
)
from .schemas import (
    EjemplarCrearRequest,
    MaterialActualizarRequest,
    MaterialCrearRequest,
    RevisionCerrarRequest,
)

router = APIRouter(prefix="/api", tags=["Catálogo y Ejemplares"])


@router.get("/libros")
@router.get("/materiales")
def listar_materiales(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    return servicio.listar_materiales()


@router.post("/libros", status_code=201)
@router.post("/materiales", status_code=201)
def crear_material(
    datos: MaterialCrearRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    nuevo_id = servicio.crear_material(datos.isbn, datos.titulo, datos.autor, datos.anio)
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.patch("/libros/{libro_id}")
@router.patch("/materiales/{libro_id}")
def actualizar_material(
    libro_id: Annotated[int, PathParam(gt=0)],
    datos: MaterialActualizarRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    servicio.actualizar_material(
        libro_id, titulo=datos.titulo, autor=datos.autor, anio=datos.anio
    )
    return {"resultado": "ok"}


@router.get("/ejemplares")
def listar_ejemplares(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    return servicio.listar_ejemplares()


@router.post("/ejemplares", status_code=201)
def crear_ejemplar(
    datos: EjemplarCrearRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    nuevo_id = servicio.crear_ejemplar(datos.codigo, datos.libro_id, datos.sede_id)
    return {"id": nuevo_id, "resultado": nuevo_id}


@router.post("/ejemplares/{ejemplar_id}/revision")
def cerrar_revision_ejemplar(
    ejemplar_id: Annotated[int, PathParam(gt=0)],
    datos: RevisionCerrarRequest,
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_GESTION))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
):
    servicio.cerrar_revision(ejemplar_id, datos.apto)
    return {"resultado": "ok"}


@router.get("/disponibilidad")
def consultar_disponibilidad(
    _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
    servicio: Annotated[CatalogoService, Depends(obtener_catalogo_service)],
    sede_id: Annotated[int | None, Query(gt=0)] = None,
):
    return servicio.disponibilidad(sede_id)
