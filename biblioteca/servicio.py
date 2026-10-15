"""Casos de uso y reglas de negocio de la biblioteca."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from .datos import BaseDatos, HistorialRemito
from .modelo import FabricaPrestamos, ReglaNegocio, Remito


class Biblioteca:
    PLAZO_DIAS = 14
    MULTA_DIARIA_CENTAVOS = 10000  # $100 por día de atraso; decisión configurable.

    def __init__(self, ruta_db: str | Path = "biblioteca.db"):
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
        if tabla not in {"sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos"}:
            raise ValueError("Tabla inválida")
        fila = con.execute(f"SELECT * FROM {tabla} WHERE id=?", (id_,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe {tabla[:-1]} con id {id_}")
        return fila

    @classmethod
    def _sede_activa(cls, con, id_: int):
        sede = cls._fila(con, "sedes", id_)
        if not sede["activa"]:
            raise ReglaNegocio(f"La sede {id_} está dada de baja")
        return sede

    @classmethod
    def _socio_habilitado(cls, con, id_: int):
        socio = cls._fila(con, "socios", id_)
        if not socio["habilitado"]:
            raise ReglaNegocio(f"El socio {id_} está inhabilitado")
        return socio

    @staticmethod
    def _ejecutar_unico(con, sql, parametros, mensaje):
        try:
            return con.execute(sql, parametros).lastrowid
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    # Altas, modificaciones y bajas lógicas de datos maestros.
    def crear_sede(self, nombre, direccion, contacto, horarios):
        valores = tuple(self._texto(v, n) for v, n in zip(
            (nombre, direccion, contacto, horarios),
            ("Nombre", "Dirección", "Contacto", "Horarios"),
        ))
        with self.db.conexion() as con:
            return self._ejecutar_unico(con,
                "INSERT INTO sedes(nombre,direccion,contacto,horarios) VALUES(?,?,?,?)",
                valores, "Ya existe una sede con ese nombre")

    def actualizar_sede(self, sede_id, *, direccion=None, contacto=None, horarios=None, activa=None):
        if activa is not None and activa not in (True, False, 0, 1):
            raise ReglaNegocio("El estado de la sede debe ser activo o baja")
        with self.db.conexion() as con:
            sede = self._fila(con, "sedes", sede_id)
            con.execute("UPDATE sedes SET direccion=?, contacto=?, horarios=?, activa=? WHERE id=?", (
                self._texto(direccion, "Dirección") if direccion is not None else sede["direccion"],
                self._texto(contacto, "Contacto") if contacto is not None else sede["contacto"],
                self._texto(horarios, "Horarios") if horarios is not None else sede["horarios"],
                int(activa) if activa is not None else sede["activa"], sede_id))

    def crear_socio(self, documento, nombre, email):
        valores = (self._texto(documento, "Documento"), self._texto(nombre, "Nombre"),
                   self._texto(email, "Email"))
        with self.db.conexion() as con:
            return self._ejecutar_unico(con,
                "INSERT INTO socios(documento,nombre,email) VALUES(?,?,?)", valores,
                "Ya existe un socio con ese documento")

    def actualizar_socio(self, socio_id, *, nombre=None, email=None, habilitado=None):
        if habilitado is not None and habilitado not in (True, False, 0, 1):
            raise ReglaNegocio("La habilitación del socio debe ser sí o no")
        with self.db.conexion() as con:
            socio = self._fila(con, "socios", socio_id)
            con.execute("UPDATE socios SET nombre=?, email=?, habilitado=? WHERE id=?", (
                self._texto(nombre, "Nombre") if nombre is not None else socio["nombre"],
                self._texto(email, "Email") if email is not None else socio["email"],
                int(habilitado) if habilitado is not None else socio["habilitado"], socio_id))

    def crear_libro(self, isbn, titulo, autor, anio=None):
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        valores = (self._texto(isbn, "ISBN"), self._texto(titulo, "Título"),
                   self._texto(autor, "Autor"), anio)
        with self.db.conexion() as con:
            return self._ejecutar_unico(con,
                "INSERT INTO libros(isbn,titulo,autor,anio) VALUES(?,?,?,?)", valores,
                "Ya existe un libro con ese ISBN")

    def actualizar_libro(self, libro_id, *, titulo=None, autor=None, anio=None):
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        with self.db.conexion() as con:
            libro = self._fila(con, "libros", libro_id)
            con.execute("UPDATE libros SET titulo=?, autor=?, anio=? WHERE id=?", (
                self._texto(titulo, "Título") if titulo is not None else libro["titulo"],
                self._texto(autor, "Autor") if autor is not None else libro["autor"],
                anio if anio is not None else libro["anio"], libro_id))

    def crear_ejemplar(self, codigo, libro_id, sede_id):
        with self.db.conexion() as con:
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            return self._ejecutar_unico(con,
                "INSERT INTO ejemplares(codigo,libro_id,sede_pertenencia_id,sede_actual_id) VALUES(?,?,?,?)",
                (self._texto(codigo, "Código"), libro_id, sede_id, sede_id),
                "Ya existe un ejemplar con ese código")

    def listar(self, tabla: str):
        if tabla not in {"sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos"}:
            raise ReglaNegocio("Listado desconocido")
        with self.db.conexion() as con:
            return [dict(x) for x in con.execute(f"SELECT * FROM {tabla} ORDER BY id")]

    def disponibilidad(self, sede_id=None):
        with self.db.conexion() as con:
            if sede_id is not None:
                self._fila(con, "sedes", sede_id)
            return [dict(x) for x in con.execute("""
                SELECT s.id sede_id, s.nombre sede, l.id libro_id, l.isbn, l.titulo,
                       COUNT(e.id) ejemplares_totales,
                       SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles
                FROM sedes s JOIN ejemplares e ON e.sede_actual_id=s.id
                JOIN libros l ON l.id=e.libro_id
                WHERE (? IS NULL OR s.id=?)
                GROUP BY s.id,l.id ORDER BY s.nombre,l.titulo
            """, (sede_id, sede_id))]

    # Reserva en espera por libro y sede; la asignación respeta el orden de llegada.
    def reservar(self, socio_id, libro_id, sede_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._fila(con, "libros", libro_id)
            self._sede_activa(con, sede_id)
            reserva_id = self._ejecutar_unico(con,
                "INSERT INTO reservas(socio_id,libro_id,sede_id,creada_en) VALUES(?,?,?,?)",
                (socio_id, libro_id, sede_id, ahora.isoformat()),
                "El socio ya tiene una reserva activa para ese libro y sede")
            disponible = con.execute("""
                SELECT id FROM ejemplares WHERE libro_id=? AND sede_actual_id=?
                AND estado='DISPONIBLE' ORDER BY id LIMIT 1
            """, (libro_id, sede_id)).fetchone()
            if disponible:
                self._asignar_reserva(con, disponible["id"])
            return reserva_id

    def _asignar_reserva(self, con, ejemplar_id):
        ejemplar = self._fila(con, "ejemplares", ejemplar_id)
        if ejemplar["estado"] != "DISPONIBLE":
            return
        espera = con.execute("""
            SELECT r.id FROM reservas r JOIN socios so ON so.id=r.socio_id
            JOIN sedes s ON s.id=r.sede_id WHERE r.libro_id=? AND r.sede_id=?
            AND r.estado='EN_ESPERA' AND so.habilitado=1 AND s.activa=1
            ORDER BY r.creada_en,r.id LIMIT 1
        """, (ejemplar["libro_id"], ejemplar["sede_actual_id"])).fetchone()
        if espera:
            con.execute("UPDATE reservas SET estado='ASIGNADA', ejemplar_id=? WHERE id=?",
                        (ejemplar_id, espera["id"]))
            con.execute("UPDATE ejemplares SET estado='RESERVADO' WHERE id=?", (ejemplar_id,))

    def cancelar_reserva(self, reserva_id):
        with self.db.conexion() as con:
            reserva = self._fila(con, "reservas", reserva_id)
            if reserva["estado"] not in ("EN_ESPERA", "ASIGNADA"):
                raise ReglaNegocio("La reserva ya está cerrada")
            con.execute("UPDATE reservas SET estado='CANCELADA' WHERE id=?", (reserva_id,))
            if reserva["ejemplar_id"]:
                con.execute("UPDATE ejemplares SET estado='DISPONIBLE' WHERE id=?",
                            (reserva["ejemplar_id"],))
                self._asignar_reserva(con, reserva["ejemplar_id"])

    def solicitar_prestamo(self, socio_id, ejemplar_id, sede_origen_id, sede_destino_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            self._socio_habilitado(con, socio_id)
            self._sede_activa(con, sede_origen_id)
            self._sede_activa(con, sede_destino_id)
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            if ejemplar["sede_pertenencia_id"] != sede_origen_id or ejemplar["sede_actual_id"] != sede_origen_id:
                raise ReglaNegocio("El ejemplar no pertenece o no se encuentra en la sede de origen")
            if ejemplar["estado"] == "RESERVADO":
                reserva = con.execute("""
                    SELECT id, socio_id, sede_id FROM reservas WHERE ejemplar_id=? AND estado='ASIGNADA'
                """, (ejemplar_id,)).fetchone()
                if reserva is None or reserva["socio_id"] != socio_id or reserva["sede_id"] != sede_destino_id:
                    raise ReglaNegocio("El ejemplar está reservado para otro socio o sede de retiro")
                con.execute("UPDATE reservas SET estado='CUMPLIDA' WHERE id=?", (reserva["id"],))
            elif ejemplar["estado"] != "DISPONIBLE":
                raise ReglaNegocio("El ejemplar no está disponible")
            prestamo = FabricaPrestamos.crear(socio_id, ejemplar_id, sede_origen_id, sede_destino_id)
            prestamo_id = con.execute("""
                INSERT INTO prestamos(socio_id,ejemplar_id,sede_origen_id,sede_destino_id,tipo,estado,solicitado_en)
                VALUES(?,?,?,?,?,'SOLICITADO',?)
            """, (socio_id, ejemplar_id, sede_origen_id, sede_destino_id,
                  prestamo.tipo, ahora.isoformat())).lastrowid
            con.execute("UPDATE ejemplares SET estado='APARTADO' WHERE id=?", (ejemplar_id,))
            if prestamo.tipo == "INTERBIBLIOTECARIO":
                self._crear_remito(con, prestamo_id, ejemplar_id, "IDA", sede_origen_id,
                                   sede_destino_id, ahora)
            return prestamo_id

    @staticmethod
    def _crear_remito(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha):
        id_ = con.execute("""
            INSERT INTO remitos(prestamo_id,ejemplar_id,tipo,origen_id,destino_id,estado,creado_en)
            VALUES(?,?,?,?,?,'CREADO',?)
        """, (prestamo_id, ejemplar_id, tipo, origen, destino, fecha.isoformat())).lastrowid
        HistorialRemito(con).actualizar(id_, "CREADO", fecha.isoformat(), "Remito generado")
        return id_

    def avanzar_remito(self, remito_id, nuevo_estado, *, fecha=None, detalle=""):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            fila = self._fila(con, "remitos", remito_id)
            ultima = con.execute("SELECT fecha FROM historial_remitos WHERE remito_id=? ORDER BY id DESC LIMIT 1",
                                 (remito_id,)).fetchone()["fecha"]
            if ahora < datetime.fromisoformat(ultima):
                raise ReglaNegocio("El evento no puede preceder al estado anterior del remito")
            if nuevo_estado in {"EMPAQUETADO", "DESPACHADO"}:
                self._sede_activa(con, fila["origen_id"])
                self._sede_activa(con, fila["destino_id"])
            remito = Remito(remito_id, fila["estado"])
            remito.suscribir(HistorialRemito(con))
            remito.avanzar(nuevo_estado, ahora, detalle)
            con.execute("UPDATE remitos SET estado=?, recibido_en=? WHERE id=?", (
                nuevo_estado, ahora.isoformat() if nuevo_estado == "RECIBIDO" else fila["recibido_en"],
                remito_id))
            if nuevo_estado == "DESPACHADO":
                con.execute("UPDATE ejemplares SET estado='EN_TRANSITO' WHERE id=?", (fila["ejemplar_id"],))
                if fila["tipo"] == "IDA":
                    con.execute("UPDATE prestamos SET estado='EN_TRANSITO' WHERE id=?", (fila["prestamo_id"],))
            elif nuevo_estado == "RECIBIDO":
                con.execute("UPDATE ejemplares SET sede_actual_id=? WHERE id=?",
                            (fila["destino_id"], fila["ejemplar_id"]))
                if fila["tipo"] == "IDA":
                    con.execute("UPDATE ejemplares SET estado='APARTADO' WHERE id=?", (fila["ejemplar_id"],))
                    con.execute("UPDATE prestamos SET estado='LISTO' WHERE id=?", (fila["prestamo_id"],))
                else:
                    prestamo = self._fila(con, "prestamos", fila["prestamo_id"])
                    estado = "DISPONIBLE" if prestamo["condicion_devolucion"] == "BUENO" else "EN_REVISION"
                    con.execute("UPDATE ejemplares SET estado=? WHERE id=?", (estado, fila["ejemplar_id"]))
                    if estado == "DISPONIBLE":
                        self._asignar_reserva(con, fila["ejemplar_id"])

    def entregar_prestamo(self, prestamo_id, *, fecha=None):
        ahora = self._ahora(fecha)
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            requerido = "SOLICITADO" if prestamo["tipo"] == "LOCAL" else "LISTO"
            if prestamo["estado"] != requerido:
                raise ReglaNegocio(f"El préstamo debe estar en estado {requerido} para entregarlo")
            fecha_minima = prestamo["solicitado_en"]
            if prestamo["tipo"] == "INTERBIBLIOTECARIO":
                fecha_minima = con.execute("""
                    SELECT recibido_en FROM remitos WHERE prestamo_id=? AND tipo='IDA'
                """, (prestamo_id,)).fetchone()["recibido_en"]
            if ahora < datetime.fromisoformat(fecha_minima):
                raise ReglaNegocio("La entrega no puede preceder a la solicitud o recepción")
            self._socio_habilitado(con, prestamo["socio_id"])
            self._sede_activa(con, prestamo["sede_destino_id"])
            vence = (ahora + timedelta(days=self.PLAZO_DIAS)).date().isoformat()
            con.execute("UPDATE prestamos SET estado='ACTIVO',entregado_en=?,vence_en=? WHERE id=?",
                        (ahora.isoformat(), vence, prestamo_id))
            con.execute("UPDATE ejemplares SET estado='PRESTADO' WHERE id=?", (prestamo["ejemplar_id"],))
            return vence

    def devolver_prestamo(self, prestamo_id, condicion="BUENO", *, fecha=None):
        ahora = self._ahora(fecha)
        condicion = self._texto(condicion, "Condición").upper()
        if condicion not in {"BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"}:
            raise ReglaNegocio("Condición de devolución inválida")
        with self.db.conexion() as con:
            prestamo = self._fila(con, "prestamos", prestamo_id)
            if prestamo["estado"] != "ACTIVO":
                raise ReglaNegocio("Solo se puede devolver un préstamo activo")
            if ahora < datetime.fromisoformat(prestamo["entregado_en"]):
                raise ReglaNegocio("La devolución no puede preceder a la entrega")
            atraso = max(0, (ahora.date() - date.fromisoformat(prestamo["vence_en"])).days)
            multa = atraso * self.MULTA_DIARIA_CENTAVOS
            con.execute("""
                UPDATE prestamos SET estado='DEVUELTO', devuelto_en=?, condicion_devolucion=?, multa_centavos=?
                WHERE id=?
            """, (ahora.isoformat(), condicion, multa, prestamo_id))
            if condicion in {"DESTRUIDO", "EXTRAVIADO"}:
                estado = "BAJA"
            elif prestamo["tipo"] == "INTERBIBLIOTECARIO":
                estado = "POR_RETORNAR"
                self._crear_remito(con, prestamo_id, prestamo["ejemplar_id"], "REGRESO",
                                   prestamo["sede_destino_id"], prestamo["sede_origen_id"], ahora)
            else:
                estado = "DISPONIBLE" if condicion == "BUENO" else "EN_REVISION"
            con.execute("UPDATE ejemplares SET estado=? WHERE id=?", (estado, prestamo["ejemplar_id"]))
            if estado == "DISPONIBLE":
                self._asignar_reserva(con, prestamo["ejemplar_id"])
            return multa

    def cerrar_revision(self, ejemplar_id, apto: bool):
        with self.db.conexion() as con:
            ejemplar = self._fila(con, "ejemplares", ejemplar_id)
            if ejemplar["estado"] != "EN_REVISION":
                raise ReglaNegocio("El ejemplar no está en revisión")
            estado = "DISPONIBLE" if apto else "BAJA"
            con.execute("UPDATE ejemplares SET estado=? WHERE id=?", (estado, ejemplar_id))
            if apto:
                self._asignar_reserva(con, ejemplar_id)

    def historial_remito(self, remito_id):
        with self.db.conexion() as con:
            self._fila(con, "remitos", remito_id)
            return [dict(x) for x in con.execute(
                "SELECT estado,fecha,detalle FROM historial_remitos WHERE remito_id=? ORDER BY id", (remito_id,))]

    # Informes SQL. Todos devuelven filas serializables y pueden consumirse por CLI.
    def reportes(self, nombre: str, *, fecha=None):
        hoy = self._ahora(fecha).date().isoformat()
        consultas = {
            "activos_transito": ("""
                SELECT p.id, l.titulo, e.codigo, so.nombre socio, p.tipo,
                       CASE WHEN r.id IS NOT NULL THEN 'RETORNO_EN_TRANSITO' ELSE p.estado END estado,
                       CASE WHEN r.id IS NOT NULL THEN d.nombre ELSE o.nombre END origen,
                       CASE WHEN r.id IS NOT NULL THEN o.nombre ELSE d.nombre END destino,
                       p.vence_en
                FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
                JOIN libros l ON l.id=e.libro_id JOIN socios so ON so.id=p.socio_id
                JOIN sedes o ON o.id=p.sede_origen_id JOIN sedes d ON d.id=p.sede_destino_id
                LEFT JOIN remitos r ON r.prestamo_id=p.id AND r.tipo='REGRESO' AND r.estado='DESPACHADO'
                WHERE p.estado IN ('ACTIVO','EN_TRANSITO','LISTO') OR r.id IS NOT NULL ORDER BY p.id
            """, ()),
            "vencidos_multas": ("""
                SELECT p.id, so.nombre socio, l.titulo, p.vence_en,
                       CAST(julianday(?) - julianday(p.vence_en) AS INTEGER) dias_atraso,
                       CAST(julianday(?) - julianday(p.vence_en) AS INTEGER) * ? multa_estimada_centavos
                FROM prestamos p JOIN socios so ON so.id=p.socio_id
                JOIN ejemplares e ON e.id=p.ejemplar_id JOIN libros l ON l.id=e.libro_id
                WHERE p.estado='ACTIVO' AND p.vence_en < ? ORDER BY dias_atraso DESC
            """, (hoy, hoy, self.MULTA_DIARIA_CENTAVOS, hoy)),
            "mas_solicitados": ("""
                SELECT l.id, l.titulo, l.isbn, COUNT(*) solicitudes_interbibliotecarias
                FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
                JOIN libros l ON l.id=e.libro_id
                WHERE p.tipo='INTERBIBLIOTECARIO'
                GROUP BY l.id ORDER BY solicitudes_interbibliotecarias DESC,l.titulo
            """, ()),
            "disponibilidad": ("""
                SELECT s.nombre sede, l.titulo, COUNT(e.id) total,
                       SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles,
                       SUM(CASE WHEN e.estado='EN_TRANSITO' THEN 1 ELSE 0 END) en_transito
                FROM ejemplares e JOIN sedes s ON s.id=e.sede_actual_id
                JOIN libros l ON l.id=e.libro_id GROUP BY s.id,l.id ORDER BY s.nombre,l.titulo
            """, ()),
            "logistica": ("""
                SELECT COUNT(*) envios, SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) recibidos,
                       SUM(CASE WHEN estado='DESPACHADO' THEN 1 ELSE 0 END) en_transito,
                       ROUND(100.0 * SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0),2) tasa_recepcion_pct,
                       ROUND(AVG(CASE WHEN estado='RECIBIDO' THEN
                         (julianday(recibido_en)-julianday(creado_en))*24 END),2) horas_promedio_trayecto
                FROM remitos
            """, ()),
            "movimientos": ("""
                SELECT o.nombre origen, d.nombre destino, r.tipo, COUNT(*) envios,
                       ROUND(AVG(CASE WHEN r.estado='RECIBIDO' THEN
                         (julianday(r.recibido_en)-julianday(r.creado_en))*24 END),2) horas_promedio
                FROM remitos r JOIN sedes o ON o.id=r.origen_id JOIN sedes d ON d.id=r.destino_id
                GROUP BY r.origen_id,r.destino_id,r.tipo ORDER BY envios DESC
            """, ()),
        }
        if nombre not in consultas:
            raise ReglaNegocio(f"Reporte desconocido: {nombre}")
        sql, parametros = consultas[nombre]
        with self.db.conexion() as con:
            return [dict(fila) for fila in con.execute(sql, parametros)]
