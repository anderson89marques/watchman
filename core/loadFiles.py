import datetime
#import logging
import configparser
import ssl
import subprocess
import json

import websocket
import yaml

from core.services import Log
from core.sshManager import SSHManager
from core.models import DomainHost, DomainService
from configuration import (EXITS_STATUS, REMOTE_DIR_SCRIPTS, HOSTS_INI_FILE, DEFAULT_SCRIPTS_PATH, PROJECT_DIR,
                           LOCAL_IP)

log = Log(__name__)


class LoadFile:
    """Classe responsável por ler os arquivos .yaml e o arquivos de host.ini
       e resolver as expressões com o jinja2
    """

    def __init__(self):
        self.configparser = configparser.ConfigParser()

    def safe_load(self, file):
        with open(file, "r") as f:
            managefile = yaml.safe_load(f)

        return managefile

    def get_host_data(self, host_name, host):
        # pensar em uma forma de tratar melhor os parâmetros permitidos no hosts.ini

        if "ip" and "username" and "password" in host:
            resp = host.split(" ")
            host_dict = {}

            if resp:
                if "ip" in resp[0]:
                    rp = resp[0].split("=")
                    host_dict[rp[0]] = rp[1]

                if "username" in resp[1]:
                    rp = resp[1].split("=")
                    host_dict[rp[0]] = rp[1]

                if "password" in resp[2]:
                    rp = resp[2].split("=")
                    host_dict[rp[0]] = rp[1]

                host_dict["host_name"] = host_name

        elif "ip" in host and "username" and "password" not in host:
            host_dict = {}
            rp = host.split("=")
            host_dict[rp[0]] = rp[1]

            host_dict["host_name"] = host_name

        return host_dict

    def load_host_file(self):
        self.configparser.read(HOSTS_INI_FILE)

    def get_all_hosts(self):
        self.load_host_file()
        hs = []
        try:
            for section in self.configparser.sections():
                for conf in self.configparser[section]:
                    hs.append(self.get_host_data(host_name=conf, host=self.configparser[section][conf]))
        except Exception as e:
            log.info(e.__str__())

        return hs

    def get_hosts(self, section):
        self.load_host_file()
        hs = []
        try:
            for conf in self.configparser[section]:
                hs.append(self.get_host_data(host_name=conf, host=self.configparser[section][conf]))
        except Exception as e:
            log.info(e.__str__())

        return hs


class Servico:
    """classe responsável por executar os camandos definidos nos arquivos .yaml"""

    def __init__(self, time, name, description, script, host=None, args=None):
        self._remote_conn = None
        self.remote_conn = host
        self.name = name
        self.description = description
        self.script = script
        self.time = time
        self.args = args

    @property
    def remote_conn(self):
        return self._remote_conn

    @remote_conn.setter
    def remote_conn(self, host):
        import re
        if not re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', host["ip"]):
            raise Exception("Ip inválido")

        if not self.remote_conn:
            self._remote_conn = self._connect_host(host)

    def _connect_host(self, host):
        ssh = SSHManager()
        try:
            ssh.connect(hostname=host["ip"], username=host["username"], password=host["password"])
        except Exception as e:
            log.info("Erro na tentiva de conexão: {}".format(e.__str__()))

        return ssh

    def run(self):
        cmd = "{dir}/{script} {args}".format(dir=REMOTE_DIR_SCRIPTS, script=self.script, args=self.args) \
            if self.args else "{dir}/{script}".format(dir=REMOTE_DIR_SCRIPTS, script=self.script)

        r = self.remote_conn.exec_command(cmd)
        log.info("Resposta exec_command:{}".format(r))

        if r["exit_status"] == 127:
            r["exit_status"] = 2  # para tratar como CRITICAL
            r["msg"] = "Comando ou diretório de scripts não encontrado"

        self.remote_conn.close()

        return r

    def get_answer_msg(self, resposta, cmd):
        """trata a mensagem de resposta do comando executado"""

        # Busco na resposta o final do comando executado porque depois disso é o resultado desse comando
        caracters_to_match = cmd[len(cmd)-3:-1]  # se o comando tiver menos que três caracteres vai ter problema
        len_carac_to_match = len(caracters_to_match)
        len_resp = len(resposta)
        pos_init = resposta.rfind(caracters_to_match, 0, len_resp-1)
        pos_fim = resposta.rfind("\n", 0, len_resp)

        r = resposta[pos_init + len_carac_to_match + 1: pos_fim]  # aqui encontrado a resposta do comnado executad

        return r


def update_service(db, servico, host, r):
    ws = websocket.create_connection("ws://{}:10000/ws/".format(LOCAL_IP),
                                     sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False}, )

    d = datetime.datetime.now()
    servico["host_name"] = host["host_name"]
    servico["ip"] = host["ip"]
    servico["exit_status"] = EXITS_STATUS[r["exit_status"]]
    servico["exit_status_info"] = r["msg"]
    servico["last_update"] = d.strftime("%d/%m/%Y %H:%M:%S")
    ws.send(json.dumps(servico))
    ws.close()

    # Atualizando dados no banco
    ds = db.query(DomainService).filter(DomainService.service_name == servico["name"]).first()
    ds.exit_status = EXITS_STATUS[r["exit_status"]]
    ds.exit_info = r["msg"]
    ds.last_update = d
    db.add(ds)
    db.commit()


