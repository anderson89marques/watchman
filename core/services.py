import logging
from core.models import Usuario, Principal, DomainHost


class UserService:
    @staticmethod
    def extraxt_params_content(req_arguments):
        login = req_arguments['username'][0].decode("utf8")
        passwd = req_arguments['senha'][0].decode("utf8")
        confirm = req_arguments['confirma_senha'][0].decode("utf8")

        return login, passwd, confirm

    @staticmethod
    def create_user(db, login, passwd):
        user = Usuario()
        user.login = login
        user.add_passwd(passwd)
        p = Principal()
        p.nome = 'role_admin'
        user.principals.append(p)

        db.add(user)
        db.add(p)
        db.commit()

    @staticmethod
    def get_user(db, login, passwd):
        """Esse método retorna o usuário logado."""

        usuario = db.query(Usuario).filter(Usuario.login == login).first()
        if usuario.validate_passwd(passwd):
            return usuario
        else:
            raise Exception("erro ao logar")

    @staticmethod
    def get_principal_roleadmin(db):
        """Verificando se o papel role_admin foi criado ou não"""

        role = db.query(Principal).filter(Principal.nome == "role_admin").first()
        if not role:
            return False

        return True

    def get_all_informations(db):
        dh = db.query(DomainHost).all()

        if not dh:
            return None

        return dh

    @staticmethod
    def get_principals(db, user):
        usuario = db.query(Usuario).filter(Usuario.login == user.decode("utf8")).first()
        if usuario:
            return [p.nome for p in usuario.principals]


class Log:
    def __init__(self, module_name):
        self.logger = logging.getLogger(module_name)

        fmt = '[W %(asctime)s %(name)s:%(funcName)s:%(lineno)d] %(message)s'
        format = logging.Formatter(fmt)
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        self.logger.addHandler(handler)

        self.__info = self.logger.info
        self.__debug = self.logger.debug

    def info(self, message):
        return self.__info(message)

    def debug(self, message):
        return self.__debug(message)
