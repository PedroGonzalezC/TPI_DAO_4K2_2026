"""Socio de la biblioteca."""

from dataclasses import dataclass

from ..regla_negocio import ReglaNegocio


@dataclass
class Socio:
    id: int | None
    documento: str
    nombre: str
    email: str
    habilitado: bool = True

    def exigir_habilitado(self) -> None:
        if not self.habilitado:
            raise ReglaNegocio(f"El socio {self.id} está inhabilitado")
