import flet as ft

from auth import login_usuario, registrar_usuario


def crear_landing(page, session):

    # ========= BOTONES PROTEGIDOS =========

    boton_nav_evaluacion = ft.TextButton(
        "Evaluacion",
        visible=False
    )

    boton_comenzar = ft.ElevatedButton(
        "COMENZAR EVALUACION",
        visible=False
    )

    # ========= CAMPOS LOGIN =========

    username_login = ft.TextField(label="Usuario")
    password_login = ft.TextField(label="Contrasena", password=True)

    # ========= CAMPOS REGISTRO =========

    username_reg = ft.TextField(label="Usuario")
    password_reg = ft.TextField(label="Contrasena", password=True)

    # ========= FUNCION ACTUALIZAR UI =========

    def actualizar_ui():

        boton_nav_evaluacion.visible = session.usuario_logueado
        boton_comenzar.visible = session.usuario_logueado

        page.update()

    # ========= LOGIN =========

    def hacer_login(e):

        resultado = login_usuario(
            username_login.value,
            password_login.value
        )

        if resultado.get("success"):

            session.login(username_login.value)

            page.snack_bar = ft.SnackBar(
                ft.Text("Login correcto")
            )

        else:

            page.snack_bar = ft.SnackBar(
                ft.Text("Credenciales incorrectas")
            )

        page.snack_bar.open = True

        actualizar_ui()

    # ========= REGISTRO =========

    def hacer_registro(e):

        resultado = registrar_usuario(
            username_reg.value,
            password_reg.value
        )

        if resultado.get("success"):

            page.snack_bar = ft.SnackBar(
                ft.Text("Usuario registrado")
            )

        else:

            page.snack_bar = ft.SnackBar(
                ft.Text("Error en registro")
            )

        page.snack_bar.open = True

        page.update()

    # ========= DIALOGOS =========

    login_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Iniciar sesion"),
        content=ft.Column([
            username_login,
            password_login,
            ft.ElevatedButton("Entrar", on_click=hacer_login)
        ])
    )

    register_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Registro"),
        content=ft.Column([
            username_reg,
            password_reg,
            ft.ElevatedButton("Registrarse", on_click=hacer_registro)
        ])
    )

    # ========= NAVBAR =========

    navbar = ft.Row(
        [
            ft.TextButton("Inicio"),
            ft.TextButton("Beneficios"),
            ft.TextButton("Contacto"),
            boton_nav_evaluacion,
            ft.ElevatedButton(
                "Iniciar sesion",
                on_click=lambda e: page.open(login_dialog)
            ),
            ft.ElevatedButton(
                "Registrarse",
                on_click=lambda e: page.open(register_dialog)
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # ========= LANDING =========

    landing = ft.Column(
        [
            ft.Text(
                "Cuida tu salud desde hoy",
                size=40,
                weight="bold"
            ),
            boton_comenzar
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

    actualizar_ui()

    return ft.Column(
        [
            navbar,
            landing
        ],
        expand=True
    )
