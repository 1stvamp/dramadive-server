#!/usr/bin/env python3

from sys import stdout
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

from trequests import setup_session
from tornalet import tornalet

# Tell requests to use our AsyncHTTPadapter for the default
# session instance
setup_session()



class MainHandler(RequestHandler):
    def prepare(self):
        self.set_header('Content-Type', 'application/json; charset="utf-8"')

    @tornalet
    def post(self):
        action = self.get_argument('action', '')
        self.write({'action': action})


application = Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    print('Service started on http://localhost:8888/', file=stdout)
    IOLoop.instance().start()
