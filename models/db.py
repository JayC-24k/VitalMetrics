import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "usuarios.db"


def _load_local_env():
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


_load_local_env()
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()


class HybridRow(dict):
    """MySQL result row that supports both row['column'] and row[0]."""

    def __init__(self, values):
        super().__init__(values)
        self._values = tuple(values.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class MySQLCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("?", "%s")
        self._cursor.execute(query, params or ())
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return HybridRow(row) if row is not None else None

    def fetchall(self):
        return [HybridRow(row) for row in self._cursor.fetchall()]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class MySQLConnection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        import pymysql

        return MySQLCursor(self._connection.cursor(pymysql.cursors.DictCursor))

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.rollback()
        self.close()


def conectar():
    if DB_ENGINE in {"mysql", "mariadb"}:
        import pymysql

        options = {
            "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "vitalmetrics"),
            "charset": "utf8mb4",
            "autocommit": False,
        }
        return MySQLConnection(pymysql.connect(**options))
    if DB_ENGINE != "sqlite":
        raise RuntimeError("DB_ENGINE debe ser 'sqlite' o 'mysql'.")
    return sqlite3.connect(DB_PATH)


def _inicializar_mysql(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(191) NOT NULL UNIQUE,
            email VARCHAR(255) NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            genero VARCHAR(80) NULL,
            municipio VARCHAR(191) NULL,
            edad INT NOT NULL,
            altura_cm DOUBLE NOT NULL,
            peso_kg DOUBLE NOT NULL,
            estrato INT NOT NULL,
            actividad VARCHAR(100) NOT NULL,
            actividad_minutos INT NULL,
            calidad_alimentacion VARCHAR(40) NULL,
            comidas_dia INT NULL,
            bebidas_azucaradas VARCHAR(80) NULL,
            horas_sueno DOUBLE NULL,
            horas_pantalla DOUBLE NULL,
            antecedentes_familiares VARCHAR(80) NULL,
            acceso_espacios VARCHAR(80) NULL,
            imc DOUBLE NOT NULL,
            nivel VARCHAR(80) NOT NULL,
            riesgo_puntaje INT NULL,
            riesgo VARCHAR(40) NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_evaluations_user_id (user_id),
            CONSTRAINT fk_evaluations_user FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    columnas_eval = {row["Field"] for row in cursor.execute("SHOW COLUMNS FROM evaluations").fetchall()}
    nuevos_campos = {
        "genero": "VARCHAR(80) NULL",
        "municipio": "VARCHAR(191) NULL",
        "actividad_minutos": "INT NULL",
        "calidad_alimentacion": "VARCHAR(40) NULL",
        "comidas_dia": "INT NULL",
        "bebidas_azucaradas": "VARCHAR(80) NULL",
        "horas_sueno": "DOUBLE NULL",
        "horas_pantalla": "DOUBLE NULL",
        "antecedentes_familiares": "VARCHAR(80) NULL",
        "acceso_espacios": "VARCHAR(80) NULL",
        "riesgo_puntaje": "INT NULL",
    }
    for columna, tipo in nuevos_campos.items():
        if columna not in columnas_eval:
            cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {columna} {tipo}")
    columnas_users = {row["Field"] for row in cursor.execute("SHOW COLUMNS FROM users").fetchall()}
    if "email" not in columnas_users:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL")
    if "created_at" not in columnas_users:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP")
    if "role" not in columnas_users:
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
    cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    conn.commit()


def inicializar_db():
    if DB_ENGINE in {"mysql", "mariadb"}:
        with conectar() as conn:
            _inicializar_mysql(conn)
        return

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
        cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at = ''")
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
            "genero": "TEXT", "municipio": "TEXT", "actividad_minutos": "INTEGER",
            "calidad_alimentacion": "TEXT", "comidas_dia": "INTEGER",
            "bebidas_azucaradas": "TEXT", "horas_sueno": "REAL", "horas_pantalla": "REAL",
            "antecedentes_familiares": "TEXT", "acceso_espacios": "TEXT", "riesgo_puntaje": "INTEGER",
        }
        for columna, tipo in nuevas_columnas.items():
            if columna not in columnas_eval:
                cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {columna} {tipo}")
        conn.commit()


def es_integrity_error(error):
    if isinstance(error, sqlite3.IntegrityError):
        return True
    try:
        import pymysql

        return isinstance(error, pymysql.err.IntegrityError)
    except ImportError:
        return False
