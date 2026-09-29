import hashlib
import hmac
import os
from .db import conectar, es_integrity_error, inicializar_db


HASH_ITERATIONS = 260_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _sha256_legacy(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verificar_password(password, password_guardado):
    if not password_guardado:
        return False

    partes = password_guardado.split("$")
    if len(partes) == 4 and partes[0] == "pbkdf2_sha256":
        _, iterations, salt_hex, digest_hex = partes
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)

    return hmac.compare_digest(password_guardado, _sha256_legacy(password)) or hmac.compare_digest(
        password_guardado,
        password,
    )


def crear_usuario(username, password, email=None, role="user"):
    username = (username or "").strip()
    email = (email or "").strip() or None
    role = role if role in ("admin", "user") else "user"

    if not username or not password:
        return {"success": False, "message": "Completa todos los campos"}

    inicializar_db()
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password, role, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (username, email, hash_password(password), role),
            )
            conn.commit()
            return {
                "success": True,
                "message": "Cuenta creada",
                "user_id": cursor.lastrowid,
                "username": username,
                "role": role,
            }
    except Exception as exc:
        if es_integrity_error(exc):
            return {"success": False, "message": "Usuario ya existe"}
        raise


def asegurar_admin_inicial():
    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        username = os.getenv("ADMIN_USERNAME", "jaze")
        password = os.getenv("ADMIN_PASSWORD", "ysya.24k")
        email = os.getenv("ADMIN_EMAIL", "jaze@vitalmetrics.local")
        existe = cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existe:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin',
                    created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                WHERE username = ?
                """,
                (username,),
            )
            conn.commit()
            return

        try:
            cursor.execute(
                """
                INSERT INTO users (username, email, password, role, created_at)
                VALUES (?, ?, ?, 'admin', CURRENT_TIMESTAMP)
                """,
                (username, email, hash_password(password)),
            )
        except Exception as exc:
            if not es_integrity_error(exc):
                raise
        conn.commit()


def autenticar_usuario(username, password):
    username = (username or "").strip()

    if not username or not password:
        return {"success": False, "message": "Completa todos los campos"}

    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()

        if not user or not verificar_password(password, user[2]):
            return {"success": False, "message": "Credenciales incorrectas"}

        if not user[2].startswith("pbkdf2_sha256$"):
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(password), user[0]),
            )
            conn.commit()

        return {
            "success": True,
            "message": "Inicio de sesion correcto",
            "user_id": user[0],
            "username": user[1],
            "role": user[3] or "user",
        }


def listar_usuarios():
    inicializar_db()
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, u.role, u.created_at,
                   COUNT(e.id) AS evaluations_count
            FROM users u
            LEFT JOIN evaluations e ON e.user_id = u.id
            GROUP BY u.id
            ORDER BY u.id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def obtener_usuario(user_id):
    inicializar_db()
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def actualizar_usuario(user_id, username, email=None, role="user", password=None):
    username = (username or "").strip()
    email = (email or "").strip() or None
    role = role if role in ("admin", "user") else "user"

    if not user_id or not username:
        return {"success": False, "message": "El usuario necesita nombre"}

    inicializar_db()
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            if password:
                cursor.execute(
                    """
                    UPDATE users
                    SET username = ?, email = ?, role = ?, password = ?
                    WHERE id = ?
                    """,
                    (username, email, role, hash_password(password), user_id),
                )
            else:
                cursor.execute(
                    "UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
                    (username, email, role, user_id),
                )
            conn.commit()
            if cursor.rowcount == 0:
                return {"success": False, "message": "Usuario no encontrado"}
            return {"success": True, "message": "Usuario actualizado"}
    except Exception as exc:
        if es_integrity_error(exc):
            return {"success": False, "message": "Ese nombre de usuario ya existe"}
        raise


def eliminar_usuario(user_id):
    inicializar_db()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evaluations WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return {"success": False, "message": "Usuario no encontrado"}
        return {"success": True, "message": "Usuario eliminado"}
