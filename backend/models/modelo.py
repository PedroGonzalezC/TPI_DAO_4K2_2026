"""Entidades y patrones de diseño del dominio."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


CONDICIONES_DEVOLUCION = ("BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO")
CONDICIONES_BAJA = ("DESTRUIDO", "EXTRAVIADO")
ESTADOS_ENTREGA = {"LOCAL": "SOLICITADO", "INTERBIBLIOTECARIO": "LISTO"}


class ReglaNegocio(ValueError):
    """Una operación incumple una regla del dominio."""


@dataclass(frozen=True)
class Sede:
    id: int
    nombre: str
    direccion: str
    contacto: str
    horarios: str
    activa: bool

    def verificar_activa(self):
        if not self.activa:
            raise ReglaNegocio(f"La sede {self.id} está dada de baja")


@dataclass(frozen=True)
class Socio:
    id: int
    documento: str
    nombre: str
    email: str
    habilitado: bool

    def verificar_habilitado(self):
        if not self.habilitado:
            raise ReglaNegocio(f"El socio {self.id} está inhabilitado")


@dataclass(frozen=True)
class Ejemplar:
    id: int
    codigo: str
    libro_id: int
    sede_pertenencia_id: int
    sede_actual_id: int
    estado: str

    def verificar_origen(self, sede_id):
        if self.sede_pertenencia_id != sede_id or self.sede_actual_id != sede_id:
            raise ReglaNegocio("El ejemplar no pertenece o no se encuentra en la sede de origen")


@dataclass(frozen=True)
class Libro:
    id: int
    isbn: str
    titulo: str
    autor: str
    anio: int | None


@dataclass(frozen=True)
class Reserva:
    id: int
    socio_id: int
    libro_id: int
    sede_id: int
    ejemplar_id: int | None
    estado: str
    creada_en: str

    def verificar_cancelable(self):
        if self.estado not in ('EN_ESPERA', 'ASIGNADA'):
            raise ReglaNegocio('La reserva ya está cerrada')


@dataclass(frozen=True)
class Prestamo:
    socio_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int

    @property
    def tipo(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class PrestamoLocal(Prestamo):
    @property
    def tipo(self) -> str:
        return "LOCAL"


@dataclass(frozen=True)
class PrestamoInterbibliotecario(Prestamo):
    @property
    def tipo(self) -> str:
        return "INTERBIBLIOTECARIO"


class FabricaPrestamos:
    """Factory: el cliente no necesita decidir qué clase de préstamo instanciar."""

    @staticmethod
    def crear(socio_id: int, ejemplar_id: int, origen: int, destino: int) -> Prestamo:
        clase = PrestamoLocal if origen == destino else PrestamoInterbibliotecario
        return clase(socio_id, ejemplar_id, origen, destino)


class ObservadorRemito(Protocol):
    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None: ...


@dataclass
class Remito:
    """Emisor del patrón Observer y responsable de sus transiciones válidas."""

    id: int
    estado: str
    observadores: list[ObservadorRemito] = field(default_factory=list)

    TRANSICIONES = {
        "CREADO": "EMPAQUETADO",
        "EMPAQUETADO": "DESPACHADO",
        "DESPACHADO": "RECIBIDO",
    }

    def suscribir(self, observador: ObservadorRemito) -> None:
        self.observadores.append(observador)

    def avanzar(self, nuevo_estado: str, fecha: datetime, detalle: str = "") -> None:
        if self.TRANSICIONES.get(self.estado) != nuevo_estado:
            raise ReglaNegocio(f"Transición de remito inválida: {self.estado} -> {nuevo_estado}")
        self.estado = nuevo_estado
        for observador in self.observadores:
            observador.actualizar(self.id, nuevo_estado, fecha.isoformat(timespec="seconds"), detalle)
