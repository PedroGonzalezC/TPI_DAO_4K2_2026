"""Casos de uso y reglas de negocio de la biblioteca."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from ..database.configuracion import CONFIG
from ..database.datos import BaseDatos, TABLAS
from ..daos.dao import DAOS, EjemplarDAO, ReservaDAO, PrestamoDAO, RemitoDAO, EventoRemitoDAO, ReporteDAO
from ..models.modelo import (
    CONDICIONES_BAJA, CONDICIONES_DEVOLUCION, ESTADOS_ENTREGA,
    Ejemplar, FabricaPrestamos, ReglaNegocio, Remito, Reserva, Sede, Socio,
)
from ..daos.reportes import REPORTES


class Biblioteca:
    PLAZO_DIAS = CONFIG["plazo_dias"]
    MULTA_DIARIA_CENTAVOS = CONFIG["multa_diaria_centavos"]

    def __init__(self, ruta_db: str | Path = CONFIG["base_datos"]):
        self.db = BaseDatos(ruta_db)

    @staticmethod
    def _ahora(fecha=None) -> datetime:
        if fecha is None:
            return datetime.now().replace(microsecond=0)
        if isinstance(fecha, date) and not isinstance(fecha, datetime):
            return datetime.combine(fecha, datetime.min.time())
        if not isinstance(fecha, datetime):
            raise ReglaNegocio("La fecha debe ser date o datetime")
        return fecha.replace(microsecond=0)

    @staticmethod
    def _texto(valor, nombre: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocio(f"{nombre} es obligatorio")
        return valor.strip()

    @staticmethod
    def _fila(con, tabla: str, id_: int):
        if tabla not in TABLAS:
            raise ValueError("Tabla inválida")
        fila = DAOS[tabla](con).obtener(id_)
        if fila is None:
            raise ReglaNegocio(f"No existe {TABLAS[tabla]} con id {id_}")
        return fila

    @classmethod
    def _sede_activa(cls, con, id_: int):
        sede = cls._fila(con, "sedes", id_)
        Sede(**dict(sede)).verificar_activa()
        return sede

    @classmethod
    def _socio_habilitado(cls, con, id_: int):
        socio = cls._fila(con, "socios", id_)
        Socio(**dict(socio)).verificar_habilitado()
        return socio

    @staticmethod
    def _ejecutar_unico(dao, valores, mensaje):
        try:
            return dao.insertar(**valores)
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    def _actualizar_maestro(self, tabla, id_, **cambios):
        """Solo recibe nombres de campos escritos en los métodos de esta clase."""
        etiquetas = {"direccion": "Dirección", "contacto": "Contacto", "horarios": "Horarios",
                     "nombre": "Nombre", "email": "Email", "titulo": "Título", "autor": "Autor"}
        with self.db.conexion() as con:
            self._fila(con, tabla, id_)
            valores = {campo: self._texto(valor, etiquetas[campo]) if campo in etiquetas else valor
                       for campo, valor in cambios.items() if valor is not None}
            if valores:
                DAOS[tabla](con).actualizar(id_, **valores)

    @staticmethod
    def _validar_anio(anio):
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")

    # Altas, modificaciones y bajas lógicas de datos maestros.
    def crear_sede(self, nombre, direccion, contacto, horarios):
        valores = tuple(self._texto(v, n) for v, n in zip(
            (nombre, direccion, contacto, horarios),
            ("Nombre", "Dirección", "Contacto", "Horarios"),
        ))
        with self.db.conexion() as con:
            return self._ejecutar_unico(DAOS["sedes"](con), dict(zip(("nombre", "direccion", "contacto", "horarios"), valores)), "Ya existe una sede con ese nombre")

    def actualizar_sede(self, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None):
        if activa is not None and activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        self._actualizar_maestro("sedes", sede_id, direccion=direccion, contacto=contacto,
                                 horarios=horarios, activa=int(activa) if activa is not None else None)

    def crear_socio(self, documento, nombre, email):
        valores = (self._texto(documento, "Documento"), self._texto(nombre, "Nombre"),
                   self._texto(email, "Email"))
        with self.db.conexion() as con:
            return self._ejecutar_unico(DAOS["socios"](con), dict(zip(("documento", "nombre", "email"), valores)), "Ya existe un socio con ese documento")

    def actualizar_socio(self, socio_id, *, nombre=None, email=None, habilitado=None):
        if habilitado is not None and habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        self._actualizar_maestro("socios", socio_id, nombre=nombre, email=email,
                                 habilitado=int(habilitado) if habilitado is not None else None)

    def crear_libro(self, isbn, titulo, autor, anio=None):
        self._validar_anio(anio)
        valores = (self._texto(isbn, "ISBN"), self._texto(titulo, "Título"),
                   self._texto(autor, "Autor"), anio)
        with self.db.conexion() as con:
            return self._ejecutar_unico(DAOS["libros"](con), dict(zip(("isbn", "titulo", "autor", "anio"), valores)), "Ya existe un libro con ese ISBN")

    def actualizar_libro(self, libro_id, *, titulo=None, autor=None, anio=None):
        self._validar_anio(anio)
        self._actualizar_maestro("libros", libro_id, titulo=titulo, autor=autor, anio=anio)

    def crear_ejemplar(self, codigo, libro_id, sede_id):
        with self.db.conexion() as con:
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            return self._ejecutar_unico(EjemplarDAO(con), {"codigo": self._texto(codigo, "Código"), "libro_id": libro_id,
                "sede_pertenencia_id": sede_id, "sede_actual_id": sede_id}, "Ya existe un ejemplar con ese código")

    def listar(self, tabla: str):
        if tabla not in TABLAS:
            raise ReglaNegocio("Listado desconocido")
        with self.db.conexion() as con:
            return DAOS[tabla](con).listar()

    def disponibilidad(self, sede_id=None):
        with self.db.conexion() as con:
            if sede_id is not None:
                self._fila(con, "sedes", sede_id)
            return EjemplarDAO(con).disponibilidad(sede_id)

    # Reserva en espera por libro y sede; la asignación respeta el orden de llegada.
    def reservar(self, socio_id, libro_id, sede_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            reserva_id = self._ejecutar_unico(ReservaDAO(con),
                {"socio_id": socio_id, "libro_id": libro_id, "sede_id": sede_id, "creada_en": ahora.isoformat()},
                "El socio ya tiene una reserva activa para ese libro y sede")
            disponible = EjemplarDAO(con).disponible(libro_id, sede_id)
            if disponible:
                self._asignar_reserva(con, disponible["id"])
            return reserva_id

    def _asignar_reserva(self, con, ejemplar_id):
        ejemplar = self._fila(con, "ejemplares", ejemplar_id)
        if ejemplar["estado"] != "DISPONIBLE":
            return
        candidatas = ReservaDAO(con).en_espera(ejemplar["libro_id"], ejemplar["sede_actual_id"])
        espera = next((r for r in candidatas if r["habilitado"] and r["activa"]), None)
        if espera:
            ReservaDAO(con).actualizar(espera["id"], estado="ASIGNADA", ejemplar_id=ejemplar_id)
            EjemplarDAO(con).actualizar(ejemplar_id, estado="RESERVADO")

    def cancelar_reserva(self, reserva_id):
        with self.db.conexion() as con:
            reserva = self._fila(con, "reservas", reserva_id)
            Reserva(**dict(reserva)).verificar_cancelable()
            ReservaDAO(con).actualizar(reserva_id, estado="CANCELADA")
            if reserva["ejemplar_id"]:
                EjemplarDAO(con).actualizar(reserva["ejemplar_id"], estado="DISPONIBLE")
                self._asignar_reserva(con, reserva["ejemplar_id"])

    def solicitar_prestamo(self, socio_id, ejemplar_id, sede_origen_id, sede_destino_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._sede_activa(con, sede_origen_id)
            self._sede_activa(con, sede_destino_id)
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            Ejemplar(**dict(ejemplar)).verificar_origen(sede_origen_id)
            if ejemplar["estado"] == "RESERVADO":
                reserva = ReservaDAO(con).asignada(ejemplar_id)
                if reserva is None or reserva["socio_id"] != socio_id or reserva["sede_id"] != sede_destino_id:
                    raise ReglaNegocio("El ejemplar está reservado para otro socio o sede de retiro")
                ReservaDAO(con).actualizar(reserva["id"], estado="CUMPLIDA")
            elif ejemplar["estado"] != "DISPONIBLE":
                raise ReglaNegocio("El ejemplar no está disponible")
            prestamo = FabricaPrestamos.crear(socio_id, ejemplar_id, sede_origen_id, sede_destino_id)
            prestamo_id = PrestamoDAO(con).insertar(socio_id=socio_id, ejemplar_id=ejemplar_id,
                sede_origen_id=sede_origen_id, sede_destino_id=sede_destino_id, tipo=prestamo.tipo,
                estado="SOLICITADO", solicitado_en=ahora.isoformat())
            EjemplarDAO(con).actualizar(ejemplar_id, estado="APARTADO")
            if prestamo.tipo == "INTERBIBLIOTECARIO":
                self._crear_remito(con, prestamo_id, ejemplar_id, "IDA", sede_origen_id,
                                   sede_destino_id, ahora)
            return prestamo_id

    @staticmethod
    def _crear_remito(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha):
        id_ = RemitoDAO(con).insertar(prestamo_id=prestamo_id, ejemplar_id=ejemplar_id, tipo=tipo,
            origen_id=origen, destino_id=destino, estado="CREADO", creado_en=fecha.isoformat())
        EventoRemitoDAO(con).actualizar(id_, "CREADO", fecha.isoformat(), "Remito generado")
        return id_

    def avanzar_remito(self, remito_id, nuevo_estado, *, fecha=None, detalle=""):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            fila = self._fila(con, "remitos", remito_id)
            ultima = EventoRemitoDAO(con).ultimo(remito_id)["fecha"]
            if ahora < datetime.fromisoformat(ultima):
                raise ReglaNegocio("El evento no puede preceder al estado anterior del remito")
            if nuevo_estado in {"EMPAQUETADO", "DESPACHADO"}:
                self._sede_activa(con, fila["origen_id"])
                self._sede_activa(con, fila["destino_id"])
            remito = Remito(remito_id, fila["estado"])
            remito.suscribir(EventoRemitoDAO(con))
            remito.avanzar(nuevo_estado, ahora, detalle)
            RemitoDAO(con).actualizar(remito_id, estado=nuevo_estado,
                recibido_en=ahora.isoformat() if nuevo_estado == "RECIBIDO" else fila["recibido_en"])
            if nuevo_estado == "DESPACHADO":
                EjemplarDAO(con).actualizar(fila["ejemplar_id"], estado="EN_TRANSITO")
                if fila["tipo"] == "IDA":
                    PrestamoDAO(con).actualizar(fila["prestamo_id"], estado="EN_TRANSITO")
            elif nuevo_estado == "RECIBIDO":
                EjemplarDAO(con).actualizar(fila["ejemplar_id"], sede_actual_id=fila["destino_id"])
                if fila["tipo"] == "IDA":
                    EjemplarDAO(con).actualizar(fila["ejemplar_id"], estado="APARTADO")
                    PrestamoDAO(con).actualizar(fila["prestamo_id"], estado="LISTO")
                else:
                    prestamo = self._fila(con, "prestamos", fila["prestamo_id"])
                    estado = "DISPONIBLE" if prestamo["condicion_devolucion"] == "BUENO" else "EN_REVISION"
                    EjemplarDAO(con).actualizar(fila["ejemplar_id"], estado=estado)
                    if estado == "DISPONIBLE":
                        self._asignar_reserva(con, fila["ejemplar_id"])

    def entregar_prestamo(self, prestamo_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            requerido = ESTADOS_ENTREGA[prestamo["tipo"]]
            if prestamo["estado"] != requerido:
                raise ReglaNegocio(f"El préstamo debe estar en estado {requerido} para entregarlo")
            fecha_minima = prestamo["solicitado_en"]
            if prestamo["tipo"] == "INTERBIBLIOTECARIO":
                fecha_minima = RemitoDAO(con).ida(prestamo_id)["recibido_en"]
            if ahora < datetime.fromisoformat(fecha_minima):
                raise ReglaNegocio("La entrega no puede preceder a la solicitud o recepción")
            self._socio_habilitado(con, prestamo["socio_id"])
            self._sede_activa(con, prestamo["sede_destino_id"])
            vence = (ahora + timedelta(days=self.PLAZO_DIAS)).date().isoformat()
            PrestamoDAO(con).actualizar(prestamo_id, estado="ACTIVO", entregado_en=ahora.isoformat(), vence_en=vence)
            EjemplarDAO(con).actualizar(prestamo["ejemplar_id"], estado="PRESTADO")
            return vence

    def devolver_prestamo(self, prestamo_id, condicion="BUENO", *, fecha=None):
        ahora = self._ahora(fecha)
        condicion = self._texto(condicion, "Condición").upper()
        if condicion not in CONDICIONES_DEVOLUCION:
            raise ReglaNegocio("Condición de devolución inválida")
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            if prestamo["estado"] != "ACTIVO":
                raise ReglaNegocio("Solo se puede devolver un préstamo activo")
            if ahora < datetime.fromisoformat(prestamo["entregado_en"]):
                raise ReglaNegocio("La devolución no puede preceder a la entrega")
            atraso = max(0, (ahora.date() - date.fromisoformat(prestamo["vence_en"])).days)
            multa = atraso * self.MULTA_DIARIA_CENTAVOS
            PrestamoDAO(con).actualizar(prestamo_id, estado="DEVUELTO", devuelto_en=ahora.isoformat(),
                condicion_devolucion=condicion, multa_centavos=multa)
            if condicion in CONDICIONES_BAJA:
                estado = "BAJA"
            elif prestamo["tipo"] == "INTERBIBLIOTECARIO":
                estado = "POR_RETORNAR"
                self._crear_remito(con, prestamo_id, prestamo["ejemplar_id"], "REGRESO",
                                   prestamo["sede_destino_id"], prestamo["sede_origen_id"], ahora)
            else:
                estado = "DISPONIBLE" if condicion == "BUENO" else "EN_REVISION"
            EjemplarDAO(con).actualizar(prestamo["ejemplar_id"], estado=estado)
            if estado == "DISPONIBLE":
                self._asignar_reserva(con, prestamo["ejemplar_id"])
            return multa

    def cerrar_revision(self, ejemplar_id, apto: bool):
        with self.db.conexion() as con:
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            if ejemplar["estado"] != "EN_REVISION":
                raise ReglaNegocio("El ejemplar no está en revisión")
            estado = "DISPONIBLE" if apto else "BAJA"
            EjemplarDAO(con).actualizar(ejemplar_id, estado=estado)
            if apto:
                self._asignar_reserva(con, ejemplar_id)

    def historial_remito(self, remito_id):
        with self.db.conexion() as con:
            self._fila(con, "remitos", remito_id)
            return EventoRemitoDAO(con).listar(remito_id)

    # Informes SQL. Todos devuelven filas serializables y pueden consumirse por CLI.
    def reportes(self, nombre: str, *, fecha=None):
        hoy = self._ahora(fecha).date().isoformat()
        if nombre not in REPORTES:
            raise ReglaNegocio(f"Reporte desconocido: {nombre}")
        parametros = {"hoy": hoy, "multa": self.MULTA_DIARIA_CENTAVOS}
        with self.db.conexion() as con:
            return ReporteDAO(con).consultar(nombre, parametros)
