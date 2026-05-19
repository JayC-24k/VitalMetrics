import flet as ft

from auth import guardar_evaluacion
from services.risk_service import calcular_riesgo_integral, clasificar_imc


def crear_pagina_evaluacion(
    page,
    usuario_logueado,
    usuario_id,
    color_acento,
    color_texto,
):
    edad = ft.TextField(label="Edad", width=200, keyboard_type=ft.KeyboardType.NUMBER)
    genero = ft.Dropdown(
        label="Genero",
        options=[
            ft.dropdown.Option("Femenino"),
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Otro"),
            ft.dropdown.Option("Prefiero no decir"),
        ],
        width=220,
    )
    municipio = ft.TextField(label="Municipio", width=220)
    altura = ft.TextField(label="Altura (cm)", width=200, keyboard_type=ft.KeyboardType.NUMBER)
    peso = ft.TextField(label="Peso (kg)", width=200, keyboard_type=ft.KeyboardType.NUMBER)
    estrato = ft.Dropdown(
        label="Estrato",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 7)],
        width=200,
    )
    actividad = ft.Dropdown(
        label="Actividad fisica",
        options=[
            ft.dropdown.Option("Ninguna"),
            ft.dropdown.Option("1-2 veces/semana"),
            ft.dropdown.Option("3-4 veces/semana"),
            ft.dropdown.Option("5+ veces/semana"),
        ],
        width=250,
    )
    actividad_minutos = ft.TextField(
        label="Minutos de actividad por semana",
        width=250,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    calidad_alimentacion = ft.Dropdown(
        label="Calidad de alimentacion",
        options=[ft.dropdown.Option("Alta"), ft.dropdown.Option("Media"), ft.dropdown.Option("Baja")],
        width=250,
    )
    comidas_dia = ft.Dropdown(
        label="Comidas al dia",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 7)],
        width=200,
    )
    bebidas_azucaradas = ft.Dropdown(
        label="Bebidas azucaradas",
        options=[
            ft.dropdown.Option("Nunca"),
            ft.dropdown.Option("1-2 veces/semana"),
            ft.dropdown.Option("3-5 veces/semana"),
            ft.dropdown.Option("Diario"),
        ],
        width=250,
    )
    horas_sueno = ft.TextField(
        label="Horas de sueno por noche",
        width=230,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    horas_pantalla = ft.TextField(
        label="Horas de pantalla al dia",
        width=230,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    antecedentes_familiares = ft.Dropdown(
        label="Antecedentes familiares de ECNT",
        options=[ft.dropdown.Option("No"), ft.dropdown.Option("Si"), ft.dropdown.Option("No sabe")],
        width=280,
    )
    acceso_espacios = ft.Dropdown(
        label="Acceso a espacios para actividad fisica",
        options=[ft.dropdown.Option("Bueno"), ft.dropdown.Option("Limitado"), ft.dropdown.Option("No tiene")],
        width=300,
    )
    resultado_texto = ft.Text("", size=16)

    def calcular(e):
        if not usuario_logueado or not usuario_id:
            resultado_texto.value = "Inicia sesion para guardar tu evaluacion"
            resultado_texto.color = ft.Colors.RED
            page.update()
            return

        campos_requeridos = [
            edad.value,
            genero.value,
            municipio.value,
            altura.value,
            peso.value,
            estrato.value,
            actividad.value,
            actividad_minutos.value,
            calidad_alimentacion.value,
            comidas_dia.value,
            bebidas_azucaradas.value,
            horas_sueno.value,
            horas_pantalla.value,
            antecedentes_familiares.value,
            acceso_espacios.value,
        ]
        if not all(campos_requeridos):
            resultado_texto.value = "Completa todos los campos"
            resultado_texto.color = ft.Colors.RED
            page.update()
            return

        try:
            edad_num = int(edad.value)
            altura_num = float(altura.value)
            peso_num = float(peso.value)
            estrato_num = int(estrato.value)
            minutos_num = int(actividad_minutos.value)
            comidas_num = int(comidas_dia.value)
            sueno_num = float(horas_sueno.value)
            pantalla_num = float(horas_pantalla.value)
            imc, nivel = clasificar_imc(peso_num, altura_num)
            riesgo_puntaje, riesgo = calcular_riesgo_integral(
                imc,
                estrato_num,
                minutos_num,
                calidad_alimentacion.value,
                bebidas_azucaradas.value,
                sueno_num,
                pantalla_num,
                antecedentes_familiares.value,
                acceso_espacios.value,
            )
            guardado = guardar_evaluacion(
                usuario_id,
                edad_num,
                altura_num,
                peso_num,
                estrato_num,
                actividad.value,
                imc,
                nivel,
                riesgo,
                genero=genero.value,
                municipio=municipio.value,
                actividad_minutos=minutos_num,
                calidad_alimentacion=calidad_alimentacion.value,
                comidas_dia=comidas_num,
                bebidas_azucaradas=bebidas_azucaradas.value,
                horas_sueno=sueno_num,
                horas_pantalla=pantalla_num,
                antecedentes_familiares=antecedentes_familiares.value,
                acceso_espacios=acceso_espacios.value,
                riesgo_puntaje=riesgo_puntaje,
            )
            mensaje_guardado = (
                "Guardada en la base de datos"
                if guardado.get("success")
                else guardado.get("message", "No se pudo guardar")
            )
            resultado_texto.value = (
                f"IMC: {imc:.1f} ({nivel})\n"
                f"Puntaje de riesgo: {riesgo_puntaje}/19\n"
                f"Riesgo integral: {riesgo}\n"
                f"{mensaje_guardado}"
            )
            if riesgo == "ALTO":
                resultado_texto.color = ft.Colors.RED
            elif riesgo == "MODERADO":
                resultado_texto.color = ft.Colors.ORANGE
            else:
                resultado_texto.color = ft.Colors.GREEN
        except ValueError:
            resultado_texto.value = "Error en los datos"
            resultado_texto.color = ft.Colors.RED
        page.update()

    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text(
                "Evaluacion de salud",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=color_acento,
                font_family="Cakecafe",
            ),
            ft.Text(
                "Cuestionario preventivo basado en IMC, entorno socioeconomico, actividad fisica y habitos",
                size=16,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Text("Datos personales", size=20, weight=ft.FontWeight.BOLD, color=color_texto),
            ft.Row([edad, genero, municipio], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=12),
            ft.Text("Datos antropometricos y socioeconomicos", size=20, weight=ft.FontWeight.BOLD, color=color_texto),
            ft.Row([altura, peso, estrato], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=12),
            ft.Text("Actividad fisica y entorno", size=20, weight=ft.FontWeight.BOLD, color=color_texto),
            ft.Row([actividad, actividad_minutos, acceso_espacios], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=12),
            ft.Text("Habitos de salud", size=20, weight=ft.FontWeight.BOLD, color=color_texto),
            ft.Row([calidad_alimentacion, comidas_dia, bebidas_azucaradas], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=12),
            ft.Row([horas_sueno, horas_pantalla, antecedentes_familiares], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=12),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Button("Calcular riesgo", bgcolor=color_acento, color=ft.Colors.WHITE, on_click=calcular),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            resultado_texto,
        ],
    )
