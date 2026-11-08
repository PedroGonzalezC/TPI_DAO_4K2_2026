"""Esquemas Pydantic para validar la estructura de los datos recibidos en los Controllers."""

from pydantic import BaseModel, ConfigDict, Field


class ModeloEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SedeCrearRequest(ModeloEntrada):
    nombre: str = Field(..., min_length=1)
    direccion: str = Field(..., min_length=1)
    contacto: str = Field(..., min_length=1)
    horarios: str = Field(..., min_length=1)


class SedeActualizarRequest(ModeloEntrada):
    direccion: str | None = None
    contacto: str | None = None
    horarios: str | None = None
    activa: bool | int | None = None


class SocioCrearRequest(ModeloEntrada):
    documento: str = Field(..., min_length=1)
    nombre: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)


class SocioActualizarRequest(ModeloEntrada):
    nombre: str | None = None
    email: str | None = None
    habilitado: bool | int | None = None


class MaterialCrearRequest(ModeloEntrada):
    isbn: str = Field(..., min_length=1)
    titulo: str = Field(..., min_length=1)
    autor: str = Field(..., min_length=1)
    anio: int | None = None


class MaterialActualizarRequest(ModeloEntrada):
    titulo: str | None = None
    autor: str | None = None
    anio: int | None = None


class EjemplarCrearRequest(ModeloEntrada):
    codigo: str = Field(..., min_length=1)
    libro_id: int = Field(..., gt=0)
    sede_id: int = Field(..., gt=0)
    condicion: str = Field(default="BUENO", min_length=1)


class RevisionCerrarRequest(ModeloEntrada):
    apto: bool


class ReservaCrearRequest(ModeloEntrada):
    socio_id: int = Field(..., gt=0)
    libro_id: int = Field(..., gt=0)
    sede_id: int = Field(..., gt=0)


class SolicitudPrestamoRequest(ModeloEntrada):
    socio_id: int = Field(..., gt=0)
    ejemplar_id: int = Field(..., gt=0)
    sede_origen_id: int = Field(..., gt=0)
    sede_destino_id: int = Field(..., gt=0)
    plazo_dias: int = Field(default=14, gt=0)


class DevolucionPrestamoRequest(ModeloEntrada):
    condicion: str = Field(default="BUENO", min_length=1)


class RemitoAvanzarRequest(ModeloEntrada):
    estado: str = Field(..., min_length=1)
    detalle: str = Field(default="")
