# -*- coding: utf-8 -*-
import os
import stat
import yaml
from configuration.config import WORK_DIR, LOCAL_DIR_SCRIPTS, HOSTS_INI_DIR, HOSTS_INI_FILE

content_ini = """[localhost]
localhost: ip=localhost
"""

content_yaml = """
--- #inicio do arquivo
- hosts: localhost
  services:
    - name: memory_usage # nome do servico
      script: memory.py
      description: verifica memória
      time: 1
... #fim do arquivo
"""

content_default_service = """
import sys
from psutil import virtual_memory

mem = virtual_memory()

LIMITE_CRITICO = 500 * 1024 * 1024  # 500MB
LIMITE_ALERTA = 800 * 1024 * 1024  # 800MB

# 0 = OK
# 1 = WARNING
# 2 = CRITICAL

if mem.available < LIMITE_CRITICO:
    print("Consumo de memória crítico!")
    sys.exit(2)
elif mem.available < LIMITE_ALERTA:
    print("Consumo de memória alto!")
    sys.exit(1)
else:
    print("Consumo de memória dentro dos padrões!")
    sys.exit(0)
"""

try:
    if not os.path.exists(WORK_DIR):
        os.mkdir(WORK_DIR)

        with open("{}/services.yaml".format(WORK_DIR), "w") as yaml_file:
            yaml_file.write(content_yaml)

    if not os.path.exists(LOCAL_DIR_SCRIPTS):
        os.mkdir(LOCAL_DIR_SCRIPTS)

        with open("{}/memory.py".format(LOCAL_DIR_SCRIPTS), "w") as memory:
            memory.write(content_default_service)
        os.chmod("{}/memory.py".format(LOCAL_DIR_SCRIPTS), stat.S_IRWXO)  # read, write, execute by other

    if not os.path.exists(HOSTS_INI_DIR):
        os.mkdir(HOSTS_INI_DIR)

        with open(HOSTS_INI_FILE, "w") as hosts_ini:
            hosts_ini.write(content_ini)
except Exception as e:
    print(e.__str__())
