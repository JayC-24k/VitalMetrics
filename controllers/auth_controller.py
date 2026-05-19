from models.db import inicializar_db
from models.user_model import asegurar_admin_inicial, autenticar_usuario, crear_usuario


def crear_tabla():
    inicializar_db()
    asegurar_admin_inicial()


def registrar_usuario(username, password, email=None, role="user"):
    return crear_usuario(username=username, password=password, email=email, role=role)


def login_usuario(username, password):
    return autenticar_usuario(username=username, password=password)
