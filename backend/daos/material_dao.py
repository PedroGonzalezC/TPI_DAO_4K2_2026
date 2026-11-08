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


LibroDAO = MaterialDAO
