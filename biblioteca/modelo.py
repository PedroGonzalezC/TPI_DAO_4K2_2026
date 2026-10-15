"""Entidades y patrones de diseño del dominio."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class ReglaNegocio(ValueError):
    """Una operación incumple una regla del dominio."""


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
