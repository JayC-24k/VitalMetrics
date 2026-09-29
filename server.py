import os
import json
import urllib.error
import urllib.request
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

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
from models.user_model import obtener_usuario
from services.risk_service import calcular_riesgo_integral, clasificar_imc


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.context_processor(lambda: {"now_year": __import__("datetime").datetime.now().year})
crear_tabla()


def usuario_actual():
    user_id = session.get("user_id")
    return obtener_usuario(user_id) if user_id else None


def requiere_sesion_admin():
    if not session.get("user_id"):
        flash("Inicia sesión para continuar.", "warning")
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Esta sección requiere una cuenta administradora.", "danger")
        return redirect(url_for("inicio"))
    return None


@app.route("/")
def inicio():
    return render_template("home.html", usuario=usuario_actual())


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        resultado = registrar_usuario(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
        )
        if resultado.get("success"):
            session.update(user_id=resultado["user_id"], username=resultado["username"], role=resultado["role"])
            flash("Tu cuenta quedó creada.", "success")
            return redirect(url_for("inicio"))
        flash(resultado.get("message", "No se pudo crear la cuenta."), "danger")
    return render_template("auth.html", modo="registro", usuario=usuario_actual())


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("inicio"))


@app.route("/evaluacion", methods=["GET", "POST"])
def pagina_evaluacion():
    usuario = usuario_actual()
    if not usuario:
        flash("Inicia sesión para completar y guardar tu evaluación.", "warning")
        return redirect(url_for("login", next=url_for("pagina_evaluacion")))
    resultado = None
    if request.method == "POST":
        try:
            def requerido(nombre):
                valor = (request.form.get(nombre) or "").strip()
                if not valor:
                    raise ValueError(f"Completa el campo {nombre.replace('_', ' ')}.")
                return valor

            edad = int(requerido("edad"))
            genero = requerido("genero")
            municipio = requerido("municipio")
            altura = float(requerido("altura_cm").replace(",", "."))
            if altura <= 3:
                altura *= 100
            peso = float(requerido("peso_kg").replace(",", "."))
            estrato = int(requerido("estrato"))
            actividad = requerido("actividad")
            minutos = int(requerido("actividad_minutos"))
            alimentacion = requerido("calidad_alimentacion")
            comidas = int(requerido("comidas_dia"))
            bebidas = requerido("bebidas_azucaradas")
            sueno = float(requerido("horas_sueno").replace(",", "."))
            pantalla = float(requerido("horas_pantalla").replace(",", "."))
            antecedentes = requerido("antecedentes_familiares")
            espacios = requerido("acceso_espacios")
            if not 1 <= edad <= 120 or not 30 <= altura <= 250 or not 1 <= peso <= 400:
                raise ValueError("Verifica edad, altura y peso.")
            if not 1 <= estrato <= 6 or not 0 <= minutos <= 10080 or not 1 <= comidas <= 6:
                raise ValueError("Verifica estrato, actividad y comidas al día.")
            if not 0 <= sueno <= 24 or not 0 <= pantalla <= 24:
                raise ValueError("Las horas deben estar entre 0 y 24.")
            imc, nivel = clasificar_imc(peso, altura)
            puntaje, riesgo = calcular_riesgo_integral(
                imc, estrato, minutos, alimentacion, bebidas, sueno, pantalla, antecedentes, espacios
            )
            resultado = guardar_evaluacion(
                usuario["id"], edad, altura, peso, estrato, actividad, imc, nivel, riesgo,
                genero=genero, municipio=municipio, actividad_minutos=minutos,
                calidad_alimentacion=alimentacion, comidas_dia=comidas,
                bebidas_azucaradas=bebidas, horas_sueno=sueno, horas_pantalla=pantalla,
                antecedentes_familiares=antecedentes, acceso_espacios=espacios,
                riesgo_puntaje=puntaje,
            )
            if resultado.get("success"):
                resultado.update(imc=round(imc, 1), nivel=nivel, riesgo=riesgo, puntaje=puntaje)
        except (ValueError, TypeError):
            flash("Revisa los datos: todos los campos deben ser válidos.", "danger")
    return render_template("evaluation.html", usuario=usuario, resultado=resultado)


@app.route("/admin")
def pagina_admin():
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    return render_template(
        "admin.html", usuario=usuario_actual(), dashboard=obtener_dashboard(),
        usuarios=obtener_usuarios(), evaluaciones=obtener_evaluaciones(),
    )


