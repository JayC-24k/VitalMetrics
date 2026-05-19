import flet as ft

from controllers.admin_controller import (
    borrar_evaluacion,
    borrar_usuario,
    crear_usuario_admin,
    editar_evaluacion,
    editar_usuario,
    obtener_dashboard,
    obtener_evaluaciones,
    obtener_usuarios,
)
from services.risk_service import calcular_riesgo_integral, clasificar_imc


def crear_pagina_admin(
    page,
    usuario_rol,
    usuario_id,
    cambiar_pagina,
    campo_auth,
    color_admin,
    color_acento,
    color_error,
    color_exito,
    color_texto,
    color_texto_suave,
):
    if usuario_rol != "admin":
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Acceso restringido", size=32, weight=ft.FontWeight.BOLD, color=color_error),
                ft.Text(
                    "Necesitas una cuenta administradora para ver esta seccion.",
                    size=16,
                    color=color_texto_suave,
                ),
            ],
        )

    mensaje = ft.Text(size=14, color=color_texto_suave)

    def mostrar_mensaje(texto, exito=True):
        mensaje.value = texto
        mensaje.color = color_exito if exito else color_error
        page.snack_bar = ft.SnackBar(ft.Text(texto))
        page.snack_bar.open = True
        cambiar_pagina(6)

    def cerrar_dialogo(dialogo):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        else:
            dialogo.open = False
            page.update()

    def abrir_dialogo(dialogo):
        if hasattr(page, "open"):
            page.open(dialogo)
        else:
            page.dialog = dialogo
            dialogo.open = True
            page.update()

    def tarjeta_metrica(titulo, valor, color):
        return ft.Container(
            width=190,
            height=100,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            padding=18,
            border=ft.border.all(1, "#E1DDF0"),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(titulo, size=13, color=color_texto_suave),
                    ft.Text(str(valor), size=30, weight=ft.FontWeight.BOLD, color=color),
                ],
            ),
        )

    def dialogo_usuario(usuario=None):
        es_edicion = usuario is not None
        nombre = campo_auth("Usuario")
        email = campo_auth("Email", keyboard_type=ft.KeyboardType.EMAIL)
        password = campo_auth("Contraseña nueva" if es_edicion else "Contraseña", password=True)
        rol = ft.Dropdown(
            label="Rol",
            width=320,
            options=[ft.dropdown.Option("user"), ft.dropdown.Option("admin")],
            value="user",
        )
        error = ft.Text(size=13, color=color_error)

        if es_edicion:
            nombre.value = usuario.get("username") or ""
            email.value = usuario.get("email") or ""
            rol.value = usuario.get("role") or "user"

        def guardar(e):
            if not nombre.value or (not es_edicion and not password.value):
                error.value = "Completa los campos requeridos"
                page.update()
                return
            if es_edicion:
                resultado = editar_usuario(
                    usuario.get("id"),
                    nombre.value,
                    email.value,
                    rol.value,
                    password.value or None,
                )
            else:
                resultado = crear_usuario_admin(
                    nombre.value,
                    email.value,
                    password.value,
                    rol.value,
                )
            if resultado.get("success"):
                cerrar_dialogo(dialogo)
                mostrar_mensaje(resultado.get("message", "Operacion completada"))
            else:
                error.value = resultado.get("message", "No se pudo guardar")
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar usuario" if es_edicion else "Nuevo usuario"),
            content=ft.Column([nombre, email, password, rol, error], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                ft.Button("Guardar", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=guardar),
            ],
        )
        abrir_dialogo(dialogo)

    def dialogo_evaluacion(evaluacion):
        edad = ft.TextField(label="Edad", width=180, value=str(evaluacion.get("edad") or ""))
        altura = ft.TextField(label="Altura (cm)", width=180, value=str(evaluacion.get("altura_cm") or ""))
        peso = ft.TextField(label="Peso (kg)", width=180, value=str(evaluacion.get("peso_kg") or ""))
        estrato = ft.Dropdown(
            label="Estrato",
            width=180,
            options=[ft.dropdown.Option(str(i)) for i in range(1, 7)],
            value=str(evaluacion.get("estrato") or "1"),
        )
        actividad = ft.Dropdown(
            label="Actividad fisica",
            width=250,
            options=[
                ft.dropdown.Option("Ninguna"),
                ft.dropdown.Option("1-2 veces/semana"),
                ft.dropdown.Option("3-4 veces/semana"),
                ft.dropdown.Option("5+ veces/semana"),
            ],
            value=evaluacion.get("actividad") or "Ninguna",
        )
        actividad_minutos = ft.TextField(label="Minutos/semana", width=180, value=str(evaluacion.get("actividad_minutos") or 0))
        calidad_alimentacion = ft.Dropdown(
            label="Alimentacion",
            width=200,
            options=[ft.dropdown.Option("Alta"), ft.dropdown.Option("Media"), ft.dropdown.Option("Baja")],
            value=evaluacion.get("calidad_alimentacion") or "Media",
        )
        comidas_dia = ft.Dropdown(
            label="Comidas/dia",
            width=160,
            options=[ft.dropdown.Option(str(i)) for i in range(1, 7)],
            value=str(evaluacion.get("comidas_dia") or "3"),
        )
        bebidas_azucaradas = ft.Dropdown(
            label="Bebidas azucaradas",
            width=230,
            options=[
                ft.dropdown.Option("Nunca"),
                ft.dropdown.Option("1-2 veces/semana"),
                ft.dropdown.Option("3-5 veces/semana"),
                ft.dropdown.Option("Diario"),
            ],
            value=evaluacion.get("bebidas_azucaradas") or "Nunca",
        )
        horas_sueno = ft.TextField(label="Horas sueno", width=160, value=str(evaluacion.get("horas_sueno") or 7))
        horas_pantalla = ft.TextField(label="Horas pantalla", width=170, value=str(evaluacion.get("horas_pantalla") or 0))
        antecedentes_familiares = ft.Dropdown(
            label="Antecedentes ECNT",
            width=220,
            options=[ft.dropdown.Option("No"), ft.dropdown.Option("Si"), ft.dropdown.Option("No sabe")],
            value=evaluacion.get("antecedentes_familiares") or "No",
        )
        acceso_espacios = ft.Dropdown(
            label="Acceso espacios",
            width=220,
            options=[ft.dropdown.Option("Bueno"), ft.dropdown.Option("Limitado"), ft.dropdown.Option("No tiene")],
            value=evaluacion.get("acceso_espacios") or "Bueno",
        )
        error = ft.Text(size=13, color=color_error)

        def guardar(e):
            try:
                imc, nivel = clasificar_imc(peso.value, altura.value)
                puntaje, riesgo = calcular_riesgo_integral(
                    imc,
                    int(estrato.value),
                    int(actividad_minutos.value),
                    calidad_alimentacion.value,
                    bebidas_azucaradas.value,
                    float(horas_sueno.value),
                    float(horas_pantalla.value),
                    antecedentes_familiares.value,
                    acceso_espacios.value,
                )
                resultado = editar_evaluacion(
                    evaluacion.get("id"),
                    edad.value,
                    altura.value,
                    peso.value,
                    estrato.value,
                    actividad.value,
                    imc,
                    nivel,
                    riesgo,
                    actividad_minutos=actividad_minutos.value,
                    calidad_alimentacion=calidad_alimentacion.value,
                    comidas_dia=comidas_dia.value,
                    bebidas_azucaradas=bebidas_azucaradas.value,
                    horas_sueno=horas_sueno.value,
                    horas_pantalla=horas_pantalla.value,
                    antecedentes_familiares=antecedentes_familiares.value,
                    acceso_espacios=acceso_espacios.value,
                    riesgo_puntaje=puntaje,
                )
            except ValueError:
                error.value = "Revisa los valores numericos"
                page.update()
                return

            if resultado.get("success"):
                cerrar_dialogo(dialogo)
                mostrar_mensaje(resultado.get("message", "Evaluacion actualizada"))
            else:
                error.value = resultado.get("message", "No se pudo guardar")
                page.update()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar evaluacion #{evaluacion.get('id')}"),
            content=ft.Container(
                width=360,
                height=520,
                content=ft.Column(
                    [
                        edad,
                        altura,
                        peso,
                        estrato,
                        actividad,
                        actividad_minutos,
                        calidad_alimentacion,
                        comidas_dia,
                        bebidas_azucaradas,
                        horas_sueno,
                        horas_pantalla,
                        antecedentes_familiares,
                        acceso_espacios,
                        error,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                ft.Button("Guardar", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=guardar),
            ],
        )
        abrir_dialogo(dialogo)

    def eliminar_usuario_admin(item):
        resultado = borrar_usuario(item.get("id"), usuario_id)
        mostrar_mensaje(resultado.get("message", "Operacion completada"), resultado.get("success", False))

    def eliminar_evaluacion_admin(item):
        resultado = borrar_evaluacion(item.get("id"))
        mostrar_mensaje(resultado.get("message", "Operacion completada"), resultado.get("success", False))

    dashboard = obtener_dashboard()
    usuarios = obtener_usuarios()
    evaluaciones = obtener_evaluaciones()

    def texto_tabla(valor, ancho=None, peso=ft.FontWeight.NORMAL):
        return ft.Text(
            str(valor),
            width=ancho,
            color=color_texto,
            size=14,
            weight=peso,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    def encabezado_tabla(valor, ancho=None):
        return ft.Text(valor, width=ancho, color="#263238", size=14, weight=ft.FontWeight.BOLD)

    def panel_tabla(tabla, ancho_minimo=720):
        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, "#D6D0EA"),
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            content=ft.Row([ft.Container(content=tabla, width=ancho_minimo)], scroll=ft.ScrollMode.AUTO),
        )

    usuarios_tabla = ft.DataTable(
        bgcolor=ft.Colors.WHITE,
        heading_row_color=ft.Colors.with_opacity(0.10, color_admin),
        data_row_color={ft.ControlState.HOVERED: ft.Colors.with_opacity(0.04, color_admin)},
        horizontal_lines=ft.BorderSide(1, "#E5E0F3"),
        divider_thickness=1,
        column_spacing=28,
        columns=[
            ft.DataColumn(encabezado_tabla("ID", 42)),
            ft.DataColumn(encabezado_tabla("Usuario", 110)),
            ft.DataColumn(encabezado_tabla("Email", 190)),
            ft.DataColumn(encabezado_tabla("Rol", 80)),
            ft.DataColumn(encabezado_tabla("Eval.", 58)),
            ft.DataColumn(encabezado_tabla("Acciones", 110)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(texto_tabla(usuario.get("id"), 42)),
                    ft.DataCell(texto_tabla(usuario.get("username") or "", 110, ft.FontWeight.W_600)),
                    ft.DataCell(texto_tabla(usuario.get("email") or "-", 190)),
                    ft.DataCell(texto_tabla(usuario.get("role") or "user", 80)),
                    ft.DataCell(texto_tabla(usuario.get("evaluations_count") or 0, 58)),
                    ft.DataCell(
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    icon_color=color_admin,
                                    on_click=lambda e, item=usuario: dialogo_usuario(item),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    icon_color=color_error,
                                    on_click=lambda e, item=usuario: eliminar_usuario_admin(item),
                                ),
                            ],
                            spacing=0,
                        )
                    ),
                ]
            )
            for usuario in usuarios
        ],
    )

    evaluaciones_tabla = ft.DataTable(
        bgcolor=ft.Colors.WHITE,
        heading_row_color=ft.Colors.with_opacity(0.10, color_admin),
        data_row_color={ft.ControlState.HOVERED: ft.Colors.with_opacity(0.04, color_admin)},
        horizontal_lines=ft.BorderSide(1, "#E5E0F3"),
        divider_thickness=1,
        column_spacing=24,
        columns=[
            ft.DataColumn(encabezado_tabla("ID", 42)),
            ft.DataColumn(encabezado_tabla("Usuario", 110)),
            ft.DataColumn(encabezado_tabla("IMC", 70)),
            ft.DataColumn(encabezado_tabla("Nivel", 110)),
            ft.DataColumn(encabezado_tabla("Puntaje", 80)),
            ft.DataColumn(encabezado_tabla("Riesgo", 90)),
            ft.DataColumn(encabezado_tabla("Fecha", 125)),
            ft.DataColumn(encabezado_tabla("Acciones", 110)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(texto_tabla(evaluacion.get("id"), 42)),
                    ft.DataCell(texto_tabla(evaluacion.get("username") or "-", 110, ft.FontWeight.W_600)),
                    ft.DataCell(texto_tabla(f"{evaluacion.get('imc'):.1f}", 70)),
                    ft.DataCell(texto_tabla(evaluacion.get("nivel") or "", 110)),
                    ft.DataCell(texto_tabla(evaluacion.get("riesgo_puntaje") or 0, 80)),
                    ft.DataCell(texto_tabla(evaluacion.get("riesgo") or "", 90, ft.FontWeight.W_600)),
                    ft.DataCell(texto_tabla(str(evaluacion.get("created_at") or "-")[:16], 125)),
                    ft.DataCell(
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    icon_color=color_admin,
                                    on_click=lambda e, item=evaluacion: dialogo_evaluacion(item),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    icon_color=color_error,
                                    on_click=lambda e, item=evaluacion: eliminar_evaluacion_admin(item),
                                ),
                            ],
                            spacing=0,
                        )
                    ),
                ]
            )
            for evaluacion in evaluaciones
        ],
    )

    riesgos = ", ".join(
        f"{item.get('riesgo')}: {item.get('total')}" for item in dashboard.get("por_riesgo", [])
    ) or "Sin evaluaciones"

    return ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=18,
        controls=[
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Panel admin",
                                size=34,
                                weight=ft.FontWeight.BOLD,
                                color=color_admin,
                                font_family="Cakecafe",
                            ),
                            ft.Text("Dashboard y CRUD de VitalMetrics", size=16, color=color_texto_suave),
                        ],
                        spacing=2,
                    ),
                    ft.Container(expand=True),
                    ft.Button("Nuevo usuario", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=lambda e: dialogo_usuario()),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    tarjeta_metrica("Usuarios", dashboard.get("usuarios", 0), color_admin),
                    tarjeta_metrica("Evaluaciones", dashboard.get("evaluaciones", 0), color_acento),
                    tarjeta_metrica("Riesgo alto", dashboard.get("riesgo_alto", 0), color_error),
                    tarjeta_metrica("IMC promedio", dashboard.get("promedio_imc", 0), color_exito),
                ],
                wrap=True,
                spacing=12,
            ),
            ft.Text(f"Distribucion por riesgo: {riesgos}", size=15, color=color_texto_suave),
            mensaje,
            ft.Text("Usuarios", size=24, weight=ft.FontWeight.BOLD, color=color_texto),
            panel_tabla(usuarios_tabla, 760),
            ft.Text("Evaluaciones", size=24, weight=ft.FontWeight.BOLD, color=color_texto),
            panel_tabla(evaluaciones_tabla, 960),
            ft.Container(height=30),
        ],
    )
