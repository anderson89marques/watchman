import logging

from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from core.models import DomainHost, Usuario, Principal, DomainService


class BaseHandler(RequestHandler):
    @property
    def sched(self):
        return self.application.sched

    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_principals(self, user):
        usuario = self.db.query(Usuario).filter(Usuario.login == user.decode("utf8")).first()
        if usuario:
            return [p.nome for p in usuario.principals]


class MainHandler(BaseHandler):

    def on_finish(self):
        self.db.remove()

    def get_principal_roleadmin(self):
        """Verificando se o papel role_admin foi criado ou não"""

        role = self.db.query(Principal).filter(Principal.nome == "role_admin").first()
        if not role:
            return False

        return True

    def get_all_informations(self):
        dh = self.db.query(DomainHost).all()

        if not dh:
            return None

        return dh

    def get(self):  # Usar o LoadFile para saber quais e quantos hosts e serviços
        role = self.get_principal_roleadmin()  # verificar se o usuário admin aínda não foi criado
        if not role:
            self.redirect('/create_user/')
            return

        if not self.current_user:
            self.redirect('/login/')
            return

        hosts = self.get_all_informations()
        self.render('control.html', hosts=hosts, user=self.get_current_user().decode())


class EchoWebSocket(WebSocketHandler):
    clients = []

    def open(self):
        logging.info('WebSocket opened from %s', self.request.remote_ip)
        EchoWebSocket.clients.append(self)

    def on_message(self, message):
        logging.info('got message from %s: %s', self.request.remote_ip, message)
        for client in EchoWebSocket.clients:
            if client is self:
                continue
            client.write_message(message)

    def on_close(self):
        logging.info('WebSocket closed')
        EchoWebSocket.clients.remove(self)


class StartOrStopOrRemoveJOB(BaseHandler):
    def post(self):
        """De acordo com o parâmetro o job será removido do banco ou será parado, quer dizer removido apenas do sched"""

        req_arguments = self.request.body_arguments
        print("Requirements: {}".format(req_arguments))
        action, serv_name = req_arguments["action"][0].decode(), req_arguments["serv_name"][0].decode()

        d = self.db.query(DomainService).filter(DomainService.service_name == serv_name).first()

        if not d:
            self.write("Serviço não encontrado")

        if action == "Start":
            print("Start")
            self.sched.resume_job(serv_name)

        elif action == "Stop":
            print("Stop")
            self.sched.pause_job(serv_name)

        elif action == "Remove":
            print("Remove")

            # aqui vou precisar remover do arquivo de configuração
            # por enquanto opção está desabilitada
            # para remover o serviço basta remove-lo do service.yaml
            self.sched.remove_job(serv_name)

        self.write(action)


class CreateUser(BaseHandler):
    def create_user(self, login, senha):
        user = Usuario()
        user.login = login
        user.add_senha(senha)
        p = Principal()
        p.nome = 'role_admin'
        user.principals.append(p)

        self.db.add(user)
        self.db.add(p)
        self.db.commit()
        print(user)

    def get(self):
        print("Create_user")
        self.render('create_user.html')

    def post(self, *args, **kwargs):
        print("Post Create")
        req_arguments = self.request.body_arguments
        login = req_arguments['username'][0].decode("utf8")
        passwd = req_arguments['senha'][0].decode("utf8")
        confirm = req_arguments['confirma_senha'][0].decode("utf8")
        if passwd != confirm:
            self.write("passwd e confirm passwd estão diferentes")
        try:
            # criando o usuário e logando
            self.create_user(login, passwd)
            self.set_secure_cookie("user", login)
            self.redirect("/control/")
        except LoginException as l:
            print(l)
            self.write("Erro ao realizar login")


class LoginException(Exception):
    pass


class LoginHandler(BaseHandler):
    def get_user(self, login, senha):
        """Esse método retorna o usuário logado."""

        usuario = self.db.query(Usuario).filter(Usuario.login == login).first()
        if usuario.validate_senha(senha):
            return usuario
        else:
            raise LoginException("erro ao logar")

    def get(self):
        self.render('login.html')

    def post(self, *args, **kwargs):
        req_arguments = self.request.body_arguments
        login = req_arguments['username'][0].decode("utf8")
        passwd = req_arguments['senha'][0].decode("utf8")

        try:
            usuario = self.get_user(login, passwd)
            self.set_secure_cookie("user", login)
            self.redirect("/control/")
        except LoginException as l:
            print(l)
            self.write("Erro ao realizar login")
        print(usuario)


class LogoutHandler(BaseHandler):
    def get(self):
        print('Logout')
        self.clear_cookie('user')
        self.redirect("/login/")

    def post(self):
        print("Chamado quando o usuário sai da página")
        print(self.current_user)
        self.redirect("/logout/")
