"""Controllers HTTP: validación, autenticación y traducción de errores."""

import secrets
import time
from pathlib import Path
from typing import Annotated, Literal, Union

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, create_model

from ..database.configuracion import CONFIG
from ..database.datos import TABLAS
from ..models.modelo import CONDICIONES_BAJA, CONDICIONES_DEVOLUCION, ESTADOS_ENTREGA, ReglaNegocio, Remito
from ..services.operaciones import ejecutar
from ..daos.reportes import REPORTES
from ..services.servicio import Biblioteca
from ..services.usuarios import autenticar


STATIC = Path(__file__).resolve().parents[2] / 'frontend'
SESSION_SECONDS = 8 * 60 * 60


class Credenciales(BaseModel):
    usuario: str = Field(min_length=1, max_length=100)
    clave: str = Field(min_length=1, max_length=1024)


# Esquemas por operación. El discriminador impide invocar métodos arbitrarios.
_campos = {
    'crear_sede': {'nombre': str, 'direccion': str, 'contacto': str, 'horarios': str},
    'editar_sede': {'id': int, 'direccion': str | None, 'contacto': str | None, 'horarios': str | None, 'activa': bool | None},
    'crear_socio': {'documento': str, 'nombre': str, 'email': str},
    'editar_socio': {'id': int, 'nombre': str | None, 'email': str | None, 'habilitado': bool | None},
    'crear_libro': {'isbn': str, 'titulo': str, 'autor': str, 'anio': int | Literal[''] | None},
    'editar_libro': {'id': int, 'titulo': str | None, 'autor': str | None, 'anio': int | Literal[''] | None},
    'crear_ejemplar': {'codigo': str, 'libro_id': int, 'sede_id': int},
    'reservar': {'socio_id': int, 'libro_id': int, 'sede_id': int},
    'cancelar_reserva': {'id': int},
    'solicitar_prestamo': {'socio_id': int, 'ejemplar_id': int, 'sede_origen_id': int, 'sede_destino_id': int},
    'entregar_prestamo': {'id': int},
    'devolver_prestamo': {'id': int, 'condicion': str},
    'avanzar_remito': {'id': int, 'estado': str, 'detalle': str | None},
    'cerrar_revision': {'ejemplar_id': int, 'apto': bool},
}
_modelos = []
for accion, campos in _campos.items():
    # Los campos opcionales solo tienen valor por defecto cuando su tipo admite None.
    atributos = {nombre: (tipo, None if type(None) in getattr(tipo, '__args__', ()) else ...) for nombre, tipo in campos.items()}
    atributos['accion'] = (Literal[accion], ...)
    _modelos.append(create_model(accion, __config__=ConfigDict(extra='forbid'), **atributos))
Accion = Annotated[Union[tuple(_modelos)], Field(discriminator='accion')]


def crear_app(ruta_db=CONFIG['base_datos']):
    biblioteca = Biblioteca(ruta_db)
    app = FastAPI(title='Biblioteca: préstamos interbibliotecarios')
    sesiones = {}

    @app.middleware('http')
    async def seguridad_local(request, call_next):
        host = request.headers.get('host', '').split(':')[0]
        origen = request.headers.get('origin')
        if host not in {'127.0.0.1', 'localhost'} or (origen and origen.rstrip('/') != str(request.base_url).rstrip('/')):
            return JSONResponse({'error': 'Acceso local no permitido'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(ReglaNegocio)
    async def error_negocio(request, exc):
        return JSONResponse({'error': str(exc)}, status_code=400)

    @app.exception_handler(RequestValidationError)
    async def error_validacion(request, exc):
        return JSONResponse({'error': 'La solicitud contiene datos inválidos o incompletos.'}, status_code=422)

    def usuario_actual(request: Request):
        token = request.cookies.get('sesion')
        sesion = sesiones.get(token)
        if not sesion or sesion['vence'] <= time.monotonic():
            sesiones.pop(token, None)
            raise HTTPException(status_code=401, detail='Iniciá sesión para continuar.')
        if sesion['usuario']['rol'] != 'PERSONAL':
            raise HTTPException(status_code=403, detail='No tenés permiso para esta operación.')
        return sesion['usuario']

    @app.post('/api/login')
    def login(datos: Credenciales, response: Response):
        usuario = autenticar(biblioteca.db, datos.usuario, datos.clave)
        if not usuario:
            raise HTTPException(status_code=401, detail='Usuario o contraseña incorrectos.')
        token = secrets.token_urlsafe(32)
        sesiones[token] = {'usuario': usuario, 'vence': time.monotonic() + SESSION_SECONDS}
        response.set_cookie('sesion', token, httponly=True, samesite='strict', max_age=SESSION_SECONDS, path='/')
        return {'usuario': usuario['nombre']}

    @app.post('/api/logout')
    def logout(request: Request, response: Response, usuario=Depends(usuario_actual)):
        sesiones.pop(request.cookies.get('sesion'), None)
        response.delete_cookie('sesion', path='/')
        return {'resultado': 'ok'}

    @app.get('/api/state')
    def estado(usuario=Depends(usuario_actual)):
        return {'tablas': {t: biblioteca.listar(t) for t in TABLAS},
                'reportes': {r: biblioteca.reportes(r) for r in REPORTES},
                'base': {'nombre': Path(ruta_db).name, 'demo': Path(ruta_db).name.startswith('demo_')},
                'configuracion': {k: v for k, v in CONFIG.items() if k not in ('base_datos', 'puerto')},
                'catalogos': {'reportes': {k: titulo for k, (titulo, _) in REPORTES.items()},
                    'transiciones_remito': Remito.TRANSICIONES, 'estados_entrega': ESTADOS_ENTREGA,
                    'condiciones_devolucion': CONDICIONES_DEVOLUCION, 'condiciones_baja': CONDICIONES_BAJA},
                'usuario': usuario['nombre']}

    @app.get('/api/remito/{remito_id}/historial')
    def historial(remito_id: int, usuario=Depends(usuario_actual)):
        return biblioteca.historial_remito(remito_id)

    @app.post('/api/action')
    def accion(datos: Accion, usuario=Depends(usuario_actual)):
        return {'resultado': ejecutar(biblioteca, datos.model_dump(exclude_none=True))}

    @app.get('/')
    def inicio(request: Request):
        try:
            usuario_actual(request)
            return FileResponse(STATIC / 'index.html')
        except HTTPException:
            return FileResponse(STATIC / 'login.html')

    app.mount('/', StaticFiles(directory=STATIC), name='estaticos')
    return app
