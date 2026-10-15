"""Casos de uso de sedes y socios."""

import sqlite3

from ..dominio.personas.sede import Sede
from ..dominio.personas.socio import Socio
from ..dominio.regla_negocio import ReglaNegocio
from ..persistencia.sede_dao import SedeDAO
from ..persistencia.socio_dao import SocioDAO


class ServicioPersonas:
    @staticmethod
    def _texto(valor, nombre: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocio(f"{nombre} es obligatorio")
        return valor.strip()

    @staticmethod
    def _unico(operacion, mensaje):
        try:
            return operacion()
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    def crear_sede(self, con, nombre, direccion, contacto, horarios) -> int:
        sede = Sede(None, *(self._texto(valor, etiqueta) for valor, etiqueta in zip(
            (nombre, direccion, contacto, horarios), ("Nombre", "Dirección", "Contacto", "Horarios")
        )))
        return self._unico(lambda: SedeDAO.crear(con, sede), "Ya existe una sede con ese nombre")

    def actualizar_sede(self, con, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None) -> None:
        if activa is not None and activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        sede = SedeDAO.obtener(con, sede_id)
        sede.direccion = self._texto(direccion, "Dirección") if direccion is not None else sede.direccion
        sede.contacto = self._texto(contacto, "Contacto") if contacto is not None else sede.contacto
        sede.horarios = self._texto(horarios, "Horarios") if horarios is not None else sede.horarios
        sede.activa = bool(activa) if activa is not None else sede.activa
        SedeDAO.guardar(con, sede)

    def crear_socio(self, con, documento, nombre, email) -> int:
        socio = Socio(None, self._texto(documento, "Documento"), self._texto(nombre, "Nombre"),
                      self._texto(email, "Email"))
        return self._unico(lambda: SocioDAO.crear(con, socio), "Ya existe un socio con ese documento")

    def actualizar_socio(self, con, socio_id, *, nombre=None, email=None, habilitado=None) -> None:
        if habilitado is not None and habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        socio = SocioDAO.obtener(con, socio_id)
        socio.nombre = self._texto(nombre, "Nombre") if nombre is not None else socio.nombre
        socio.email = self._texto(email, "Email") if email is not None else socio.email
        socio.habilitado = bool(habilitado) if habilitado is not None else socio.habilitado
        SocioDAO.guardar(con, socio)
