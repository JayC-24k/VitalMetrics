import json
import os
import urllib.error
import urllib.request

from config import load_local_env
from services.chat_scope import es_mensaje_vitalmetrics, respuesta_fuera_de_tema

load_local_env()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
GROQ_FALLBACK_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]
GROQ_MODEL = os.getenv("GROQ_MODEL", GROQ_FALLBACK_MODELS[0])

GROQ_HEADERS_BASE = {
    "User-Agent": "VitalMetrics/1.0",
    "Accept": "application/json",
}

def consultar_modelos_groq(api_key):
    models_request = urllib.request.Request(
        GROQ_MODELS_URL,
        headers={
            **GROQ_HEADERS_BASE,
            "Authorization": f"Bearer {api_key}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(models_request, timeout=20) as respuesta:
            data = json.loads(respuesta.read().decode("utf-8"))
        modelos = [
            item.get("id")
            for item in data.get("data", [])
            if item.get("id")
        ]
        return modelos, ""
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="ignore")
        return [], f"HTTP {exc.code}: {detalle}"
    except Exception as exc:
        return [], str(exc)


def modelos_disponibles_groq(api_key):
    modelos, _ = consultar_modelos_groq(api_key)
    return modelos


def respuesta_local(mensaje):
    texto = mensaje.lower()
    if "imc" in texto:
        return (
            "Puedo ayudarte con IMC. Se calcula como peso / altura^2, usando la "
            "altura en metros. En VitalMetrics guardamos edad, altura, peso, "
            "estrato y actividad fisica para estimar un riesgo inicial. Esto no "
            "reemplaza una valoracion medica."
        )
    if "actividad" in texto or "ejercicio" in texto:
        return (
            "Para mejorar el perfil de riesgo, una meta inicial razonable es sumar "
            "actividad fisica de forma progresiva: caminar, bicicleta suave o rutinas "
            "cortas 3 a 4 veces por semana, segun tu condicion."
        )
    if "riesgo" in texto or "salud" in texto:
        return (
            "El riesgo se estima combinando IMC, actividad fisica y estrato. Si el "
            "resultado sale alto, lo ideal es revisar habitos y consultar a un "
            "profesional de salud para una orientacion completa."
        )
    return (
        "Estoy funcionando en modo local porque el servicio externo no esta disponible "
        "por el momento. Puedo orientarte sobre IMC, actividad fisica y riesgo "
        "preventivo mientras se habilita el servicio externo."
    )


def pedir_a_groq(api_key, mensaje, model):
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el asistente de VitalMetrics. Responde en espanol, "
                    "con tono claro y amable. Solo puedes responder temas de "
                    "VitalMetrics: IMC, actividad fisica, estrato socioeconomico, "
                    "habitos de salud, alimentacion, sedentarismo, sueno, "
                    "prevencion y riesgo de enfermedades cronicas no transmisibles. "
                    "Si el usuario pregunta otra cosa, rechaza brevemente y redirige "
                    "a esos temas. No resuelvas matematicas, programacion, cultura "
                    "general ni conversaciones fuera del alcance. No des diagnosticos "
                    "medicos definitivos; recomienda consultar a un profesional cuando "
                    "sea necesario."
                ),
            },
            {"role": "user", "content": mensaje},
        ],
        "temperature": 0.6,
        "max_tokens": 500,
    }

    request_data = json.dumps(payload).encode("utf-8")
    groq_request = urllib.request.Request(
        GROQ_API_URL,
        data=request_data,
        headers={
            **GROQ_HEADERS_BASE,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(groq_request, timeout=30) as respuesta:
            data = json.loads(respuesta.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="ignore")
        return {"error": True, "status": exc.code, "detail": detalle}
    except urllib.error.URLError as exc:
        return {"error": True, "status": None, "detail": f"No pude conectar con el servicio del chat: {exc}"}
    except (KeyError, IndexError, TypeError):
        return {"error": True, "status": None, "detail": "El servicio del chat respondio con un formato inesperado."}


def responder_con_groq(mensaje):
    if not es_mensaje_vitalmetrics(mensaje):
        return respuesta_fuera_de_tema()

    load_local_env()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "Falta configurar el servicio del chat en el servidor."
        )

    modelos_disponibles = modelos_disponibles_groq(api_key)
    modelo_configurado = os.getenv("GROQ_MODEL", GROQ_MODEL)
    candidatos = [modelo_configurado, *GROQ_FALLBACK_MODELS]
    if modelos_disponibles:
        modelos = []
        for model in candidatos:
            if model in modelos_disponibles and model not in modelos:
                modelos.append(model)
    else:
        modelos = list(dict.fromkeys(model for model in candidatos if model))

    if not modelos:
        return "La clave de Groq no tiene acceso a un modelo de chat compatible."

    errores_permiso = []
    ultimo_error = ""
    for model in modelos:
        resultado = pedir_a_groq(api_key, mensaje, model)
        if isinstance(resultado, str):
            if not es_mensaje_vitalmetrics(resultado):
                return respuesta_fuera_de_tema()
            return resultado

        detalle = resultado.get("detail", "")
        ultimo_error = detalle
        if resultado.get("status") == 403 and any(
            codigo in detalle.lower()
            for codigo in (
                "1010",
                "model_permission_blocked_project",
                "not authorized to use",
                "permission denied",
            )
        ):
            errores_permiso.append(model)
            continue
        if resultado.get("status") == 400 and any(
            codigo in detalle.lower()
            for codigo in ("model_not_found", "model_decommissioned", "model is not available")
        ):
            errores_permiso.append(model)
            continue

        return f"El servicio del chat devolvio un error: {detalle}"

    return respuesta_local(mensaje)
