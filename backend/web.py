"""Punto de entrada y configuración del servidor web FastAPI para la interfaz de la biblioteca."""

import argparse
import os
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .controllers.catalogo_controller import router as catalogo_router
from .controllers.dependencias import ROLES_LECTURA, UsuarioActual, requerir_autorizacion
from .controllers.multa_controller import router as multas_router
from .controllers.prestamo_controller import router as prestamos_router
from .controllers.remito_controller import router as remitos_router
from .controllers.reporte_controller import router as reportes_router
from .controllers.reserva_controller import router as reservas_router
from .controllers.sede_controller import router as sedes_router
from .controllers.socio_controller import router as socios_router
from .models.excepciones import NoAutorizadoError, NoEncontradoError, ReglaNegocio
from .services.biblioteca_service import Biblioteca

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def crear_app(ruta_db: str | Path | None = None) -> FastAPI:
    ruta_efectiva = Path(ruta_db or os.environ.get("BIBLIOTECA_DB", "demo_biblioteca.db"))
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
    app.include_router(multas_router)
    app.include_router(reportes_router)

    # Sirve directamente la carpeta frontend/ (index.html, styles.css y componentes React en src/)
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor FastAPI local de la biblioteca")
    parser.add_argument("--db", default="demo_biblioteca.db", help="Ruta de la base SQLite")
    parser.add_argument("--port", type=int, default=8000, help="Puerto local (por defecto 8000)")
    args = parser.parse_args()
    ruta_db = Path(args.db)
    if not ruta_db.exists() or ruta_db.stat().st_size == 0:
        from .demo import poblar

        poblar(ruta_db, reset=False)
    app = crear_app(ruta_db)
    if not app.state.biblioteca.listar("sedes"):
        from .demo import poblar

        poblar(ruta_db, reset=False)
    print(f"Biblioteca disponible en http://127.0.0.1:{args.port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
