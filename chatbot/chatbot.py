import requests

SERVER_URL = "http://127.0.0.1:5000/chat"


def enviar_mensaje_al_servidor(mensaje_usuario, id_usuario):

    try:
        datos = {
            "mensaje": mensaje_usuario,
            "id_usuario": id_usuario
        }

        respuesta = requests.post(SERVER_URL, json=datos)

        if respuesta.status_code == 200:
            return respuesta.json()["response"]

        return "Error al conectar con el servidor."

    except Exception as e:
        return f"No se pudo conectar: {e}"