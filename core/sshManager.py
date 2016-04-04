import logging
import paramiko


# usar um contextManager depois
class SSHManager:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.logger = logging.getLogger("SSHManager")
        self.channel = None
        self.hostname = None
        self.username = None
        self.password = None

        fmt = '%(asctime)s MySSH:%(funcName)s:%(lineno)d %(message)s'
        format = logging.Formatter(fmt)
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        self.logger.addHandler(handler)
        self.info = self.logger.info

    def connect(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

        print("Conectando {}@{}".format(self.username, self.hostname))
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.hostname, username=self.username, password=self.password)
            print("conexão realizada com sucesso!\n")
        except Exception as e:
            print("Falhou: {}".format(e.__str__()))
            raise Exception("Falhou: {}".format(e.__str__()))
        return True

    def exec_command(self, cmd):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            msg = stdout.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            r = {"msg": msg, "exit_status": exit_status}
        except Exception as e:
            print(e.__str__())
        return r

    def close(self):
        print("Fechando Conexão")
        self.ssh.close()