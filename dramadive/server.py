#!/usr/bin/env python3

from os.path import dirname, join
from sys import stdout
from time import time

import paypalrestsdk
from pprint import pprint
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
from yaml import load


def paypal_transfer(config):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "credit_card",
            "funding_instruments": [{
                "credit_card": {
                    "type": "visa",
                    "number": config['paypal']['visa_account_no'],
                    "expire_month": config['paypal']['visa_exp_month'],
                    "expire_year": config['paypal']['visa_exp_year'],
                    "cvv2": "874",
                    "first_name": "Joe",
                    "last_name": "Shopper"
                }}]},
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "item",
                        "sku": "item",
                        "price": "{0:.2f}".format(config['giving']),
                        "currency": "USD",
                        "quantity": 1
                        }]},
                    "amount": {
                        "total": "{0:.2f}".format(config['giving']),
                        "currency": "USD"
                        },
                    "description": 'dramadive donation'}]})

    if payment.create():
        print("Payment created successfully")
    else:
        print(payment.error)


def climber_mode(config, action=False):
    if action:
        config['giving'] = 0.01
    else:
        paypal_transfer(config)

        config['giving'] += 0.10

    print(config['giving'])

    for cb in SocketHandler.callbacks:
        cb(config['giving'])


def generous_mode(config, action=False):
    if action:
        config['giving'] += 0.10
    else:
        paypal_transfer(config)

        if config['giving'] > 0.10:
            config['giving'] -= 0.10
        else:
            config['giving'] = 0.01

    print(config['giving'])

    for cb in SocketHandler.callbacks:
        cb(config['giving'])


MODE_MAP = {
    'climber': climber_mode,
    'generous': generous_mode,
}


class MainHandler(RequestHandler):

    def post(self):
        self.set_header('Content-Type', 'application/json; charset="utf-8"')

        action = self.get_argument('action', '')
        self.write({'action': action})
        if action == 'down':
            MODE_MAP[self.config['mode']](self.config, True)

    def get(self):
        self.set_header('Content-Type', 'text/html; charset="utf-8"')

        self.render('index.html',
                    giving="{0:.2f}".format(self.config['giving']))


class SocketHandler(WebSocketHandler):
    callbacks = []

    def open(self):
        self.callbacks.append(self.call)

    def on_message(self, msg):
        pass

    def on_close(self):
        self.callbacks.remove(self.call)

    def call(self, giving):
        self.write_message("{0:.2f}".format(giving))


application = Application(
    [
        (r"/", MainHandler),
        (r"/socket/", SocketHandler)
    ],
    template_path=join(dirname(__file__), '../templates')
)

if __name__ == "__main__":
    config = load(open(join(dirname(__file__), '../config.yaml'), 'r'))
    config['giving'] = 0.01
    MainHandler.config = config

    paypalrestsdk.configure({
        "mode": "sandbox",
        "client_id": config['paypal']['api']['client_id'],
        "client_secret": config['paypal']['api']['client_secret']
    })

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
