import os
from datetime import datetime

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from auth import crear_tabla
from config import load_local_env
from routes.api import api
from routes.web import web


def create_app():
    load_local_env()
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
    app.secret_key = os.getenv('SECRET_KEY') or os.urandom(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    app.context_processor(lambda: {'now_year': datetime.now().year})
    app.register_blueprint(web)
    app.register_blueprint(api)
    crear_tabla()
    return app


app = create_app()


if __name__ == '__main__':
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)
