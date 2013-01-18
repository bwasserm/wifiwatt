

# debugging
import traceback
import sys
import random

# prog basics
import time
import logging
import os.path
import uuid
import copy
from tornado.options import define, options

# tornado engine
import socket
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web

# sockJS lib
import sockjs.tornado
import json

# pika (RabbitMQ lib)
import pika
from pika.adapters.tornado_connection import TornadoConnection

# helper files
import wifiWattRabbitConfig
import wifiWattNode
import watermark

################################################################################
## some global helpers #########################################################
define("port", default=8080, help="run on the given port", type=int)

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
        '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

rc = wifiWattRabbitConfig.generateRabbitObjs(socket.gethostname())

prefMsgRate = 0.2 # (s)
tornadoApp = None # we're going to cheat, since I can't figure out how to pass
# this to the SockJSClient instance

## / global helpers ############################################################
## Tornado App Definition ######################################################

class Application(tornado.web.Application):

  # TODO: think about having a timeout to zero-fill the data for disconnected nodes

  def __init__(self, sockJSUrls):
    # setup tornado app
    handlers = [
      (r"/", MainHandler),
    ] + sockJSUrls
    settings = dict(
      cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
      # login_url="/auth/login",
      template_path=os.path.join(os.path.dirname(__file__), "templates"),
      static_path=os.path.join(os.path.dirname(__file__), "static"),
      xsrf_cookies=True,
      autoescape="xhtml_escape",
    )
    tornado.web.Application.__init__(self, handlers, **settings)

    # application data structures
    self.nodes = dict() # dict of hostname=wifiWattNode(object)
    self.webClients = set()
# / class Application




class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("index.html")
# / class MainHandler


## / Tornado App Definition ####################################################
################################################################################

class SockJSClient(sockjs.tornado.SockJSConnection):
  webClients = set() # class var

  ## Connection Setup ##########################################################
  def on_open(self, info):
    self.app = tornadoApp
    self.app.webClients = self.webClients
    # add to client pool
    self.webClients.add(self)
    # inform/subscript the webclient of/to known nodes with newNode callback
    for (nodeName, nodeObj) in self.app.nodes.iteritems():
      self.newNodeCb(nodeObj)


    # nodesList = self.app.nodes.keys()
    # if(len(nodesList) > 0):
    #   msgPayload = dict(nodes=nodesList)
    #   self.sendJson("newNodes", msgPayload)
    # # subscribe to status of all existing nodes
    # for nodeHostname, nodeObj in self.app.nodes.iteritems():
    #   nodeObj.newSubscription(self, "status")
    # TODO: when a new person subscribes, should we send them data or wait for request?

  def on_close(self):
    # remove from client pool
    self.webClients.remove(self)
    # unsubscribe from all lists
    for nodeHostname, nodeObj in self.app.nodes.iteritems():
      nodeObj.delSubscription(self, "status")
      nodeObj.delSubscription(self, "hour")
      nodeObj.delSubscription(self, "day")

  def sendJson(self, msgType, payload):
    """
    send a message to web client in json format
    msgType(string): message type key
    payload(dict): data of the message; msgType is appended
    """
    # msgDict = copy.deepcopy(payload)
    msgDict = payload # we're always given a temp dict anyways
    msgDict["type"] = msgType
    msgString = json.dumps(msgDict)
    self.send(msgString)

  def on_message(self, msg):
    # attempt to unpack message and check integrity
    LOGGER.info("new message: %s", msg)
    try:
      msgJson = json.loads(msg)
    except:
      LOGGER.error('Got malformed json from client %s', repr(self))
      return -1
    if("type" not in msgJson):
      LOGGER.error('Got message without type from client %s', repr(self))
      return -1
    msgType = msgJson["type"]
    # dispatch to correct handler
    if(msgType == "subscription"):
      self.subscriptionHandler(msgJson)
    elif(msgType == "delSubscription"):
      self.delSubscriptionHandler(msgJson)
    elif(msgType == "nodePower"):
      self.nodePwrHandler(msgJson)
    else:
      LOGGER.error('Couldn\'t handle message type from client %s', repr(self))

  ## Handlers (deal with requests from browser) ################################
  def subscriptionHandler(self, msgJson):
    # check for malformed message
    if("hostname" not in msgJson):
      LOGGER.error('No hostname in sub request from %s!', repr(self))
      return -1
    if(("subType" not in msgJson) and
      not (msgJson["subType"] == "day" or msgJson["subType"] == "hour")):
      LOGGER.error('Bad sub subType from %s!', repr(self))
      return -1
    # try to grant subscription
    hostname = msgJson["hostname"]
    if(hostname not in self.app.nodes):
      LOGGER.error('Sub request for mystery hostname from %s!', repr(self))
      return -1
    self.app.nodes[hostname].newSubscription(self, msgJson["subType"])


  def delSubscriptionHandler(self, msgJson):
    # check for malformed message
    if("hostname" not in msgJson):
      LOGGER.error('No hostname in delSub request from %s!', repr(self))
      return -1
    if(("subType" not in msgJson) and
      not (msgJson["subType"] == "day" or msgJson["subType"] == "hour")):
      LOGGER.error('Bad delSub subType from %s!', repr(self))
      return -1
    # try to grant subscription
    hostname = msgJson["hostname"]
    if(hostname not in self.app.nodes):
      LOGGER.error('DelSub request for mystery hostname from %s!', repr(self))
      return -1
    self.app.nodes[hostname].delSubscription(self, msgJson["subType"])

  def nodePwrHandler(self, msgJson):
    # check for malformed message
    if("nodeName" not in msgJson):
      LOGGER.error('No nodeName in power request from %s!', repr(self))
      return -1
    # try to grant power on
    nodeName = msgJson["nodeName"]
    if(nodeName not in self.app.nodes):
      LOGGER.error('Power request for mystery nodeName from %s!', repr(self))
      return -1
    self.app.nodes[nodeName].powerSet(msgJson["pwrVal"])
    # send rabbit cmd
    self.app.rabbit.sendNodeCtrlMsg(nodeName, 1 if msgJson["pwrVal"] else 0) 

