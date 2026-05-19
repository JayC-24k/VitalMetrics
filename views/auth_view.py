import flet as ft

from auth import login_usuario as login_usuario_local
from auth import registrar_usuario as registrar_usuario_local


def crear_pagina_login(
    page,
    campo_auth,
    cambiar_pagina,
    on_login_success,
    color_acento,
    color_error,
    color_exito,
    color_panel_auth,
    color_texto_suave,
):
    email = campo_auth("Usuario")
    password = campo_auth("Contraseña", password=True)
    mensaje = ft.Text(size=14, color=color_texto_suave)

    def ingresar(e):
        if not email.value or not password.value:
            mensaje.value = "Completa todos los campos"
            mensaje.color = color_error
            page.update()
            return

        respuesta = login_usuario_local(email.value, password.value)
        mensaje.value = respuesta.get("message", "Error")

        if respuesta.get("success", False):
            mensaje.color = color_exito
            page.snack_bar = ft.SnackBar(ft.Text(f"Bienvenido {email.value}"))
            page.snack_bar.open = True
            on_login_success(respuesta)
        else:
            mensaje.color = color_error

        page.update()

    return _contenedor_auth(
        color_panel_auth,
        ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Iniciar sesion",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=color_acento,
                    font_family="Cakecafe",
                ),
                ft.Text("Accede para guardar tus evaluaciones", size=15, color=color_texto_suave),
                ft.Divider(height=22, color=ft.Colors.TRANSPARENT),
                email,
                password,
                mensaje,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Button("Entrar", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=ingresar),
                ft.TextButton(
                    "No tienes cuenta? Registrate",
                    style=ft.ButtonStyle(color=color_acento),
                    on_click=lambda e: cambiar_pagina(5),
                ),
            ],
        ),
    )


def crear_pagina_registro(
    page,
    campo_auth,
    cambiar_pagina,
    on_register_success,
    color_acento,
    color_error,
    color_exito,
    color_panel_auth,
    color_texto_suave,
):
    nombre = campo_auth("Usuario")
    email_registro = campo_auth("Email", keyboard_type=ft.KeyboardType.EMAIL)
    password = campo_auth("Contraseña", password=True)
    mensaje = ft.Text(size=14, color=color_texto_suave)

    def registrar(e):
        if not nombre.value or not password.value:
            mensaje.value = "Completa todos los campos"
            mensaje.color = color_error
            page.update()
            return

        respuesta = registrar_usuario_local(nombre.value, password.value, email_registro.value)
        mensaje.value = respuesta.get("message", "Error")

        if respuesta.get("success", False):
            mensaje.color = color_exito
            page.snack_bar = ft.SnackBar(ft.Text("Cuenta creada"))
            page.snack_bar.open = True
            on_register_success(respuesta)
        else:
            mensaje.color = color_error

        page.update()

    return _contenedor_auth(
        color_panel_auth,
        ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Registro",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=color_acento,
                    font_family="Cakecafe",
                ),
                ft.Text("Crea tu cuenta para iniciar el seguimiento", size=15, color=color_texto_suave),
                ft.Divider(height=22, color=ft.Colors.TRANSPARENT),
                nombre,
                email_registro,
                password,
                mensaje,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                ft.Button("Registrarse", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=registrar),
                ft.TextButton(
                    "Ya tienes cuenta? Inicia sesion",
                    style=ft.ButtonStyle(color=color_acento),
                    on_click=lambda e: cambiar_pagina(4),
                ),
            ],
        ),
    )


def _contenedor_auth(color_panel_auth, content):
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Container(
            width=460,
            bgcolor=color_panel_auth,
            border_radius=16,
            padding=ft.Padding.symmetric(horizontal=42, vertical=34),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
            content=content,
        ),
    )
