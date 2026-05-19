import os
import json
import urllib.error
import urllib.request
from functools import wraps

from flask import Flask, jsonify, request

from auth import crear_tabla, guardar_evaluacion, login_usuario, registrar_usuario
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
from services.chat_scope import es_mensaje_vitalmetrics, respuesta_fuera_de_tema


app = Flask(__name__)
crear_tabla()


def requiere_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        username = request.headers.get("X-Admin-Username")
        password = request.headers.get("X-Admin-Password")
        resultado = login_usuario(username, password)
        if not resultado.get("success") or resultado.get("role") != "admin":
            return jsonify({"success": False, "message": "Acceso admin requerido"}), 403
        return func(*args, **kwargs)

    return wrapper


def cargar_env_local():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lstrip("\ufeff")
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ[key] = value



cargar_env_local()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_FALLBACK_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
]

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

    cargar_env_local()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "Falta configurar el servicio del chat en el servidor."
        )

    modelos = []
    modelo_configurado = os.getenv("GROQ_MODEL", GROQ_MODEL)
    modelos_api = modelos_disponibles_groq(api_key)
    for model in [modelo_configurado, *modelos_api, *GROQ_FALLBACK_MODELS]:
        if model and model not in modelos:
            modelos.append(model)

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
        if resultado.get("status") == 403 and "1010" in detalle:
            errores_permiso.append(model)
            continue

        return f"El servicio del chat devolvio un error: {detalle}"

    return respuesta_local(mensaje)


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    resultado = registrar_usuario(
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    resultado = login_usuario(
        username=data.get("username"),
        password=data.get("password"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 401


@app.route("/chat", methods=["GET", "POST"])
def chat():
    cargar_env_local()
    if request.method == "GET":
        api_key = os.getenv("GROQ_API_KEY")
        modelos, modelos_error = consultar_modelos_groq(api_key) if api_key else ([], "")
        return jsonify(
            {
                "status": "ok",
                "message": "El endpoint /chat esta listo. Envia un POST con {'message': 'tu mensaje'}.",
                "chat_configured": bool(api_key),
            }
        )

    data = request.get_json(silent=True) or {}
    mensaje = data.get("message") or data.get("mensaje") or ""
    if not mensaje.strip():
        return jsonify({"response": "Escribe un mensaje para poder ayudarte."}), 400

    return jsonify({"response": responder_con_groq(mensaje)})


@app.route("/evaluations", methods=["POST"])
def evaluations():
    data = request.get_json(silent=True) or {}
    resultado = guardar_evaluacion(
        user_id=data.get("user_id"),
        edad=data.get("edad"),
        altura_cm=data.get("altura_cm"),
        peso_kg=data.get("peso_kg"),
        estrato=data.get("estrato"),
        actividad=data.get("actividad"),
        imc=data.get("imc"),
        nivel=data.get("nivel"),
        riesgo=data.get("riesgo"),
        genero=data.get("genero"),
        municipio=data.get("municipio"),
        actividad_minutos=data.get("actividad_minutos"),
        calidad_alimentacion=data.get("calidad_alimentacion"),
        comidas_dia=data.get("comidas_dia"),
        bebidas_azucaradas=data.get("bebidas_azucaradas"),
        horas_sueno=data.get("horas_sueno"),
        horas_pantalla=data.get("horas_pantalla"),
        antecedentes_familiares=data.get("antecedentes_familiares"),
        acceso_espacios=data.get("acceso_espacios"),
        riesgo_puntaje=data.get("riesgo_puntaje"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


@app.route("/admin/dashboard", methods=["GET"])
@requiere_admin
def admin_dashboard():
    return jsonify(obtener_dashboard())


@app.route("/admin/users", methods=["GET", "POST"])
@requiere_admin
def admin_users():
    if request.method == "GET":
        return jsonify({"success": True, "users": obtener_usuarios()})

    data = request.get_json(silent=True) or {}
    resultado = crear_usuario_admin(
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
        role=data.get("role", "user"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


@app.route("/admin/users/<int:user_id>", methods=["PUT", "DELETE"])
@requiere_admin
def admin_user_detail(user_id):
    if request.method == "DELETE":
        resultado = borrar_usuario(user_id)
        return jsonify(resultado), 200 if resultado["success"] else 404

    data = request.get_json(silent=True) or {}
    resultado = editar_usuario(
        user_id,
        username=data.get("username"),
        email=data.get("email"),
        role=data.get("role", "user"),
        password=data.get("password") or None,
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


@app.route("/admin/evaluations", methods=["GET"])
@requiere_admin
def admin_evaluations():
    return jsonify({"success": True, "evaluations": obtener_evaluaciones()})


@app.route("/admin/evaluations/<int:evaluation_id>", methods=["PUT", "DELETE"])
@requiere_admin
def admin_evaluation_detail(evaluation_id):
    if request.method == "DELETE":
        resultado = borrar_evaluacion(evaluation_id)
        return jsonify(resultado), 200 if resultado["success"] else 404

    data = request.get_json(silent=True) or {}
    resultado = editar_evaluacion(
        evaluation_id,
        edad=data.get("edad"),
        altura_cm=data.get("altura_cm"),
        peso_kg=data.get("peso_kg"),
        estrato=data.get("estrato"),
        actividad=data.get("actividad"),
        imc=data.get("imc"),
        nivel=data.get("nivel"),
        riesgo=data.get("riesgo"),
        actividad_minutos=data.get("actividad_minutos"),
        calidad_alimentacion=data.get("calidad_alimentacion"),
        comidas_dia=data.get("comidas_dia"),
        bebidas_azucaradas=data.get("bebidas_azucaradas"),
        horas_sueno=data.get("horas_sueno"),
        horas_pantalla=data.get("horas_pantalla"),
        antecedentes_familiares=data.get("antecedentes_familiares"),
        acceso_espacios=data.get("acceso_espacios"),
        riesgo_puntaje=data.get("riesgo_puntaje"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


if __name__ == "__main__":
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)