# todo: make the new data callbacks go to all sockjs connections

  ## Callbacks (send back to browser) ##########################################
  def statusCb(self, dataList, nodeName, relayState):
    msg = dict(
      dataPoints = dataList,
      subType = "status",
      nodeName = nodeName,
      relayState = relayState
    )
    self.sendJson("newData", msg)

  def hourCb(self, dataList, nodeName):
    msg = dict(
      dataPoints = dataList,
      nodeName = nodeName,
      subType = "hour"
    )
    self.sendJson("newData", msg)

  def dayCb(self, dataList, nodeName):
    msg = dict(
      dataPoints = dataList,
      nodeName = nodeName,
      subType = "day"
    )
    self.sendJson("newData", msg)

  def newNodeCb(self, nodeObj):
    # send back a list of new nodes (only 1 in this case)
    msgPayload = dict( nodes = [nodeObj.hostname] )
    self.sendJson("newNodes", msgPayload)
    # subscribe user to this node's status
    nodeObj.newSubscription(self, "status")


  


## / class SockJSClient ########################################################
################################################################################

class RabbitClient(object):

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

  ## Connection Logic ##########################################################

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

  def sendNodeCtrlMsg(self, nodeHostname, ctrlCode):
    self._channel.basic_publish(
      rc.msgExngAttr["exchange"],
      "node.{0}.cmd".format(nodeHostname),
      str(ctrlCode)
    )

  ## Message Route Init ########################################################

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
    self._channel.basic_consume(self.valueHandler, rc.valueQueAttr["queue"],
      no_ack=True)
    self._channel.basic_consume(self.initNodeHandler,
      rc.handshakeQueAttr["queue"])
    self._channel.basic_consume(self.serverCmdHandler, rc.cmdQueAttr["queue"])
    self._channel.basic_consume(self.nErrHandler, rc.nErrQueAttr["queue"])
    LOGGER.info('Server ready!')


  ## Handlers ##################################################################

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
    # attempt to parse message and check fields
    try:
      msgData = json.loads(body)
    except:
      LOGGER.error("Couldn't parse message. Malformed.")
      return -1
    if(("hostname" not in msgData)
      or ("current" not in msgData)
      or ("relayState" not in msgData)):
      LOGGER.error("Couldn't parse message. Mising fields.")
      return -1
    hostname = msgData["hostname"]
    value = float(msgData["current"])
    relayState = bool(int(msgData["relayState"]))
    LOGGER.info("Raw: %s Parsed: %d", msgData["relayState"], int(relayState))

    # if we've inited this node, call it's append method
    if hostname in self.app.nodes:
      nodeObj = self.app.nodes[hostname]
      newDP = wifiWattNode.wwDataPoint(value, time.time())
      nodeObj.appendData(newDP, relayState)
    else:
      LOGGER.error('No node with hostname <%s>!', hostname)

    # attempt to read message header info
    # if "hostname" in prop.headers:
    #   hostname = prop.headers["hostname"]
    # else:
    #   LOGGER.error('Couldn\'t read hostname from message!')
    #   return -1
    # # parse the message 
    # value = float(body)
    # LOGGER.info('Got new value "%f" from hostname <%s>.', value, hostname)
    


  def initNodeHandler(self, channel, basicDeliver, prop, body):
    """
    Initialize the data stores for a node on the server. Works as a callback for
    a new message to the server handshake queue.
    """
    # parse the hostname from handshake message
    hostname = body
    nodes = self.app.nodes
    # check if we already have structures for this node
    if(hostname in nodes):
      # we have it already
      LOGGER.info('Got handshake for node <%s>; already exists.', hostname)
    else:
      # make a new node instance
      LOGGER.info('Initing new node for hostname: %s', hostname)
      newNode = wifiWattNode.wifiWattNode(hostname)
      nodes[hostname] = newNode
    # send back the prefered message rate to start value stream
    self._channel.basic_publish(
      rc.msgExngAttr["exchange"],
      "node.{0}.handshake".format(hostname),
      str(prefMsgRate)
    )
    # notify all our webclients that we have a new node
    for webClient in self.app.webClients:
      webClient.newNodeCb(newNode)

  def serverCmdHandler(self, channel, basicDeliver, prop, body):
    LOGGER.info('Got new command: %s', msg)

  def nErrHandler(self, channel, basicDeliver, prop, body):
    LOGGER.info('Got node error: %s', msg)

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

### / class RabbitClient #######################################################
################################################################################


def main():
  global tornadoApp
  watermark.printWatermark()

  tornado.options.parse_command_line()

  sockJSRouter = sockjs.tornado.SockJSRouter(SockJSClient, '/socket')

  app = Application(sockJSRouter.urls)
  tornadoApp = app # globals cheating
  ioloop = tornado.ioloop.IOLoop.instance()

  # instance sockJS server
  # app.sockjs = sockjs.tornado.SockJSRouter(SockJSClient, '/socket')
  # for handler in app.sockjs.urls:
  #   print(handler)
  #   print("")
  #   # app.add_handlers(handler[0], handler[1])
  # app.add_handlers(r"*", app.sockjs.urls)

  # instance rabbitMQ server
  app.rabbit = RabbitClient(app, ioloop)
  app.listen(options.port)
  
  ioloop.add_timeout(500, app.rabbit.connect)
  ioloop.start()

if __name__ == "__main__":
  main()
