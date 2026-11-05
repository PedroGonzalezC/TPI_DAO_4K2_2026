"""Acceso a datos. Cada DAO usa la conexión de la transacción del servicio."""

from ..database.datos import TABLAS
from .reportes import REPORTES


class DAO:
    tabla = None

    def __init__(self, conexion):
        self.con = conexion

    def obtener(self, id_):
        return self.con.execute(f"SELECT * FROM {self.tabla} WHERE id=?", (id_,)).fetchone()

    def listar(self):
        return [dict(fila) for fila in self.con.execute(f"SELECT * FROM {self.tabla} ORDER BY id")]

    def insertar(self, **valores):
        columnas = ",".join(valores)
        marcadores = ",".join("?" for _ in valores)
        return self.con.execute(f"INSERT INTO {self.tabla}({columnas}) VALUES({marcadores})", tuple(valores.values())).lastrowid

    def actualizar(self, id_, **valores):
        if valores:
            asignaciones = ",".join(f"{campo}=?" for campo in valores)
            self.con.execute(f"UPDATE {self.tabla} SET {asignaciones} WHERE id=?", (*valores.values(), id_))


class SedeDAO(DAO):
    tabla = "sedes"


class SocioDAO(DAO):
    tabla = "socios"


class LibroDAO(DAO):
    tabla = "libros"


class EjemplarDAO(DAO):
    tabla = "ejemplares"

    def disponible(self, libro_id, sede_id):
        return self.con.execute("""SELECT id FROM ejemplares WHERE libro_id=? AND sede_actual_id=?
            AND estado='DISPONIBLE' ORDER BY id LIMIT 1""", (libro_id, sede_id)).fetchone()

    def disponibilidad(self, sede_id):
        filas = self.con.execute("""SELECT s.id sede_id, s.nombre sede, l.id libro_id, l.isbn, l.titulo,
            COUNT(e.id) ejemplares_totales, SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles
            FROM sedes s JOIN ejemplares e ON e.sede_actual_id=s.id JOIN libros l ON l.id=e.libro_id
            WHERE (? IS NULL OR s.id=?) GROUP BY s.id,l.id ORDER BY s.nombre,l.titulo""", (sede_id, sede_id))
        return [dict(fila) for fila in filas]


class ReservaDAO(DAO):
    tabla = "reservas"

    def en_espera(self, libro_id, sede_id):
        return self.con.execute("""SELECT r.id, so.habilitado, s.activa FROM reservas r JOIN socios so ON so.id=r.socio_id
            JOIN sedes s ON s.id=r.sede_id WHERE r.libro_id=? AND r.sede_id=?
            AND r.estado='EN_ESPERA' ORDER BY r.creada_en,r.id""", (libro_id, sede_id)).fetchall()

    def asignada(self, ejemplar_id):
        return self.con.execute("SELECT id, socio_id, sede_id FROM reservas WHERE ejemplar_id=? AND estado='ASIGNADA'", (ejemplar_id,)).fetchone()


class PrestamoDAO(DAO):
    tabla = "prestamos"


class RemitoDAO(DAO):
    tabla = "remitos"

    def ida(self, prestamo_id):
        return self.con.execute("SELECT recibido_en FROM remitos WHERE prestamo_id=? AND tipo='IDA'", (prestamo_id,)).fetchone()


class EventoRemitoDAO:
    def __init__(self, conexion):
        self.con = conexion

    def actualizar(self, remito_id, estado, fecha, detalle):
        self.con.execute("INSERT INTO historial_remitos(remito_id,estado,fecha,detalle) VALUES(?,?,?,?)", (remito_id, estado, fecha, detalle))

    def ultimo(self, remito_id):
        return self.con.execute("SELECT fecha FROM historial_remitos WHERE remito_id=? ORDER BY id DESC LIMIT 1", (remito_id,)).fetchone()

    def listar(self, remito_id):
        return [dict(fila) for fila in self.con.execute("SELECT estado,fecha,detalle FROM historial_remitos WHERE remito_id=? ORDER BY id", (remito_id,))]


class ReporteDAO:
    def __init__(self, conexion):
        self.con = conexion

    def consultar(self, nombre, parametros):
        _, sql = REPORTES[nombre]
        return [dict(fila) for fila in self.con.execute(sql, parametros)]


DAOS = {clase.tabla: clase for clase in (SedeDAO, SocioDAO, LibroDAO, EjemplarDAO, ReservaDAO, PrestamoDAO, RemitoDAO)}
assert set(DAOS) == set(TABLAS)
