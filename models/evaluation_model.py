import sqlite3

from .db import conectar, inicializar_db


def crear_evaluacion(
    user_id,
    edad,
    altura_cm,
    peso_kg,
    estrato,
    actividad,
    imc,
    nivel,
    riesgo,
    genero=None,
    municipio=None,
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
    if not user_id:
        return {"success": False, "message": "Debes iniciar sesion"}

    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evaluations (
                user_id, genero, municipio, edad, altura_cm, peso_kg, estrato,
                actividad, actividad_minutos, calidad_alimentacion, comidas_dia,
                bebidas_azucaradas, horas_sueno, horas_pantalla,
                antecedentes_familiares, acceso_espacios, imc, nivel,
                riesgo_puntaje, riesgo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                genero,
                municipio,
                int(edad),
                float(altura_cm),
                float(peso_kg),
                int(estrato),
                actividad,
                int(actividad_minutos or 0),
                calidad_alimentacion,
                int(comidas_dia or 0),
                bebidas_azucaradas,
                float(horas_sueno or 0),
                float(horas_pantalla or 0),
                antecedentes_familiares,
                acceso_espacios,
                float(imc),
                nivel,
                int(riesgo_puntaje or 0),
                riesgo,
            ),
        )
        conn.commit()
        return {
            "success": True,
            "message": "Evaluacion guardada",
            "evaluation_id": cursor.lastrowid,
        }


def listar_evaluaciones():
    inicializar_db()
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.id, e.user_id, u.username, e.genero, e.municipio, e.edad,
                   e.altura_cm, e.peso_kg, e.estrato, e.actividad,
                   e.actividad_minutos, e.calidad_alimentacion, e.comidas_dia,
                   e.bebidas_azucaradas, e.horas_sueno, e.horas_pantalla,
                   e.antecedentes_familiares, e.acceso_espacios, e.imc, e.nivel,
                   e.riesgo_puntaje, e.riesgo, e.created_at
            FROM evaluations e
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY e.id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def actualizar_evaluacion(
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
    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE evaluations
            SET edad = ?, altura_cm = ?, peso_kg = ?, estrato = ?,
                actividad = ?, actividad_minutos = ?, calidad_alimentacion = ?,
                comidas_dia = ?, bebidas_azucaradas = ?, horas_sueno = ?,
                horas_pantalla = ?, antecedentes_familiares = ?,
                acceso_espacios = ?, imc = ?, nivel = ?, riesgo_puntaje = ?,
                riesgo = ?
            WHERE id = ?
            """,
            (
                int(edad),
                float(altura_cm),
                float(peso_kg),
                int(estrato),
                actividad,
                int(actividad_minutos or 0),
                calidad_alimentacion,
                int(comidas_dia or 0),
                bebidas_azucaradas,
                float(horas_sueno or 0),
                float(horas_pantalla or 0),
                antecedentes_familiares,
                acceso_espacios,
                float(imc),
                nivel,
                int(riesgo_puntaje or 0),
                riesgo,
                evaluation_id,
            ),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return {"success": False, "message": "Evaluacion no encontrada"}
        return {"success": True, "message": "Evaluacion actualizada"}


def eliminar_evaluacion(evaluation_id):
    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return {"success": False, "message": "Evaluacion no encontrada"}
        return {"success": True, "message": "Evaluacion eliminada"}


def estadisticas_dashboard():
    inicializar_db()
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        usuarios = cursor.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        evaluaciones = cursor.execute("SELECT COUNT(*) AS total FROM evaluations").fetchone()["total"]
        riesgo_alto = cursor.execute(
            "SELECT COUNT(*) AS total FROM evaluations WHERE riesgo = 'ALTO'"
        ).fetchone()["total"]
        promedio_imc = cursor.execute("SELECT AVG(imc) AS promedio FROM evaluations").fetchone()["promedio"]
        por_riesgo = cursor.execute(
            "SELECT riesgo, COUNT(*) AS total FROM evaluations GROUP BY riesgo ORDER BY total DESC"
        ).fetchall()
        recientes = cursor.execute(
            """
            SELECT e.id, u.username, e.imc, e.riesgo, e.created_at
            FROM evaluations e
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY e.id DESC
            LIMIT 5
            """
        ).fetchall()

        return {
            "usuarios": usuarios,
            "evaluaciones": evaluaciones,
            "riesgo_alto": riesgo_alto,
            "promedio_imc": round(promedio_imc or 0, 1),
            "por_riesgo": [dict(row) for row in por_riesgo],
            "recientes": [dict(row) for row in recientes],
        }
