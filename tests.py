import unittest
from core.sshManager import SSHManager
from core.loadFiles import Servico, LoadFile


class TestServico(unittest.TestCase):
    def setUp(self):
        self.host = {"ip": "177.126.189.65", "username": "devop", "password": "T636:6yX"}
        self.s = Servico(name="s1", description="d", time=1, script="script.py", host=self.host)

    def test_falta_params(self):
        """Deve retornar uma exceção por falta de parâmetrio"""

        with self.assertRaises(Exception):
            Servico(host=self.host)

    def test_Servico_remote_conn_return_SSHManager(self):
        """O método remote_conn deve retornar um SSHManager"""

        self.assertIsInstance(self.s.remote_conn, SSHManager)

    def test_ip_format_error(self):
        """Se o ip não for um ip válido deve ser lançado um exceção"""

        host = {"ip": "177.126.189.a", "username": "devop", "password": "T636:6yX"}
        with self.assertRaises(Exception):
            Servico(name="s1", description="d", time=1, script="script.py", host=host)

    def tearDown(self):
        self.s.remote_conn.close()


class TestSSHManager(unittest.TestCase):
    def setUp(self):
        self.ssh = SSHManager()

    def test_connect_ok(self):
        """Conexão válida retorna deve retornar True"""

        self.assertTrue(self.ssh.connect(hostname="177.126.189.65", username="devop", password="T636:6yX"))

    def test_connect_ip_error(self):
        with self.assertRaises(Exception):
            self.ssh.connect(hostname="177.126.189.a", username="devop", password="T636:6yX")

    def test_connect_user_error(self):
        with self.assertRaises(Exception):
            self.ssh.connect(hostname="177.126.189.65", username="devopA", password="T636:6yX")

    def test_connect_password_error(self):
        with self.assertRaises(Exception):
            self.ssh.connect(hostname="177.126.189.65", username="devop", password="T636:6yy")

    def test_execommand_ok(self):
        self.ssh.connect(hostname="177.126.189.65", username="devop", password="T636:6yX")
        self.assertIsInstance(self.ssh.exec_command("ls"), dict)

if __name__ == "__main__":
    unittest.main()