import flet as ft
import os
import threading
import time
from auth import crear_tabla
from ui.chat_widget import crear_boton_chat
from views.admin_view import crear_pagina_admin
from views.auth_view import crear_pagina_login, crear_pagina_registro
from views.evaluation_view import crear_pagina_evaluacion

def main(page: ft.Page):

    crear_tabla()

    usuario_logueado = False
    usuario_id = None
    usuario_rol = "user"

    page.fonts = {
        "CaviarDreams": "assets/CaviarDreams.ttf",
        "Eurofurence": "assets/eurof35.ttf",
        "Nirakolu": "assets/Nirakolu.ttf",
        "Cakecafe": "assets/Cakecafe.otf",
        "ChampagneLimousines": "assets/Champagne & Limousines.ttf",
    }
    
    page.theme = ft.Theme(font_family="ChampagneLimousines")
    
    page.title = "VitalMetrics"
    page.padding = 0
    page.bgcolor = "#F5F5F5"
    
    COLOR_BANNER = "#9AD7ED"
    COLOR_TITULOS = "#B7A5F0"
    COLOR_ACENTO = "#7B6CD9"
    COLOR_FONDO_CARRUSEL = "#E8DEF8"
    COLOR_FONDO_BENEFICIOS = "#E8DEF8"
    COLOR_TEXTO = "#2D2D2D"
    COLOR_TEXTO_SUAVE = "#5C567E"
    COLOR_ERROR = "#C94F6D"
    COLOR_EXITO = "#2E9D68"
    COLOR_PANEL_AUTH = "#FDFBFF"
    COLOR_ADMIN = "#1F6F8B"
    
    COLOR_MISION = "#B8E4F0"
    COLOR_VISION = "#F8D7E0"
    
    pagina_actual = 0

    def campo_auth(label, password=False, keyboard_type=ft.KeyboardType.TEXT):
        return ft.TextField(
            label=label,
            width=320,
            password=password,
            keyboard_type=keyboard_type,
            color=COLOR_TEXTO,
            bgcolor=ft.Colors.WHITE,
            border_color=COLOR_TITULOS,
            focused_border_color=COLOR_ACENTO,
            cursor_color=COLOR_ACENTO,
            label_style=ft.TextStyle(color=COLOR_TEXTO_SUAVE),
            text_style=ft.TextStyle(color=COLOR_TEXTO),
        )

    def mostrar_login_requerido():
        page.snack_bar = ft.SnackBar(
            ft.Text("Inicia sesion o registrate para usar la evaluacion")
        )
        page.snack_bar.open = True
        cambiar_pagina(4)

    def ir_a_evaluacion(e=None):
        if usuario_logueado:
            cambiar_pagina(3)
        else:
            mostrar_login_requerido()

    def actualizar_botones_protegidos():
        def recorrer(control):
            texto = ""
            if hasattr(control, "text"):
                texto = str(control.text)
            elif hasattr(control, "content") and hasattr(control.content, "value"):
                texto = str(control.content.value)

            texto = texto.lower()
            if "evaluaci" in texto and (
                "comenzar" in texto or texto.strip() == "evaluacion"
            ):
                control.visible = usuario_logueado

            if hasattr(control, "content") and control.content:
                recorrer(control.content)
            if hasattr(control, "controls"):
                for hijo in control.controls:
                    recorrer(hijo)

        try:
            btn_evaluacion.visible = usuario_logueado
        except NameError:
            pass
        try:
            recorrer(contenedor_paginas)
        except NameError:
            pass
        if page.controls:
            for control in page.controls:
                recorrer(control)
        actualizar_botones_auth()
        page.update()

    def actualizar_botones_auth():
        try:
            btn_login.visible = not usuario_logueado
            btn_registro.visible = not usuario_logueado
            btn_logout.visible = usuario_logueado
            btn_admin.visible = usuario_logueado and usuario_rol == "admin"
        except NameError:
            pass

    def actualizar_colores_menu(index):
        btn_inicio.style.color = ft.Colors.WHITE if index == 0 else "#2D2D2D"
        btn_beneficios.style.color = ft.Colors.WHITE if index == 1 else "#2D2D2D"
        btn_contacto.style.color = ft.Colors.WHITE if index == 2 else "#2D2D2D"
        btn_evaluacion.style.color = ft.Colors.WHITE if index == 3 else "#2D2D2D"
        try:
            btn_admin.style.color = ft.Colors.WHITE if index == 6 else "#2D2D2D"
        except NameError:
            pass
        page.update()
    
    def pagina_inicio():
        imagenes = [
            "assets/fotopanda1.jpeg",
            "assets/fotopanda2.jpeg",
            "assets/fotopanda3.jpeg",
        ]
        
        imagenes_validas = []
        for img in imagenes:
            if os.path.exists(img):
                imagenes_validas.append(img)
            else:
                print(f"No se encuentra: {img}")
        
        if not imagenes_validas:
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Agrega imagenes en la carpeta 'assets'", 
                           size=14, color=ft.Colors.GREY),
                    ft.Container(height=30),
                    ft.Button(
                        "COMENZAR EVALUACION",
                        bgcolor=COLOR_ACENTO,
                        color=ft.Colors.WHITE,
                        visible=usuario_logueado,
                        on_click=ir_a_evaluacion,
                    ),
                ]
            )

        
        indice_actual = 0
        imagen_actual = ft.Image(src=imagenes_validas[0], width=900, height=450, fit="contain")
        
        contenedor_imagen = ft.Container(
            content=imagen_actual,
            width=900,
            height=450,
            border_radius=20,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
        
        texto_contador = ft.Text(f"1 / {len(imagenes_validas)}", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        
        def cambiar_imagen(delta):
            nonlocal indice_actual
            indice_actual = (indice_actual + delta) % len(imagenes_validas)
            imagen_actual.src = imagenes_validas[indice_actual]
            texto_contador.value = f"{indice_actual + 1} / {len(imagenes_validas)}"
            page.update()
        
        boton_anterior = ft.Container(
            content=ft.Text("<", size=36, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            width=60,
            height=60,
            bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
            border_radius=30,
            alignment=ft.Alignment.CENTER,
            on_click=lambda e: cambiar_imagen(-1),
        )
        
        boton_siguiente = ft.Container(
            content=ft.Text(">", size=36, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            width=60,
            height=60,
            bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
            border_radius=30,
            alignment=ft.Alignment.CENTER,
            on_click=lambda e: cambiar_imagen(1),
        )
        
        def auto_cambiar():
            nonlocal indice_actual
            while True:
                time.sleep(4)
                try:
                    indice_actual = (indice_actual + 1) % len(imagenes_validas)
                    imagen_actual.src = imagenes_validas[indice_actual]
                    texto_contador.value = f"{indice_actual + 1} / {len(imagenes_validas)}"
                    page.update()
                except Exception as e:
                    print(f"Error en auto_cambiar: {e}")
        
        if len(imagenes_validas) > 1:
            threading.Thread(target=auto_cambiar, daemon=True).start()
        
        carrusel = ft.Stack(
            [
                contenedor_imagen,
                ft.Container(
                    content=ft.Row(
                        [boton_anterior, boton_siguiente],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    width=900,
                    top=195,
                )
            ]
        )
        
        cuadrado_info = ft.Container(
            width=220,
            height=530,
            bgcolor=COLOR_BANNER,
            border_radius=20,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Container(
                width=230,
                height=510,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                margin=ft.Margin.all(10),
                padding=ft.Padding.symmetric(horizontal=8, vertical=12),
                content=ft.Column(
                    [
                        ft.Container(
                            width=185,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                "ASIS\nCUNDINAMARCA 2024",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=COLOR_ACENTO,
                            border_radius=30,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        ),
                        ft.Container(height=6),
                        ft.Text("41.4%", size=28, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER),
                        ft.Text("de adultos mayores de 64 anos\npresentan exceso de peso", size=11, color="#2D2D2D", text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        ft.Text("6 de cada 10", size=15, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER),
                        ft.Text("adultos en Cundinamarca\ntienen sobrepeso", size=10, color="#2D2D2D", text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        ft.Text("52% -> 59.3%", size=15, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER),
                        ft.Text("aumento en la ultima decada\n(2013 - 2023)", size=10, color="#2D2D2D", text_align=ft.TextAlign.CENTER),
                        ft.Container(height=12),
                        ft.Container(width=180, height=1, bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                        ft.Container(height=10),
                        ft.Text("Prevencion es la clave", size=12, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER),
                        ft.Text("Actua hoy para proteger\ntu salud del manana", size=9, color="#2D2D2D", text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
            ),
        )
        
        fila_contenido = ft.Row(
            [
                ft.Column(
                    [
                        carrusel,
                        ft.Container(height=0),
                        ft.Container(
                            width=900,
                            content=ft.Row(
                                [ft.Button(
                                    "COMENZAR EVALUACION",
                                    bgcolor=COLOR_ACENTO,
                                    color=ft.Colors.WHITE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=30),
                                        padding=ft.Padding.symmetric(horizontal=40, vertical=15),
                                    ),
                                    visible=usuario_logueado,
                                    on_click=ir_a_evaluacion,
                                )],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ),
                    ]
                ),
                ft.Container(width=5),
                cuadrado_info,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        fondo_contenedor = ft.Container(
            expand=True,
            height=560,
            bgcolor=COLOR_FONDO_CARRUSEL,
            border_radius=25,
            padding=ft.Padding.symmetric(horizontal=15, vertical=15),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
            content=fila_contenido,
        )
        
        return ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=5),
                fondo_contenedor,
            ]
        )
    
    def _tarjeta(titulo, descripcion):
        return ft.Container(
            width=200,
            padding=20,
            bgcolor="#BFE5FF",
            border_radius=15,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO),
                    ft.Text(descripcion, size=12, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                ]
            )
        )
    
    def pagina_beneficios():
        tarjetas = ft.ResponsiveRow(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=30,
            run_spacing=30,
            controls=[
                _beneficio_card(
                    "assets/beneficios3.png",
                    "Predictivo, no solo descriptivo", 
                    "No solo te decimos como estas hoy. Nuestro sistema de analisis anticipa que riesgo tienes de desarrollar enfermedades cronicas no transmisibles (diabetes, hipertension, problemas cardiovasculares) en el futuro."
                ),
                _beneficio_card(
                    "assets/beneficios1.png",
                    "Basado en datos reales", 
                    "Nuestro sistema de analisis fue entrenado con datos de jovenes colombianos de 16 a 26 anos. El modelo analiza patrones complejos que relacionan IMC, actividad fisica y contexto socioeconomico."
                ),
                _beneficio_card(
                    "assets/beneficios6.png",
                    "Entiende tu contexto", 
                    "El estrato socioeconomico importa tanto como tus habitos. No es lo mismo vivir en un entorno con acceso a parques, gimnasios y comida saludable, que en uno sin estas oportunidades."
                ),
                _beneficio_card(
                    "assets/beneficios5.png",
                    "Resultados inmediatos", 
                    "Ingresa tus datos (edad, altura, peso, estrato y actividad fisica) y en segundos obtienes tu nivel de riesgo junto con recomendaciones personalizadas."
                ),
                _beneficio_card(
                    "assets/beneficios2.png",
                    "Privacidad garantizada", 
                    "Tus datos son completamente anonimos. Solo se utilizan para generar tu prediccion y mejorar nuestro modelo. No compartimos informacion personal con terceros."
                ),
                _beneficio_card(
                    "assets/beneficios4.png",
                    "Recomendaciones personalizadas", 
                    "Cada resultado incluye consejos concretos y accionables basados en tu perfil unico. Desde sugerencias de actividad fisica hasta cambios en la alimentacion."
                ),
            ],
        )
        
        fondo_beneficios = ft.Container(
            width=1300,
            bgcolor=COLOR_FONDO_BENEFICIOS,
            border_radius=25,
            padding=ft.Padding.symmetric(horizontal=30, vertical=30),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                [
                    ft.Text("Beneficios de VitalMetrics", size=42, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER, font_family="Cakecafe"),
                    ft.Text("Descubre como nuestra plataforma transforma tu salud", size=18, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    tarjetas,
                    ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        [ft.Button(
                            "PROBAR AHORA", 
                            bgcolor=COLOR_ACENTO, 
                            color=ft.Colors.WHITE, 
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=30), 
                                padding=ft.Padding.symmetric(horizontal=50, vertical=18)
                            ), 
                            on_click=lambda e: cambiar_pagina(5)
                        )],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(height=10),
                fondo_beneficios,
                ft.Container(height=20),
            ],
        )
    
    def _beneficio_card(icono_ruta, titulo, descripcion):
        if os.path.exists(icono_ruta):
            icono_widget = ft.Image(
                src=icono_ruta,
                width=130,
                height=130,
                fit="contain",
            )
        else:
            icono_widget = ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=70, color=COLOR_ACENTO)
            print(f"No se encuentra la imagen: {icono_ruta}")
        
        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4},
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    icono_widget,
                    ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO),
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.Text(descripcion, size=13, color=ft.Colors.GREY_700, text_align=ft.TextAlign.JUSTIFY),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    
    def pagina_contacto():
        
        intro_general = ft.Container(
            width=1000,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    ft.Text("Sobre VitalMetrics", size=24, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, font_family="Cakecafe"),
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                    ft.Text(
                        "Actualmente, las enfermedades cronicas no transmisibles representan uno de los mayores desafios en salud publica, muchas de ellas originadas en habitos adquiridos durante la juventud.",
                        size=15,
                        color="#2D2D2D",
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "En respuesta a esta problematica, nuestro sistema integra datos personales como el indice de masa corporal (IMC), el nivel socioeconomico y la actividad fisica para analizar patrones y predecir posibles riesgos en la salud fisica.",
                        size=15,
                        color="#2D2D2D",
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "A traves del uso de metodos de analisis y herramientas predictivas, buscamos no solo identificar riesgos, sino tambien brindar informacion util que permita tomar decisiones oportunas y fomentar estilos de vida saludables.",
                        size=15,
                        color="#2D2D2D",
                    ),
                ],
                spacing=10,
            ),
        )
        
        tarjeta_mision = ft.Container(
            width=480,
            bgcolor=COLOR_MISION,
            border_radius=20,
            padding=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    ft.Text("Mision", size=24, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, font_family="Cakecafe"),
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                    ft.Text(
                        "Desarrollar un sistema predictivo de salud fisica basado en datos personales que permita identificar riesgos tempranos de enfermedades cronicas no transmisibles, integrando variables como el indice de masa corporal (IMC), el nivel socioeconomico y la actividad fisica, con el fin de promover la prevencion, mejorar la calidad de vida y optimizar la toma de decisiones en salud.",
                        size=14,
                        color="#2D2D2D",
                    ),
                ],
                spacing=10,
            ),
        )
        
        tarjeta_vision = ft.Container(
            width=480,
            bgcolor=COLOR_VISION,
            border_radius=20,
            padding=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    ft.Text("Vision", size=24, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, font_family="Cakecafe"),
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                    ft.Text(
                        "Ser una herramienta innovadora lider en el ambito de la salud digital, reconocida por su capacidad de anticipar riesgos fisicos mediante analisis de datos, contribuyendo a la prevencion de enfermedades y al desarrollo de una sociedad mas saludable, informada y consciente de sus habitos de vida.",
                        size=14,
                        color="#2D2D2D",
                    ),
                ],
                spacing=10,
            ),
        )
        
        intro_contacto = ft.Container(
            width=1000,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    ft.Text("Tienes dudas o sugerencias?", size=24, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, font_family="Cakecafe"),
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                    ft.Text(
                        "Tienes dudas, sugerencias o quieres saber mas sobre nuestro sistema predictivo de salud? Estamos disponibles para ayudarte. Puedes contactarnos a traves de los siguientes medios:",
                        size=15,
                        color="#2D2D2D",
                    ),
                ],
                spacing=10,
            ),
        )
        
        contacto_items = []
        
        ruta_email = "assets/gmail.png"
        ruta_phone = "assets/telefono.png"
        ruta_github = "assets/github.png"

        def icono_contacto(ruta, icono):
            if os.path.exists(ruta):
                return ft.Image(src=ruta, width=30, height=30, fit="contain")
            return ft.Icon(icono, size=30, color=COLOR_ACENTO)

        def abrir_github(e=None):
            page.launch_url("https://github.com/JayC-24k")

        contacto_items.append(
            ft.Text("Juan Camilo Trujillo Ramirez", size=18, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO)
        )
        
        contacto_items.append(
            ft.Row(
                [
                    icono_contacto(ruta_email, ft.Icons.EMAIL),
                    ft.Text("jayce24k@gmail.com", size=16, color="#2D2D2D"),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        
        contacto_items.append(
            ft.Row(
                [
                    icono_contacto(ruta_phone, ft.Icons.PHONE),
                    ft.Text("+57 3137164757", size=16, color="#2D2D2D"),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        
        contacto_items.append(
            ft.Row(
                [
                    ft.Container(
                        content=icono_contacto(ruta_github, ft.Icons.CODE),
                        on_click=abrir_github,
                        tooltip="Abrir GitHub",
                    ),
                    ft.Button(
                        "GitHub",
                        bgcolor=COLOR_ACENTO,
                        color=ft.Colors.WHITE,
                        on_click=abrir_github,
                    ),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        contacto_items.append(
            ft.Divider(height=12, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
        )

        contacto_items.append(
            ft.Text("Alison Daiana Sierra Gonzalez", size=18, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO)
        )

        contacto_items.append(
            ft.Row(
                [
                    icono_contacto(ruta_email, ft.Icons.EMAIL),
                    ft.Text("meaoowwwo@gmail.com", size=16, color="#2D2D2D"),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        contacto_items.append(
            ft.Row(
                [
                    icono_contacto(ruta_phone, ft.Icons.PHONE),
                    ft.Text("+57 319 6060435", size=16, color="#2D2D2D"),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        
        tarjeta_contacto = ft.Container(
            width=1000,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=25,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            content=ft.Column(
                [
                    ft.Text("Contacto", size=24, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, font_family="Cakecafe"),
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                    ft.Column(contacto_items, spacing=15),
                ],
                spacing=15,
            ),
        )
        
        frase_final = ft.Container(
            width=1000,
            bgcolor=COLOR_FONDO_CARRUSEL,
            border_radius=20,
            padding=20,
            content=ft.Text(
                "Nuestro equipo esta comprometido con el desarrollo de soluciones tecnologicas que mejoren la calidad de vida mediante el analisis de datos.",
                size=16,
                weight=ft.FontWeight.W_500,
                color=COLOR_ACENTO,
                text_align=ft.TextAlign.CENTER,
            ),
        )
        
        fondo_contacto = ft.Container(
            width=1100,
            bgcolor=ft.Colors.WHITE,
            border_radius=25,
            padding=ft.Padding.symmetric(horizontal=30, vertical=30),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                [
                    intro_general,
                    ft.Container(height=20),
                    ft.Row(
                        [tarjeta_mision, tarjeta_vision],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30,
                    ),
                    ft.Container(height=25),
                    intro_contacto,
                    ft.Container(height=15),
                    tarjeta_contacto,
                    ft.Container(height=20),
                    frase_final,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(height=20),
                ft.Text("Contacto", size=42, weight=ft.FontWeight.BOLD, color=COLOR_ACENTO, text_align=ft.TextAlign.CENTER, font_family="Cakecafe"),
                ft.Text("Conoce mas sobre nuestro proyecto y como contactarnos", size=18, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                fondo_contacto,
                ft.Container(height=40),
            ],
        )
    
    def pagina_evaluacion():
        return crear_pagina_evaluacion(
            page,
            usuario_logueado,
            usuario_id,
            COLOR_ACENTO,
            COLOR_TEXTO,
        )
    
    def aplicar_login_exitoso(respuesta):
        nonlocal usuario_logueado, usuario_id, usuario_rol
        usuario_logueado = True
        usuario_id = respuesta.get("user_id")
        usuario_rol = respuesta.get("role", "user")
        actualizar_botones_protegidos()
        cambiar_pagina(0)

    def pagina_login():
        return crear_pagina_login(
            page,
            campo_auth,
            cambiar_pagina,
            aplicar_login_exitoso,
            COLOR_ACENTO,
            COLOR_ERROR,
            COLOR_EXITO,
            COLOR_PANEL_AUTH,
            COLOR_TEXTO_SUAVE,
        )
    
    def pagina_registro():
        return crear_pagina_registro(
            page,
            campo_auth,
            cambiar_pagina,
            aplicar_login_exitoso,
            COLOR_ACENTO,
            COLOR_ERROR,
            COLOR_EXITO,
            COLOR_PANEL_AUTH,
            COLOR_TEXTO_SUAVE,
        )

    def pagina_admin():
        return crear_pagina_admin(
            page,
            usuario_rol,
            usuario_id,
            cambiar_pagina,
            campo_auth,
            COLOR_ADMIN,
            COLOR_ACENTO,
            COLOR_ERROR,
            COLOR_EXITO,
            COLOR_TEXTO,
            COLOR_TEXTO_SUAVE,
        )

    def construir_pagina(index):
        constructores = [
            pagina_inicio,
            pagina_beneficios,
            pagina_contacto,
            pagina_evaluacion,
            pagina_login,
            pagina_registro,
            pagina_admin,
        ]
        return constructores[index]()
    
    contenedor_paginas = ft.Container(
        content=construir_pagina(0),
        expand=True,
        padding=ft.Padding.symmetric(horizontal=24, vertical=14),
    )
    
    def cambiar_pagina(index):
        nonlocal pagina_actual
        if index == 3 and not usuario_logueado:
            mostrar_login_requerido()
            return
        if index == 6 and usuario_rol != "admin":
            page.snack_bar = ft.SnackBar(ft.Text("Acceso solo para administradores"))
            page.snack_bar.open = True
            page.update()
            return

        pagina_actual = index
        contenedor_paginas.content = construir_pagina(index)
        actualizar_colores_menu(index)
        
        actualizar_botones_auth()
        
        contenedor_paginas.update()
        page.update()

    def cerrar_sesion(e=None):
        nonlocal usuario_logueado, usuario_id, usuario_rol
        usuario_logueado = False
        usuario_id = None
        usuario_rol = "user"
        actualizar_botones_protegidos()
        cambiar_pagina(0)
    
    
    btn_login = ft.Button(
        "Iniciar sesion",
        bgcolor=COLOR_ACENTO,
        color=ft.Colors.WHITE,
        on_click=lambda e: cambiar_pagina(4),
    )

    btn_registro = ft.OutlinedButton(
        "Registrarse",
        style=ft.ButtonStyle(color=COLOR_ACENTO),
        on_click=lambda e: cambiar_pagina(5),
    )

    btn_logout = ft.Button(
        "Cerrar sesion",
        bgcolor=COLOR_ACENTO,
        color=ft.Colors.WHITE,
        visible=False,
        on_click=cerrar_sesion,
    )

    btn_inicio = ft.TextButton(
        content=ft.Text("Inicio", size=16, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(color="#2D2D2D"),
        on_click=lambda e: cambiar_pagina(0),
    )
    
    btn_beneficios = ft.TextButton(
        content=ft.Text("Beneficios", size=16, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(color="#2D2D2D"),
        on_click=lambda e: cambiar_pagina(1),
    )
    
    btn_contacto = ft.TextButton(
        content=ft.Text("Contacto", size=16, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(color="#2D2D2D"),
        on_click=lambda e: cambiar_pagina(2),
    )
    
    btn_evaluacion = ft.TextButton(
        content=ft.Text("Evaluacion", size=16, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(color="#2D2D2D"),
        visible=usuario_logueado,
        on_click=ir_a_evaluacion,
    )

    btn_admin = ft.TextButton(
        content=ft.Text("Admin", size=16, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(color="#2D2D2D"),
        visible=False,
        on_click=lambda e: cambiar_pagina(6),
    )
    
    ruta_icono = "assets/fotopanda5.png"
    
    if os.path.exists(ruta_icono):
        icono_vital = ft.Image(
            src=ruta_icono,
            width=50,
            height=50,
            fit="contain",
        )
    else:
        icono_vital = ft.Container(width=0, height=0)
        print(f"No se encuentra la imagen: {ruta_icono}")
    
    nav = ft.Container(
        bgcolor=COLOR_BANNER,
        padding=ft.Padding.symmetric(horizontal=22, vertical=10),
        content=ft.Row(
            [
                ft.Row(
                    [
                        icono_vital,
                        ft.Row(
                            [
                                ft.Text("Vital", size=32, weight=ft.FontWeight.BOLD, font_family="Cakecafe", color=ft.Colors.BLACK),
                                ft.Text("Metrics", size=32, weight=ft.FontWeight.BOLD, font_family="Cakecafe", color=ft.Colors.WHITE),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                btn_inicio,
                btn_beneficios,
                btn_contacto,
                btn_evaluacion,
                btn_admin,
                ft.Container(width=12),
                ft.Row(
                    [btn_login, btn_registro, btn_logout],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    
    actualizar_colores_menu(0)
    
    page.floating_action_button = crear_boton_chat(page, COLOR_ACENTO)
    page.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT

    contenido_principal = ft.Column(
        controls=[
            nav,
            contenedor_paginas,
        ],
        expand=True,
    )

    page.add(contenido_principal)
    actualizar_botones_protegidos()
    page.update()

ft.run(main, assets_dir="assets")







