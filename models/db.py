import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "usuarios.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_db():
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columnas = {row[1] for row in cursor.execute("PRAGMA table_info(users)")}
        if "email" not in columnas:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "created_at" not in columnas:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
        if "role" not in columnas:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        cursor.execute(
            "UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at = ''"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                genero TEXT,
                municipio TEXT,
                edad INTEGER NOT NULL,
                altura_cm REAL NOT NULL,
                peso_kg REAL NOT NULL,
                estrato INTEGER NOT NULL,
                actividad TEXT NOT NULL,
                actividad_minutos INTEGER,
                calidad_alimentacion TEXT,
                comidas_dia INTEGER,
                bebidas_azucaradas TEXT,
                horas_sueno REAL,
                horas_pantalla REAL,
                antecedentes_familiares TEXT,
                acceso_espacios TEXT,
                imc REAL NOT NULL,
                nivel TEXT NOT NULL,
                riesgo_puntaje INTEGER,
                riesgo TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        columnas_eval = {row[1] for row in cursor.execute("PRAGMA table_info(evaluations)")}
        nuevas_columnas = {
            "genero": "TEXT",
            "municipio": "TEXT",
            "actividad_minutos": "INTEGER",
            "calidad_alimentacion": "TEXT",
            "comidas_dia": "INTEGER",
            "bebidas_azucaradas": "TEXT",
            "horas_sueno": "REAL",
            "horas_pantalla": "REAL",
            "antecedentes_familiares": "TEXT",
            "acceso_espacios": "TEXT",
            "riesgo_puntaje": "INTEGER",
        }
        for columna, tipo in nuevas_columnas.items():
            if columna not in columnas_eval:
                cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {columna} {tipo}")
        conn.commit()
