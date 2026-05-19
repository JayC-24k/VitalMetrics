class SessionManager:

    def __init__(self):

        self.usuario_logueado = False
        self.usuario = None

    def login(self, user):

        self.usuario_logueado = True
        self.usuario = user

    def logout(self):

        self.usuario_logueado = False
        self.usuario = None