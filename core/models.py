from sqlalchemy import Column, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost/watchmanDB")
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    login = Column(Text, nullable=True)
    passwd = Column(Text, nullable=True)
    principals = relationship("Principal", secondary="usuario_principal")

    def add_passwd(self, senha):
        #Criando um objeto que usará criptografia do método shs256, rounds default de 80000
        cripto = CryptContext(schemes="sha256_crypt")

        #Encriptografando uma string
        self.senha = cripto.encrypt(senha)

    def validate_passwd(self, senha):
         #Criando um objeto que usará criptografia do método shs256, rounds default de 80000
        cripto = CryptContext(schemes="sha256_crypt")

        #Comparando o valor da string com o valor criptografado
        okornot = cripto.verify(senha, self.senha)
        return okornot


class Usuario_Principal(Base):
    __tablename__ = "usuario_principal"

    usuario_id = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    principal_id = Column(Integer, ForeignKey("principal.id"), primary_key=True)


class Principal(Base):
    __tablename__ = "principal"

    id = Column(Integer, primary_key=True)
    nome = Column(Text, nullable=True)
    usuarios = relationship("Usuario", secondary="usuario_principal")


class DomainHost(Base):
    __tablename__ = "domain_host"

    id = Column(Integer, primary_key=True)
    host_name = Column(Text)
    host_ip = Column(Text)
    services = relationship("DomainService", uselist=True, back_populates="host", cascade="all, delete-orphan")

    def __str__(self):
        return "[host_name: {}, host_ip: {}]".format(self.host_name, self.host_ip)


class DomainService(Base):
    __tablename__ = "domain_service"

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime)
    last_update = Column(DateTime)
    service_name = Column(Text)
    description = Column(Text)
    script_name = Column(Text)
    exit_status = Column(Text)
    exit_info = Column(Text)
    interval = Column(Integer)
    args = Column(Text)
    host_id = Column(Integer, ForeignKey("domain_host.id"))
    host = relationship("DomainHost", uselist=False, back_populates="services", )

    def __str__(self):
        return "[service_name: {}, status_servico: {}]".format(self.service_name, self.status_service)

