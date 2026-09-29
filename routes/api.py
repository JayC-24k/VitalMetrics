import os
from functools import wraps
from flask import Blueprint, jsonify, request
from auth import guardar_evaluacion, login_usuario, registrar_usuario
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
from services.chat_service import consultar_modelos_groq, modelos_disponibles_groq, responder_con_groq

api = Blueprint('api', __name__)

@api.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    resultado = registrar_usuario(
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
    )
    return jsonify(resultado), 200 if resultado["success"] else 400




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


@api.route("/chat", methods=["GET", "POST"])
def chat():
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


@api.route("/evaluations", methods=["POST"])
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


@api.route("/admin/dashboard", methods=["GET"])
@requiere_admin
def admin_dashboard():
    return jsonify(obtener_dashboard())


@api.route("/admin/users", methods=["GET", "POST"])
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


@api.route("/admin/users/<int:user_id>", methods=["PUT", "DELETE"])
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


@api.route("/admin/evaluations", methods=["GET"])
@requiere_admin
def admin_evaluations():
    return jsonify({"success": True, "evaluations": obtener_evaluaciones()})


@api.route("/admin/evaluations/<int:evaluation_id>", methods=["PUT", "DELETE"])
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
