import hashlib
from urllib.parse import urlencode

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from auth import guardar_evaluacion, login_usuario
from controllers.admin_controller import (borrar_evaluacion, borrar_usuario, crear_usuario_admin, editar_evaluacion, editar_usuario, obtener_dashboard, obtener_evaluaciones, obtener_usuarios)
from models.db import conectar
from models.user_model import obtener_usuario
from services.risk_service import calcular_riesgo_integral, clasificar_imc

web = Blueprint('web', __name__)

def usuario_actual():
    user_id = session.get("user_id")
    return obtener_usuario(user_id) if user_id else None


def requiere_sesion_admin():
    if not session.get("user_id"):
        flash("Inicia sesión para continuar.", "warning")
        return redirect(url_for("web.login"))
    if session.get("role") != "admin":
        flash("Esta sección requiere una cuenta administradora.", "danger")
        return redirect(url_for("web.inicio"))
    return None


@web.route("/")
def inicio():
    return render_template("home.html", usuario=usuario_actual())


@web.route("/signup")
def signup():
    return redirect(f"{request.script_root}/registrar.php")


@web.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("web.inicio"))


@web.route("/auth/php-session", methods=["POST"])
def php_session():
    ticket = request.form.get("ticket", "")
    if len(ticket) != 64:
        return redirect(url_for("web.login"))

    token_hash = hashlib.sha256(ticket.encode("ascii", errors="ignore")).hexdigest()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, redirect_to FROM php_login_tickets "
            "WHERE token_hash = ? AND expires_at > CURRENT_TIMESTAMP",
            (token_hash,),
        )
        ticket_row = cursor.fetchone()
        if not ticket_row:
            return redirect(url_for("web.login"))
        cursor.execute(
            "DELETE FROM php_login_tickets "
            "WHERE token_hash = ? AND expires_at > CURRENT_TIMESTAMP",
            (token_hash,),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            return redirect(url_for("web.login"))
        conn.commit()

    usuario = obtener_usuario(ticket_row["user_id"])
    if not usuario:
        return redirect(url_for("web.login"))

    destino = ticket_row["redirect_to"] or url_for("web.inicio")
    base = request.script_root.rstrip("/")
    if not destino.startswith("/") or destino.startswith("//") or (base and destino != base and not destino.startswith(base + "/")):
        destino = url_for("web.inicio")
    session.clear()
    session.update(user_id=usuario["id"], username=usuario["username"], role=usuario["role"])
    return redirect(destino)


@web.route("/evaluacion", methods=["GET", "POST"])
def pagina_evaluacion():
    usuario = usuario_actual()
    if not usuario:
        flash("Inicia sesión para completar y guardar tu evaluación.", "warning")
        return redirect(url_for("web.login", next=url_for("web.pagina_evaluacion")))
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


@web.route("/admin")
def pagina_admin():
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    return render_template(
        "admin.html", usuario=usuario_actual(), dashboard=obtener_dashboard(),
        usuarios=obtener_usuarios(), evaluaciones=obtener_evaluaciones(),
    )


@web.route("/admin/usuarios", methods=["POST"])
def admin_crear_usuario_web():
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = crear_usuario_admin(request.form.get("username"), request.form.get("email"), request.form.get("password"), request.form.get("role", "user"))
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("web.pagina_admin") + "#usuarios")


@web.route("/admin/usuarios/<int:user_id>/eliminar", methods=["POST"])
def admin_eliminar_usuario_web(user_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = borrar_usuario(user_id, session.get("user_id"))
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("web.pagina_admin") + "#usuarios")


@web.route("/admin/usuarios/<int:user_id>/editar", methods=["POST"])
def admin_editar_usuario_web(user_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    rol = request.form.get("role", "user")
    if user_id == session.get("user_id") and rol != "admin":
        flash("No puedes quitarte el rol de administrador durante esta sesión.", "danger")
        return redirect(url_for("web.pagina_admin") + "#usuarios")
    resultado = editar_usuario(
        user_id, request.form.get("username"), request.form.get("email"), rol,
        request.form.get("password") or None,
    )
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("web.pagina_admin") + "#usuarios")


@web.route("/admin/evaluaciones/<int:evaluation_id>/eliminar", methods=["POST"])
def admin_eliminar_evaluacion_web(evaluation_id):
    rechazo = requiere_sesion_admin()
    if rechazo:
        return rechazo
    resultado = borrar_evaluacion(evaluation_id)
    flash(resultado.get("message", "Listo."), "success" if resultado.get("success") else "danger")
    return redirect(url_for("web.pagina_admin") + "#evaluaciones")


@web.route("/admin/evaluaciones/<int:evaluation_id>/editar", methods=["POST"])
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
    return redirect(url_for("web.pagina_admin") + "#evaluaciones")




@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if usuario_actual():
            return redirect(url_for("web.inicio"))
        destino = f"{request.script_root}/login.php"
        siguiente = request.args.get("next", "")
        if siguiente.startswith("/") and not siguiente.startswith("//"):
            destino += "?" + urlencode({"next": siguiente})
        return redirect(destino)
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form
    resultado = login_usuario(
        username=(request.form.get("username") if not request.is_json else data.get("username")),
        password=(request.form.get("password") if not request.is_json else data.get("password")),
    )
    if not request.is_json:
        return redirect(f"{request.script_root}/login.php")
    return jsonify(resultado), 200 if resultado["success"] else 401
