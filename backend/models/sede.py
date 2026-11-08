"""Entidad de dominio Sede."""

from dataclasses import dataclass

from .excepciones import ReglaNegocio, validar_texto_obligatorio


@dataclass
class Sede:
    """Representa una sede de la red de bibliotecas."""

    nombre: str
    direccion: str
    contacto: str
    horarios: str
    activa: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.nombre = validar_texto_obligatorio(self.nombre, "Nombre")
        self.direccion = validar_texto_obligatorio(self.direccion, "Dirección")
        self.contacto = validar_texto_obligatorio(self.contacto, "Contacto")
        self.horarios = validar_texto_obligatorio(self.horarios, "Horarios")
        if self.activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        self.activa = bool(self.activa)

    def asegurar_activa(self) -> None:
        if not self.activa:
            raise ReglaNegocio(f"La sede {self.id} está dada de baja")

    def actualizar(
        self,
        *,
        direccion: str | None = None,
        contacto: str | None = None,
        horarios: str | None = None,
        activa: bool | int | None = None,
    ) -> None:
        if activa is not None and activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        if direccion is not None:
            self.direccion = validar_texto_obligatorio(direccion, "Dirección")
        if contacto is not None:
            self.contacto = validar_texto_obligatorio(contacto, "Contacto")
        if horarios is not None:
            self.horarios = validar_texto_obligatorio(horarios, "Horarios")
        if activa is not None:
            self.activa = bool(activa)