@app.route("/admin/usuarios", methods=["POST"])
def admin_crear_usuario_web():
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = crear_usuario_admin(request.form.get("username"), request.form.get("email"), request.form.get("password"), request.form.get("role", "user"))
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("pagina_admin") + "#usuarios")


@app.route("/admin/usuarios/<int:user_id>/eliminar", methods=["POST"])
def admin_eliminar_usuario_web(user_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = borrar_usuario(user_id, session.get("user_id"))
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("pagina_admin") + "#usuarios")


@app.route("/admin/usuarios/<int:user_id>/editar", methods=["POST"])
def admin_editar_usuario_web(user_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    rol = request.form.get("role", "user")
    if user_id == session.get("user_id") and rol != "admin":
        flash("No puedes quitarte el rol de administrador durante esta sesión.", "danger")
        return redirect(url_for("pagina_admin") + "#usuarios")
    resultado = editar_usuario(
        user_id, request.form.get("username"), request.form.get("email"), rol,
        request.form.get("password") or None,
    )
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("pagina_admin") + "#usuarios")


@app.route("/admin/evaluaciones/<int:evaluation_id>/eliminar", methods=["POST"])
def admin_eliminar_evaluacion_web(evaluation_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = borrar_evaluacion(evaluation_id)
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("pagina_admin") + "#evaluaciones")


@app.route("/admin/evaluaciones/<int:evaluation_id>/editar", methods=["POST"])
def admin_editar_evaluacion_web(evaluation_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    try:
        altura = float(request.form.get("altura_cm", "").replace(",", "."))
        peso = float(request.form.get("peso_kg", "").replace(",", "."))
        estrato = int(request.form.get("estrato", ""))
        minutos = int(request.form.get("actividad_minutos", ""))
        alimentacion = request.form.get("calidad_alimentacion", "")
        bebidas = request.form.get("bebidas_azucaradas", "")
        sueno = float(request.form.get("horas_sueno", "").replace(",", "."))
        pantalla = float(request.form.get("horas_pantalla", "").replace(",", "."))
        antecedentes = request.form.get("antecedentes_familiares", "")
        espacios = request.form.get("acceso_espacios", "")
        edad = int(request.form.get("edad", ""))
        comidas = int(request.form.get("comidas_dia", ""))
        if not 1 <= edad <= 120 or not 30 <= altura <= 250 or not 1 <= peso <= 400:
            raise ValueError("Edad, altura o peso fuera de rango.")
        if not 1 <= estrato <= 6 or not 0 <= minutos <= 10080 or not 1 <= comidas <= 6:
            raise ValueError("Estrato, actividad o comidas fuera de rango.")
        if not 0 <= sueno <= 24 or not 0 <= pantalla <= 24:
            raise ValueError("Horas fuera de rango.")
        imc, nivel = clasificar_imc(peso, altura)
        puntaje, riesgo = calcular_riesgo_integral(
            imc, estrato, minutos, alimentacion, bebidas, sueno, pantalla, antecedentes, espacios
        )
        resultado = editar_evaluacion(
            evaluation_id, edad, altura, peso, estrato,
            request.form.get("actividad", ""), imc, nivel, riesgo,
            actividad_minutos=minutos, calidad_alimentacion=alimentacion,
            comidas_dia=comidas, bebidas_azucaradas=bebidas,
            horas_sueno=sueno, horas_pantalla=pantalla,
            antecedentes_familiares=antecedentes, acceso_espacios=espacios,
            riesgo_puntaje=puntaje,
        )
    except (ValueError, TypeError):
        resultado = {"success": False, "message": "Revisa los campos numéricos de la evaluación."}
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("pagina_admin") + "#evaluaciones")


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

    cargar_env_local()
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


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    resultado = registrar_usuario(
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if usuario_actual():
            return redirect(url_for("inicio"))
        return render_template("auth.html", modo="login", usuario=None)
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form
    resultado = login_usuario(
        username=(request.form.get("username") if not request.is_json else data.get("username")),
        password=(request.form.get("password") if not request.is_json else data.get("password")),
    )
    if not request.is_json:
        if resultado.get("success"):
            session.update(user_id=resultado["user_id"], username=resultado["username"], role=resultado["role"])
            flash(f"Bienvenido, {resultado['username']}.", "success")
            destino = request.args.get("next", "")
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("inicio")
            return redirect(destino)
        flash(resultado.get("message", "No se pudo iniciar sesión."), "danger")
        return render_template("auth.html", modo="login", usuario=usuario_actual())
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