def exec_local_scripts(db, servico, host):
    try:
        cmd = list()
        cmd.append("{dir}/{script}".format(dir=DEFAULT_SCRIPTS_PATH, script=servico['script']))
        if servico.get("args"):
            cmd.append("{args}".format(args=servico["args"]))

        resp = subprocess.run(cmd, stdout=subprocess.PIPE)
        r = {"msg": resp.stdout.decode(), "exit_status": resp.returncode}

        update_service(db, servico, host, r)
    except Exception as e:
        log.info("Erro exec local scripts:{}".format(e.__str__()))


def exec_remote_scripts(db, servico, host):
    try:
        args = servico["args"] if servico.get("args") else None
        remote_host = Servico(time=servico['time'], name=servico['name'], description=servico['description'],
                              script=servico['script'], host=host, args=args)

        resp = remote_host.run()
        r = {"msg": resp["msg"], "exit_status": resp["exit_status"]}

        update_service(db, servico, host, r)
    except Exception as e:
        log.info("Erro exec remote scripts: {}".format(e.__str__()))


def add_to_sched(sched, func, db, servico, host):
    sched.add_job(func, "interval", minutes=servico['time'],
                  kwargs={"db": db, "servico": servico, "host": host}, id=servico["name"])

    return True


def update_database(db, hosts, managefile):
    # como é passado só os services do manage específico então procuro os hosts do banco relacionado

    hs_db = db.query(DomainHost).all()
    if hs_db:
        for hdb in hs_db:
            is_h_in_file = False
            for ha in hosts:
                if hdb.host_name == ha["host_name"]:
                    is_h_in_file = True
                    break

            if is_h_in_file:
                for serv in hdb.services:
                    is_s_in_file = False
                    for manage in managefile:
                        if manage["services"]:
                            for servico in manage["services"]:
                                if serv.service_name == servico["name"]:
                                    is_s_in_file = True
                                    break
                            if is_s_in_file:
                                break
                        else:
                            raise Exception("Sem Serviço no arquivo")

                    if not is_s_in_file:
                        hdb.services.remove(serv)
                        db.delete(serv)
                        db.commit()
            else:
                db.delete(hdb)
                db.commit()


def process(db, schedule):
    sched = schedule

    load_file = LoadFile()
    managefile = load_file.safe_load("{dir}/teste.yaml".format(dir=PROJECT_DIR))
    #managefile = load_file.safe_load("{dir}/services.yaml".format(dir=WORK_DIR))
    log.info(managefile)

    ht = []  # será usado no controle dos hosts e serviços que foram excluídos do arquivo .yaml
    for manage in managefile:
        if manage["hosts"] == "all":
            # para cada host será executado aqueles serviços, lá também deve ser passado login e senha
            # deve retornar uma lista de mapas com os dados necessários, ip, username, password de cada host
            hosts = load_file.get_all_hosts()
        else:
            hosts = load_file.get_hosts(manage["hosts"])

        for hh in hosts:
            ht.append(hh)

        for host in hosts:
            h = db.query(DomainHost).filter(DomainHost.host_name == host["host_name"]).first()
            if not h:
                h = DomainHost(host_name=host["host_name"], host_ip=host["ip"])

            if manage.get('services'):
                for servico in manage['services']:
                    d = db.query(DomainService).filter(DomainService.service_name == servico["name"]).first()
                    date = datetime.datetime.now()

                    if not d:  # assim evito que um servico que já esteja rodando seja recriado
                        ds = DomainService(service_name=servico["name"], description=servico["description"],
                                           script_name=servico["script"], exit_status="WAITING", exit_info="WAITING",
                                           date_created=date, last_update=date, args=servico.get("args"),
                                           interval=servico['time'])            # pode não ter args
                        h.services.append(ds)
                        db.add(h)
                    else:
                        # Atualizando dados
                        if d.interval != servico['time']:
                            d.interval = servico['time']

                        if d.service_name != servico['name']:
                            d.service_name = servico['name']

                        if d.description != servico['description']:
                            d.description = servico["description"]

                        if d.script_name != servico['script']:
                            d.script_name = servico["script"]

                        if servico.get("args"):
                            if d.args != servico['args']:
                                d.args = servico['args']

                        db.add(d)

                    # criando os jobs
                    if host["host_name"] == "localhost":  # serviços executados localmente
                        add_to_sched(sched, exec_local_scripts, db, servico, host)
                    else:
                        add_to_sched(sched, exec_remote_scripts, db, servico, host)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            log.info("Erro DB: {}".format(e.__str__()))

    # iniciando os jobs
    sched.start()

    # atualizando as informações a partir do arquivo services.yaml
    update_database(db, ht, managefile)
    log.info("jobs running!")

#process()


