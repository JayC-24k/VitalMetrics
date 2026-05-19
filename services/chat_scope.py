import unicodedata


TEMAS_VITALMETRICS = (
    "vitalmetrics",
    "imc",
    "indice de masa corporal",
    "peso",
    "altura",
    "obesidad",
    "sobrepeso",
    "bajo peso",
    "actividad fisica",
    "ejercicio",
    "sedentarismo",
    "salud",
    "riesgo",
    "riesgos",
    "prevencion",
    "enfermedades cronicas",
    "ecnt",
    "diabetes",
    "hipertension",
    "cardiovascular",
    "estrato",
    "socioeconomico",
    "alimentacion",
    "habitos",
    "sueno",
    "pantalla",
    "cuestionario",
    "evaluacion",
)

SALUDOS = ("hola", "buenas", "buenos dias", "buenas tardes", "buenas noches")


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    return texto.lower().strip()


def es_mensaje_vitalmetrics(mensaje):
    texto = normalizar_texto(mensaje)
    if not texto:
        return False
    if texto in SALUDOS:
        return True
    return any(tema in texto for tema in TEMAS_VITALMETRICS)


def respuesta_fuera_de_tema():
    return (
        "Solo puedo responder preguntas relacionadas con VitalMetrics: IMC, "
        "actividad fisica, estrato socioeconomico, habitos de salud, prevencion "
        "y riesgo de enfermedades cronicas no transmisibles."
    )
