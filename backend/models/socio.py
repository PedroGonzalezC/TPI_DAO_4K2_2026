"""Entidad de dominio Socio."""

from dataclasses import dataclass

from .excepciones import ReglaNegocio, validar_texto_obligatorio


@dataclass
class Socio:
    """Representa un socio registrado en la red de bibliotecas."""

    documento: str
    nombre: str
    email: str
    habilitado: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.documento = validar_texto_obligatorio(self.documento, "Documento")
        self.nombre = validar_texto_obligatorio(self.nombre, "Nombre")
        self.email = validar_texto_obligatorio(self.email, "Email")
        if self.habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        self.habilitado = bool(self.habilitado)

    def asegurar_habilitado(self) -> None:
        if not self.habilitado:
            raise ReglaNegocio(f"El socio {self.id} está inhabilitado")

    def actualizar(
        self,
        *,
        nombre: str | None = None,
        email: str | None = None,
        habilitado: bool | int | None = None,
    ) -> None:
        if habilitado is not None and habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        if nombre is not None:
            self.nombre = validar_texto_obligatorio(nombre, "Nombre")
        if email is not None:
            self.email = validar_texto_obligatorio(email, "Email")
        if habilitado is not None:
            self.habilitado = bool(habilitado)
