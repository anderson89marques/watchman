import os
import tornado


from apscheduler.schedulers.tornado import TornadoScheduler
from sqlalchemy.orm import scoped_session, sessionmaker
from tornado.ioloop import IOLoop
from tornado.options import define, options

from core.models import engine, Base
from core.views import MainHandler, EchoWebSocket, LoginHandler, LogoutHandler, CreateUser, StartOrStopOrRemoveJOB
from core.loadFiles import process
from core.tornado_jinja2 import Jinja2Loader
from configuration.config import LOCAL_IP

rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))
sched = TornadoScheduler()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r'/login/', LoginHandler), (r'/control/', MainHandler), (r'/ws/', EchoWebSocket),
                    (r'/logout/', LogoutHandler), (r'/create_user/', CreateUser), (r'/action', StartOrStopOrRemoveJOB),
                    ]

        jinja2Loader = Jinja2Loader(rel('templates'))

        settings = dict(template_loader=jinja2Loader,
                        static_path=rel('static'),
                        template_path=rel('templates'),
                        debug=True, cookie_secret="key:ab1b90A")

        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = scoped_session(sessionmaker(bind=engine))
        self.sched = TornadoScheduler()
        Base.metadata.bind = engine
        Base.metadata.create_all(engine)

        try:
            process(self.db, self.sched)
        except Exception as e:
            print("Erro: {}".format(e))


def main():
    print("Inicializando aplicação...")
    define('listen', metavar='IP', default='{ip}'.format(ip=LOCAL_IP), help='listen on IP address (default 127.0.0.1)')
    define('port', metavar='PORT', default=10000, type=int, help='listen on PORT (default 6544)')
    define('debug', metavar='True|False', default=False, type=bool,
           help='enable Tornado debug mode: templates will not be cached '
           'and the app will watch for changes to its source files '
           'and reload itself when anything changes')

    options.parse_command_line()

    Application().listen(address=options.listen, port=options.port)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
