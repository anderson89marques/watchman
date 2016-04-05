from core.services import Log
import paramiko

log = Log(__name__)


# usar um contextManager depois
class SSHManager:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.channel = None
        self.hostname = None
        self.username = None
        self.password = None

    def connect(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

        log.info("Conectando {}@{}".format(self.username, self.hostname))
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.hostname, username=self.username, password=self.password)
            log.info("conexão realizada com sucesso!")
        except Exception as e:
            log.info("Falhou: {}".format(e.__str__()))
            raise Exception("Falhou: {}".format(e.__str__()))
        return True

    def exec_command(self, cmd):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            msg = stdout.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            r = {"msg": msg, "exit_status": exit_status}
        except Exception as e:
            log.info(e.__str__())
        return r

    def close(self):
        log.info("Fechando Conexão")
        self.ssh.close()
