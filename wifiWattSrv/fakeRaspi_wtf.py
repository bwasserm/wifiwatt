import random
import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import uuid
import pika
from pika.adapters.tornado_connection import TornadoConnection
from tornado.options import define, options
import wifiWattRabbitConfig as rc


define("port", default=8080, help="run on the given port", type=int)


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
        '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class Application(tornado.web.Application):
  def __init__(self):
    handlers = [
      (r"/", MainHandler),
    ]
    settings = dict(
      cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
      login_url="/auth/login",
      template_path=os.path.join(os.path.dirname(__file__), "templates"),
      static_path=os.path.join(os.path.dirname(__file__), "static"),
      xsrf_cookies=True,
      autoescape="xhtml_escape",
    )
    tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("index.html")

class PikaClient(object):

  def __init__(self, app, ioloop):
    print('PikaClient: __init__')
    self.app = app
    self.ioloop = ioloop

    self.connected = False
    self.connecting = False
    self.connection = None
    self.channel = None

    self.valueExng = rc.valueExngAttr

  def connect(self):
    if self.connecting:
      print('PikaClient: Already connecting to RabbitMQ')
      return

    print('PikaClient: Connecting to RabbitMQ')
    self.connecting = True

    cred = pika.PlainCredentials('guest', 'guest')
    param = pika.ConnectionParameters(
      host='localhost',
      port=5672,
      virtual_host='/',
      credentials=cred
    )

    self.connection = TornadoConnection(param,
      on_open_callback=self.onConnected)
    self.connection.add_on_close_callback(self.onClosed)

  def onConnected(self, connection):
    print('PikaClient: connected to RabbitMQ')
    self.connected = True
    self.connection = connection
    self.connection.channel(self.onChannelOpen)

  def onChannelOpen(self, channel):
    LOGGER.info('PikaClient: Channel open, Declaring exchange')
    self.channel = channel
    self.channel.confirm_delivery(self.onDeliveryConfirmation)
    # make exchange
    self.channel.exchange_declare(self.onExchangeDeclare(),"ww.valueUpdate", "fanout")
  
  def onExchangeDeclare(self):
    LOGGER.info("Starting to send garbage.")
    self.sendGarbage()

  def sendGarbage(self):
    randNum = random.randrange(0, 15)
    # print("sendGarbage: sending {0}".format(randNum))
    self.channel.basic_publish(
      exchange = rc.valueExngAttr['exchange'],
      routing_key = "",
      body = "{0}".format(randNum)
    )
    self.ioloop.add_timeout(100, self.sendGarbage)

  def onDeliveryConfirmation(self):
    print("delivery confirmed")

  def onClosed(self, connection):
    print('PikaClient: rabbit connection closed')
    self.ioloop.stop()

  def onMessage(self, channel, method, header, body):
    print('PikaClient: message received: \n header: {0}\n body: {1}'.format(header, body))




def main():
  tornado.options.parse_command_line()

  app = Application()
  ioloop = tornado.ioloop.IOLoop.instance()

  app.pika = PikaClient(app, ioloop)
  app.listen(options.port)
  
  ioloop.add_timeout(500, app.pika.connect)
  ioloop.start()

if __name__ == "__main__":
  main()
