"""DAO de Material: acceso a datos del catálogo bibliográfico (tabla libros)."""

import sqlite3

from ..models.material import Material


class MaterialDAO:
    """Encapsula las consultas y operaciones SQL sobre materiales bibliográficos."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def crear(self, material: Material) -> int:
        cursor = self.con.execute(
            "INSERT INTO libros(isbn, titulo, autor, anio) VALUES(?, ?, ?, ?)",
            (material.isbn, material.titulo, material.autor, material.anio),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, libro_id: int) -> Material | None:
        fila = self.con.execute("SELECT * FROM libros WHERE id=?", (libro_id,)).fetchone()
        if fila is None:
            return None
        return Material(
            id=fila["id"],
            isbn=fila["isbn"],
            titulo=fila["titulo"],
            autor=fila["autor"],
            anio=fila["anio"],
        )

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM libros ORDER BY id")]

    def actualizar(self, material: Material) -> None:
        self.con.execute(
            "UPDATE libros SET titulo=?, autor=?, anio=? WHERE id=?",
            (material.titulo, material.autor, material.anio, material.id),
        )

    def tiene_dependencias(self, libro_id: int) -> bool:
        ejemplares = self.con.execute(
            "SELECT 1 FROM ejemplares WHERE libro_id=? LIMIT 1", (libro_id,)
        ).fetchone()
        reservas = self.con.execute(
            "SELECT 1 FROM reservas WHERE libro_id=? LIMIT 1", (libro_id,)
        ).fetchone()
        return ejemplares is not None or reservas is not None

    def eliminar(self, libro_id: int) -> None:
        self.con.execute("DELETE FROM libros WHERE id=?", (libro_id,))


LibroDAO = MaterialDAO
