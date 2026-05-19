from auth import conectar, crear_tabla, hash_password, login_usuario
from auth import registrar_usuario as _registrar_usuario


def registrar_usuario(username, email=None, password=None):
    if password is None:
        password = email
        email = None
    return _registrar_usuario(username=username, email=email, password=password)
