import traceback
import sys
import socket
import random
import time
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
import wifiWattRabbitConfig


define("port", default=8080, help="run on the given port", type=int)

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
        '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

rc = wifiWattRabbitConfig.generateRabbitObjs(socket.gethostname())


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

class ExamplePublisher(object):
  """This is an example publisher that will handle unexpected interactions
  with RabbitMQ such as channel and connection closures.

  If RabbitMQ closes the connection, it will reopen it. You should
  look at the output, as there are limited reasons why the connection may
  be closed, which usually are tied to permission related issues or
  socket timeouts.

  It uses delivery confirmations and illustrates one way to keep track of
  messages that have been sent and if they've been confirmed by RabbitMQ.

  """
  EXCHANGE = 'message'
  EXCHANGE_TYPE = 'topic'
  PUBLISH_INTERVAL = .001
  QUEUE = 'text'
  ROUTING_KEY = 'example.text'

  def __init__(self, app, ioloop):
    """Setup the example publisher object, passing in the URL we will use
    to connect to RabbitMQ.

    :param str amqp_url: The URL for connecting to RabbitMQ

    """
    self._connection = None
    self._channel = None
    self._deliveries = []
    self._acked = 0
    self._nacked = 0
    self._message_number = 0
    self._stopping = False
    self.app = app
    self.ioloop = ioloop

  ##############################################################################
  ## Connection Logic                                                         ##
  ##############################################################################

  def connect(self):
    LOGGER.info('Connecting to RabbitMQ')
    # exc_type, exc_value, exc_traceback = sys.exc_info()
    # traceback.print_tb(exc_traceback, limit=None, file=sys.stdout)
    # self.connecting = True

    self._connection = TornadoConnection(rc.connParam,
      on_open_callback=self.on_connection_open)

  def close_connection(self):
    """This method closes the connection to RabbitMQ."""
    LOGGER.info('Closing connection')
    self._connection.close()

  def add_on_connection_close_callback(self):
    LOGGER.info('Adding connection close callback')
    self._connection.add_on_close_callback(self.on_connection_closed)

  def on_connection_closed(self, method_frame):
    # if we loose the connection, try to reconnect
    LOGGER.warning('Server closed connection, reopening: (%s) %s',
             method_frame.method.reply_code,
             method_frame.method.reply_text)
    self._channel = None
    self._connection = self.connect()

  def on_connection_open(self, unused_connection):
    LOGGER.info('Connection opened')
    self.add_on_connection_close_callback()
    self.open_channel()

  def add_on_channel_close_callback(self):
    LOGGER.info('Adding channel close callback')
    self._channel.add_on_close_callback(self.on_channel_closed)

  def on_channel_closed(self, method_frame):
    # if rabbit closes the channel, quit server
    LOGGER.warning('Channel was closed: (%s) %s',
             method_frame.method.reply_code,
             method_frame.method.reply_text)
    self._connection.close()

  def on_channel_open(self, channel):
    LOGGER.info('Channel opened')
    self._channel = channel
    self.add_on_channel_close_callback()
    self.setupExngsQueues()

  ##############################################################################
  ## Message Route Init                                                       ##
  ##############################################################################

  def setupExngsQueues(self):
    LOGGER.info('')
    self.exngQueCount = 0
    self.exngQueNum = len(rc.svrExngs) + len(rc.svrQueues)
    # open all exchanges and queues we need asynchronously
    for exng in rc.svrExngs:
      self.setupExchange(exng)
    for queue in rc.svrQueues:
      self.setupQueue(queue)
    # callback fn counts when everything is declared
  def setupExchange(self, exng):
    LOGGER.info('Declaring exchange %s', exng["exchange"])
    self._channel.exchange_declare(self.onExngQueDeclare, **exng)
  def setupQueue(self, queue):
    LOGGER.info('Declaring queue %s', queue["queue"])
    self._channel.queue_declare(self.onExngQueDeclare, **queue)

  def onExngQueDeclare(self, mystery=None): # got unknown return
    # check to see how many rabbit entities are declared
    self.exngQueCount = self.exngQueCount + 1
    LOGGER.info('Declared %d exchanges/queues.', self.exngQueCount)
    if(self.exngQueCount == self.exngQueNum):
      # all our exchanges and queues are accounted for; setup bindings
      self.setupBindings()

  def setupBindings(self):
    self.bindingsCount = 0
    self.bindingsNum = len(rc.svrBindings)
    for binding in rc.svrBindings:
      LOGGER.info('Binding exchange %s to queue %s', binding["exchange"],
        binding["queue"])
      self._channel.queue_bind(self.onBind, binding["queue"],
        binding["exchange"], binding["routing_key"])

  def onBind(self, mystery=None):
    # check to see if we made all our bindings
    self.bindingsCount = self.bindingsCount + 1
    LOGGER.info('Made %d bindings.', self.bindingsCount)
    if(self.bindingsCount == self.bindingsNum):
      # all of our bindings are accounted for; build message logic
      self.setupMsgRouting()
  def setupMsgRouting(self):
    # map the message queues we defined to our handlers
    LOGGER.info('Mapping handlers...')
    self._channel.basic_consume(self.valueHandler, rc.valueQueAttr["queue"])
    self._channel.basic_consume(self.initNodeHandler,
      rc.handshakeQueAttr["queue"])
    self._channel.basic_consume(self.serverCmdHandler, rc.cmdQueAttr["queue"])
    self._channel.basic_consume(self.nErrHandler, rc.nErrQueAttr["queue"])
    LOGGER.info('Server ready!')


  ##############################################################################
  ## Handlers                                                                 ##
  ##############################################################################

