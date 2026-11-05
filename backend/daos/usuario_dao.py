"""Persistencia de las cuentas de personal."""


class UsuarioDAO:
    def __init__(self, conexion):
        self.conexion = conexion

    def crear(self, nombre, salt, clave_hash):
        self.conexion.execute("INSERT INTO usuarios(nombre,salt,clave_hash,rol) VALUES(?,?,?,'PERSONAL')", (nombre, salt, clave_hash))

    def obtener(self, nombre):
        return self.conexion.execute("SELECT id,nombre,salt,clave_hash,rol FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
