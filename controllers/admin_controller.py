from models.evaluation_model import (
    actualizar_evaluacion,
    eliminar_evaluacion,
    estadisticas_dashboard,
    listar_evaluaciones,
)
from models.user_model import (
    actualizar_usuario,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
)


def obtener_dashboard():
    return estadisticas_dashboard()


def obtener_usuarios():
    return listar_usuarios()


def crear_usuario_admin(username, email, password, role="user"):
    return crear_usuario(username=username, email=email, password=password, role=role)


def editar_usuario(user_id, username, email, role, password=None):
    return actualizar_usuario(user_id, username=username, email=email, role=role, password=password)


def borrar_usuario(user_id, usuario_actual_id=None):
    if usuario_actual_id and int(user_id) == int(usuario_actual_id):
        return {"success": False, "message": "No puedes eliminar tu propia cuenta activa"}
    return eliminar_usuario(user_id)


def obtener_evaluaciones():
    return listar_evaluaciones()


def editar_evaluacion(
    evaluation_id,
    edad,
    altura_cm,
    peso_kg,
    estrato,
    actividad,
    imc,
    nivel,
    riesgo,
    actividad_minutos=None,
    calidad_alimentacion=None,
    comidas_dia=None,
    bebidas_azucaradas=None,
    horas_sueno=None,
    horas_pantalla=None,
    antecedentes_familiares=None,
    acceso_espacios=None,
    riesgo_puntaje=None,
):
    return actualizar_evaluacion(
        evaluation_id,
        edad,
        altura_cm,
        peso_kg,
        estrato,
        actividad,
        imc,
        nivel,
        riesgo,
        actividad_minutos=actividad_minutos,
        calidad_alimentacion=calidad_alimentacion,
        comidas_dia=comidas_dia,
        bebidas_azucaradas=bebidas_azucaradas,
        horas_sueno=horas_sueno,
        horas_pantalla=horas_pantalla,
        antecedentes_familiares=antecedentes_familiares,
        acceso_espacios=acceso_espacios,
        riesgo_puntaje=riesgo_puntaje,
    )


def borrar_evaluacion(evaluation_id):
    return eliminar_evaluacion(evaluation_id)
