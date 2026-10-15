"""Sede de la red de bibliotecas."""

from dataclasses import dataclass

from ..regla_negocio import ReglaNegocio


@dataclass
class Sede:
    id: int | None
    nombre: str
    direccion: str
    contacto: str
    horarios: str
    activa: bool = True

    def exigir_activa(self) -> None:
        if not self.activa:
            raise ReglaNegocio(f"La sede {self.id} está dada de baja")
