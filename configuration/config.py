###########################
#                         #
# Arquivo de Configuração #
#                         #
###########################

import os

HOME_USER_DIR = os.path.expanduser("~")

# .yaml file deve está dentro do work_dir
WORK_DIR = "{}/watchman".format(HOME_USER_DIR)

REMOTE_DIR_SCRIPTS = "watchman/scripts"

LOCAL_DIR_SCRIPTS = "{}/scripts".format(WORK_DIR)

HOSTS_INI_DIR = "/etc/watchman"

HOSTS_INI_FILE = "{}/hosts.ini".format(HOSTS_INI_DIR)

EXITS_STATUS = {0: "OK", 1: "WARNING", 2: "CRITICAL"}

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # diretorio do projeto

DEFAULT_SCRIPTS_PATH = "{}/scripts/local".format(PROJECT_DIR)  # aqui deve home/user/watchman/scripts

#LOCAL_IP = "192.168.0.105"
LOCAL_IP = "192.168.1.188"