from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from core.models import DomainService
from core.services import UserService
from core.services import Log


log = Log(__name__)


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
        return UserService.get_principals(self.db, user)


class MainHandler(BaseHandler):

    def on_finish(self):
        self.db.remove()

    def get(self):  # Usar o LoadFile para saber quais e quantos hosts e serviços
        role = UserService.get_principal_roleadmin(self.db)  # verificar se o usuário admin aínda não foi criado
        if not role:
            self.redirect('/create_user/')
            return

        if not self.current_user:
            self.redirect('/login/')
            return

        hosts = UserService.get_all_informations(self.db)
        self.render('control.html', hosts=hosts, user=self.get_current_user().decode())


class EchoWebSocket(WebSocketHandler):
    clients = []

    def open(self):
        log.info('WebSocket opened from %s' % self.request.remote_ip)
        EchoWebSocket.clients.append(self)

    def on_message(self, message):
        log.info('got message from %s: %s' % (self.request.remote_ip, message))
        for client in EchoWebSocket.clients:
            if client is self:
                continue
            client.write_message(message)

    def on_close(self):
        log.info('WebSocket closed')
        EchoWebSocket.clients.remove(self)


class StartOrStopOrRemoveJOB(BaseHandler):
    def post(self):
        """De acordo com o parâmetro o job será removido do banco ou será parado, quer dizer removido apenas do sched"""

        req_arguments = self.request.body_arguments
        log.info("Requirements: {}".format(req_arguments))
        action, serv_name = req_arguments["action"][0].decode(), req_arguments["serv_name"][0].decode()

        d = self.db.query(DomainService).filter(DomainService.service_name == serv_name).first()

        if not d:
            self.write("Serviço não encontrado")

        if action == "Start":
            log.info("Start")
            self.sched.resume_job(serv_name)

        elif action == "Stop":
            log.info("Stop")
            self.sched.pause_job(serv_name)

        elif action == "Remove":
            log.info("Remove")

            # aqui vou precisar remover do arquivo de configuração
            # por enquanto opção está desabilitada
            # para remover o serviço basta remove-lo do service.yaml
            # self.sched.remove_job(serv_name)

        self.write(action)


class CreateUser(BaseHandler):
    def get(self):
        log.info("Create_user")
        self.render('create_user.html')

    def post(self, *args, **kwargs):
        log.info("Post Create")
        req_arguments = self.request.body_arguments
        login, passwd, confirm = UserService.extraxt_params_content(req_arguments)

        if passwd != confirm:
            self.write("passwd e confirm passwd estão diferentes")
        try:
            # criando o usuário e logando
            UserService.create_user(self.db, login, passwd)
            self.set_secure_cookie("user", login)
            self.redirect("/control/")
        except Exception as l:
            log.info(l)
            self.write("Erro ao realizar login")


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self, *args, **kwargs):
        req_arguments = self.request.body_arguments
        login = req_arguments['username'][0].decode("utf8")
        passwd = req_arguments['senha'][0].decode("utf8")

        try:
            usuario = UserService.get_user(self.db, login, passwd)
            self.set_secure_cookie("user", login)
            self.redirect("/control/")
        except Exception as l:
            log.info(l)
            self.write("Erro ao realizar login")


class LogoutHandler(BaseHandler):
    def get(self):
        log.info('Logout')
        self.clear_cookie('user')
        self.redirect("/login/")

    def post(self):
        log.info("Saindo da pagina!")
        self.redirect("/logout/")
