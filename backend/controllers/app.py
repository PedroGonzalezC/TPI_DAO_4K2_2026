"""Aplicación FastAPI principal: registro de routers, traducción de errores de negocio y archivos de presentación."""

import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..models.excepciones import NoAutorizadoError, NoEncontradoError, ReglaNegocio
from ..services.biblioteca_service import Biblioteca
from .catalogo_controller import router as catalogo_router
from .dependencias import ROLES_LECTURA, UsuarioActual, requerir_autorizacion
from .prestamo_controller import router as prestamos_router
from .remito_controller import router as remitos_router
from .reporte_controller import router as reportes_router
from .reserva_controller import router as reservas_router
from .sede_controller import router as sedes_router
from .socio_controller import router as socios_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def crear_app(ruta_db: str | Path | None = None) -> FastAPI:
    ruta_efectiva = Path(ruta_db or os.environ.get("BIBLIOTECA_DB", "biblioteca.db"))
    app = FastAPI(
        title="Red de Bibliotecas - API REST",
        description="Controllers FastAPI en arquitectura por capas para préstamos interbibliotecarios.",
        version="2.0.0",
    )
    app.state.biblioteca = Biblioteca(ruta_efectiva)
    app.state.nombre_base = ruta_efectiva.name

    @app.exception_handler(NoAutorizadoError)
    async def manejar_no_autorizado(_request: Request, exc: NoAutorizadoError):
        mensaje = str(exc)
        return JSONResponse(status_code=403, content={"error": mensaje, "detail": mensaje})

    @app.exception_handler(NoEncontradoError)
    async def manejar_no_encontrado(_request: Request, exc: NoEncontradoError):
        mensaje = str(exc)
        return JSONResponse(status_code=404, content={"error": mensaje, "detail": mensaje})

    @app.exception_handler(ReglaNegocio)
    async def manejar_regla_negocio(_request: Request, exc: ReglaNegocio):
        mensaje = str(exc)
        return JSONResponse(status_code=400, content={"error": mensaje, "detail": mensaje})

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(_request: Request, exc: RequestValidationError):
        errores = exc.errors()
        primer_campo = ".".join(str(x) for x in errores[0].get("loc", [])[1:]) if errores else "datos"
        mensaje = f"Estructura de datos inválida en '{primer_campo or 'solicitud'}'"
        return JSONResponse(
            status_code=400,
            content={"error": mensaje, "detail": errores},
        )

    @app.exception_handler(StarletteHTTPException)
    async def manejar_http_exception(_request: Request, exc: StarletteHTTPException):
        mensaje = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": mensaje, "detail": mensaje},
        )

    @app.get("/api/base", tags=["Sistema"])
    def info_base(
        _usuario: Annotated[UsuarioActual, Depends(requerir_autorizacion(*ROLES_LECTURA))],
        request: Request,
    ):
        nombre = request.app.state.nombre_base
        return {"nombre": nombre, "demo": nombre.startswith("demo_")}

    app.include_router(sedes_router)
    app.include_router(socios_router)
    app.include_router(catalogo_router)
    app.include_router(reservas_router)
    app.include_router(prestamos_router)
    app.include_router(remitos_router)
    app.include_router(reportes_router)

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def servir_index():
        return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html; charset=utf-8")

    @app.get("/styles.css", include_in_schema=False)
    def servir_estilos():
        return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css; charset=utf-8")

    @app.get("/app.js", include_in_schema=False)
    def servir_js():
        return FileResponse(FRONTEND_DIR / "app.js", media_type="text/javascript; charset=utf-8")

    return app
