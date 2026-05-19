import os

import flet as ft
import requests
from services.chat_scope import es_mensaje_vitalmetrics, respuesta_fuera_de_tema

CHAT_BG = "#FDFBFF"
CHAT_PANEL = "#F4F0FF"
CHAT_TEXT = "#2D2D2D"
CHAT_MUTED = "#5C567E"
CHAT_USER = "#1F6F8B"
CHAT_BOT = "#7B6CD9"
CHAT_ERROR = "#C94F6D"

def abrir_chat(page, color_acento, e=None):
    mensajes = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    campo = ft.TextField(
        hint_text="Escribe un mensaje...",
        expand=True,
        color=CHAT_TEXT,
        bgcolor=ft.Colors.WHITE,
        border_color="#B7A5F0",
        focused_border_color=color_acento,
        cursor_color=color_acento,
        hint_style=ft.TextStyle(color=CHAT_MUTED),
        text_style=ft.TextStyle(color=CHAT_TEXT),
    )

    mensajes.controls.append(
        ft.Text(
            "Hola, soy el asistente de VitalMetrics.",
            color=CHAT_MUTED,
        )
    )

    def enviar_mensaje(ev=None):
        if not campo.value:
            return

        texto_usuario = campo.value
        mensajes.controls.append(
            ft.Text(
                f"Tu: {texto_usuario}",
                color=CHAT_USER,
                weight=ft.FontWeight.W_600,
            )
        )

        campo.value = ""
        page.update()

        if not es_mensaje_vitalmetrics(texto_usuario):
            mensajes.controls.append(
                ft.Text(
                    f"Bot: {respuesta_fuera_de_tema()}",
                    color=CHAT_ERROR,
                )
            )
            page.update()
            return

        try:
            respuesta = requests.post(
                "http://127.0.0.1:5000/chat",
                json={"message": texto_usuario},
                timeout=30,
            )
            if respuesta.status_code == 200:
                texto_bot = respuesta.json().get("response", "Sin respuesta")
                color_respuesta = CHAT_ERROR if (
                    "servicio del chat devolvio" in texto_bot
                    or "Falta configurar" in texto_bot
                    or "No pude conectar" in texto_bot
                ) else CHAT_BOT
            else:
                texto_bot = "Error del servidor"
                color_respuesta = CHAT_ERROR
        except Exception as ex:
            texto_bot = f"No pude conectar con el servidor del chat: {ex}"
            color_respuesta = CHAT_ERROR

        mensajes.controls.append(
            ft.Text(
                f"Bot: {texto_bot}",
                color=color_respuesta,
            )
        )
        page.update()

    def cerrar_chat(ev=None):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        else:
            dialogo.open = False
            page.update()

    campo.on_submit = enviar_mensaje

    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Chat VitalMetrics",
            color=color_acento,
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor=CHAT_BG,
        content=ft.Container(
            width=520,
            height=420,
            bgcolor=CHAT_PANEL,
            border_radius=14,
            padding=16,
            content=ft.Column(
                [
                    mensajes,
                    ft.Row(
                        [
                            campo,
                            ft.IconButton(
                                icon=ft.Icons.SEND,
                                icon_color=color_acento,
                                on_click=enviar_mensaje,
                            ),
                        ]
                    ),
                ],
                expand=True,
            ),
        ),
        actions=[
            ft.TextButton(
                "Cerrar",
                style=ft.ButtonStyle(color=CHAT_USER),
                on_click=cerrar_chat,
            )
        ],
    )

    if hasattr(page, "show_dialog"):
        page.show_dialog(dialogo)
    else:
        page.dialog = dialogo
        dialogo.open = True
        page.update()


def crear_boton_chat(page, color_acento):
    ruta_imagen_chat = "assets/fotopanda4.png"
    if os.path.exists(ruta_imagen_chat):
        contenido_chat = ft.Image(
            src=ruta_imagen_chat,
            width=54,
            height=54,
            fit="contain",
        )
    else:
        contenido_chat = ft.Icon(
            ft.Icons.CHAT,
            color=ft.Colors.WHITE,
            size=30,
        )

    return ft.FloatingActionButton(
        content=contenido_chat,
        bgcolor=color_acento,
        elevation=8,
        highlight_elevation=12,
        on_click=lambda e: abrir_chat(page, color_acento, e),
        shape=ft.RoundedRectangleBorder(radius=50),
    )



