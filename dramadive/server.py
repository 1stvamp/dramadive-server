#!/usr/bin/env python3

from sys import stdout
from os.path import join, dirname
from time import time

from yaml import load

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import RequestHandler, Application

from trequests import setup_session
from tornalet import tornalet

# Tell requests to use our AsyncHTTPadapter for the default
# session instance
setup_session()


def climber_mode(config, action=False):
    if action:
        config['giving'] = 0.01
    else:
        config['giving'] += 0.10
    print(config['giving'])


def generous_mode(config, action=False):
    if action:
        config['giving'] += 0.10
    else:
        if config['giving'] > 0.10:
            config['giving'] -= 0.10
        else:
            config['giving'] = 0.01
    print(config['giving'])


MODE_MAP = {
    'climber': climber_mode,
    'generous': generous_mode,
}


class MainHandler(RequestHandler):

    def __init__(self, *args, **kwargs):
        self.config = self.application.dd_config

    def prepare(self):
        self.set_header('Content-Type', 'application/json; charset="utf-8"')

    @tornalet
    def post(self):
        action = self.get_argument('action', '')
        self.write({'action': action})
        if action == 'down':
            MODE_MAP[self.config['mode']](self.config, True)


application = Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    config = load(open(join(dirname(__file__), '../config.yaml'), 'r'))
    config['giving'] = 0.01
    application.dd_config = config

    application.listen(8888)
    print('Service started on http://localhost:8888/', file=stdout)

    ioloop = IOLoop.instance()

    mode_func = MODE_MAP[config['mode']]

    callback = PeriodicCallback(
            lambda: mode_func(config, False),
            config.get('update', 60 * 60 * 24) * 1000,
            ioloop)

    callback.start()
    ioloop.start()