# [I 130116 01:17:40 wifiWattSrv:203] 
# Bad message (TypeError('not all arguments converted during string formatting',)):
# {'threadName': 'MainThread', 'name': '__main__', 'thread': 139807606114048, 'created': 1358317060.982559, 'process': 10225, 'processName': 'MainProcess',
# 'args': (<pika.channel.Channel object at 0x1b77590>,
#   <Basic.Deliver(['consumer_tag=ctag1.0', 'redelivered=True', 'routing_key=', 'delivery_tag=1', 'exchange=ww.valueUpdate'])>,
#   <BasicProperties(['delivery_mode=1', "headers={'hostname': 'applepi'}"])>, '2.9493'), 'module': 'wifiWattSrv', 'filename': 'wifiWattSrv.py', 'levelno': 20, 'exc_text': None, 'pathname': 'wifiWattSrv.py', 'lineno': 203, 'msg':
# 'Got new channel: %s, basicDeliver: %s, prop: %s, body: ', 'exc_info': None, 'funcName': 'valueHandler', 'relativeCreated': 252.96688079833984, 'levelname': 'INFO', 'msecs': 982.5589656829834}


  def valueHandler(self, channel, basicDeliver, prop, body):
    """
    :param pika.channel.Channel unused_channel: The channel object
    :param pika.Spec.Basic.Deliver: basic_deliver method
    :param pika.Spec.BasicProperties: properties
    :param str|unicode body: The message body
    """
    LOGGER.info('Got new value "%s" from hostname <%s>', body, prop.headers["hostname"])

  def initNodeHandler(self, channel, basicDeliver, prop, body):
    LOGGER.info('Got new node @ hostname: %s', msg)

  def serverCmdHandler(self, channel, basicDeliver, prop, body):
    LOGGER.info('Got new command: %s', msg)

  def nErrHandler(self, channel, basicDeliver, prop, body):
    LOGGER.info('Got node error: %s', msg)




  # def on_delivery_confirmation(self, method_frame):
  #   confirmation_type = method_frame.method.NAME.split('.')[1].lower()
  #   LOGGER.info('Received %s for delivery tag: %i',
  #         confirmation_type,
  #         method_frame.method.delivery_tag)
  #   if confirmation_type == 'ack':
  #     self._acked += 1
  #   elif confirmation_type == 'nack':
  #     self._nacked += 1
  #   self._deliveries.remove(method_frame.method.delivery_tag)
  #   LOGGER.info('Published %i messages, %i have yet to be confirmed, '
  #         '%i were acked and %i were nacked',
  #         self._message_number, len(self._deliveries),
  #         self._acked, self._nacked)

  # def enable_delivery_confirmations(self):
  #   LOGGER.info('Issuing Confirm.Select RPC command')
  #   self._channel.confirm_delivery(self.on_delivery_confirmation)

  # def publish_message(self):
  #   if self._stopping:
  #     return

  #   message = 'The current epoch value is %i' % time.time()
  #   properties = pika.BasicProperties(app_id='example-publisher',
  #                     content_type='text/plain')

  #   self._channel.basic_publish(rc.valueExngAttr["exchange"], self.ROUTING_KEY,
  #                 message, properties)
  #   self._message_number += 1
  #   self._deliveries.append(self._message_number)
  #   LOGGER.info('Published message # %i', self._message_number)
  #   self.schedule_next_message()

  # def schedule_next_message(self):
  #   """If we are not closing our connection to RabbitMQ, schedule another
  #   message to be delivered in PUBLISH_INTERVAL seconds.

  #   """
  #   if self._stopping:
  #     return
  #   LOGGER.info('Scheduling next message for %0.1f ms',
  #         self.PUBLISH_INTERVAL)
  #   self._connection.add_timeout(self.PUBLISH_INTERVAL,
  #                  self.publish_message)

  # def start_publishing(self):
  #   """This method will enable delivery confirmations and schedule the
  #   first message to be sent to RabbitMQ

  #   """
  #   LOGGER.info('Issuing consumer related RPC commands')
  #   self.enable_delivery_confirmations()
  #   self.schedule_next_message()

  # def on_bindok(self, unused_frame):
  #   """This method is invoked by pika when it receives the Queue.BindOk
  #   response from RabbitMQ. Since we know we're now setup and bound, it's
  #   time to start publishing."""
  #   LOGGER.info('Queue bound')
  #   self.start_publishing()

  def close_channel(self):
    """Invoke this command to close the channel with RabbitMQ by sending
    the Channel.Close RPC command.

    """
    LOGGER.info('Closing the channel')
    self._channel.close()

  def open_channel(self):
    """This method will open a new channel with RabbitMQ by issuing the
    Channel.Open RPC command. When RabbitMQ confirms the channel is open
    by sending the Channel.OpenOK RPC reply, the on_channel_open method
    will be invoked.

    """
    LOGGER.info('Creating a new channel')
    self._connection.channel(on_open_callback=self.on_channel_open)





def main():
  tornado.options.parse_command_line()

  app = Application()
  ioloop = tornado.ioloop.IOLoop.instance()

  app.pika = ExamplePublisher(app, ioloop)
  app.listen(options.port)
  
  ioloop.add_timeout(500, app.pika.connect)
  ioloop.start()

if __name__ == "__main__":
  main()
