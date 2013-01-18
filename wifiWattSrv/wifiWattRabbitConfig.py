import pika




# Routing keys
# node command: msg -> msgExng -> specific node's command queue
# 
# server time command: msg -> msgExng -> any server's work queue
# 
# node error: msg -> msgExng -> 
# 
# 
# node.<hostname>.cmd
# node.<hostname>.handshake
# server.<hostname>.handshake
# server.<hostname>.cmd
# server.<hostname>.nodeError
# server.ANYHOST.nodeError
# 
# 

class generateRabbitObjs(object):
  def __init__(self, hostname):
    ############################################################################
    # connection information
    ############################################################################
    login = dict(
      username = "guest",
      password = "guest"
    )
    cred = pika.PlainCredentials(**login)

    hostinfo = dict(
      host='localhost',
      port=5672,
      virtual_host='/',
      credentials=cred
    )
    self.connParam = pika.ConnectionParameters(**hostinfo)

    ############################################################################
    # exchanges
    ############################################################################

    # nodes write new values here
    self.valueExngAttr  = dict(
      exchange = "ww.valueUpdate",
      exchange_type = "fanout",
      durable = False,
      auto_delete = False,
      internal = False,
    )
    # used to send messages internally; both server + nodes have consumers
    self.msgExngAttr  = dict(
      exchange = "ww.messages",
      exchange_type = "topic",
      durable = False,
      auto_delete = False,
      internal = False,
    )
    self.svrExngs = [self.valueExngAttr, self.msgExngAttr]

    ############################################################################
    # queues
    ############################################################################

    # server reads in values here; when do we want data to expire?
    self.valueQueAttr = dict(
      queue = "ww.valueConsumer",
      durable = False,
      exclusive = False,
      auto_delete = False,
    )
    # messaging queues
    self.handshakeQueAttr = dict(
      queue = "server.{0}.handshake".format(hostname),
      durable = False,
      exclusive = True,
      auto_delete = False,
    )
    self.cmdQueAttr = dict(
      queue = "server.{0}.cmd".format(hostname),
      durable = False,
      exclusive = True,
      auto_delete = False,
    )
    self.nErrQueAttr = dict(
      queue = "server.{0}.nodeError".format(hostname),
      durable = False,
      exclusive = True,
      auto_delete = False,
    )
    self.svrQueues = [self.valueQueAttr, self.handshakeQueAttr, self.cmdQueAttr,
      self.nErrQueAttr]

    ############################################################################
    # bindings
    ############################################################################

    self.valueBindAttr = dict(
      queue = "ww.valueConsumer",
      exchange = "ww.valueUpdate",
      routing_key = "#"
    )
    self.handshakeBindAttr = dict(
      queue = "server.{0}.handshake".format(hostname),
      exchange = "ww.messages",
      routing_key = "server.*.handshake"
    )
    self.cmdBindAttr = dict(
      queue = "server.{0}.cmd".format(hostname),
      exchange = "ww.messages",
      routing_key = "server.*.cmd"
    )
    self.nErrBindAttr = dict(
      queue = "server.{0}.nodeError".format(hostname),
      exchange = "ww.messages",
      routing_key = "server.*.nodeError"
    )
    self.svrBindings = [self.valueBindAttr, self.handshakeBindAttr,
      self.cmdBindAttr, self.nErrBindAttr]






