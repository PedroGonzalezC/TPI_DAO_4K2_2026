"""Alta de personal y comprobación de credenciales locales."""

import argparse
import getpass
import hashlib
import hmac
import secrets
import sqlite3

from ..database.configuracion import CONFIG
from ..database.datos import BaseDatos
from ..daos.usuario_dao import UsuarioDAO


ITERACIONES = 600_000


def _hash(clave, salt):
    return hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'), salt, ITERACIONES)


def crear_usuario(db, nombre, clave):
    nombre = nombre.strip()
    if not nombre or len(clave) < 8:
        raise ValueError('Ingresá un usuario y una contraseña de al menos 8 caracteres.')
    salt = secrets.token_bytes(16)
    try:
        with db.conexion() as con:
            UsuarioDAO(con).crear(nombre, salt, _hash(clave, salt))
    except sqlite3.IntegrityError as exc:
        raise ValueError('El usuario ya existe.') from exc


def autenticar(db, nombre, clave):
    with db.conexion() as con:
        usuario = UsuarioDAO(con).obtener(nombre)
    if usuario and hmac.compare_digest(_hash(clave, usuario['salt']), usuario['clave_hash']):
        return {'id': usuario['id'], 'nombre': usuario['nombre'], 'rol': usuario['rol']}
    return None


def main():
    parser = argparse.ArgumentParser(description='Crear usuario de personal')
    parser.add_argument('--db', default=CONFIG['base_datos'])
    parser.add_argument('--usuario', required=True)
    args = parser.parse_args()
    clave = getpass.getpass('Contraseña: ')
    if clave != getpass.getpass('Repetir contraseña: '):
        parser.error('Las contraseñas no coinciden.')
    try:
        crear_usuario(BaseDatos(args.db), args.usuario, clave)
    except ValueError as exc:
        parser.error(str(exc))
    print('Usuario de personal creado.')


if __name__ == '__main__':
    main()
