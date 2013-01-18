import time

# 10MB per node = 10485760bytes

# 1 day = 86400000 ms

# samples are 8 bytes (timestamp) + 8 bytes (float) = 16bytes

# 655360 samples/day

# sample ~ every 132ms

class ringBuffer(object):
  def __init__(self, size):
    nullDP = wwDataPoint(0, time.time())
    self.data = [nullDP for i in xrange(size)]
    self.size = size

  def append(self, x):
    self.data.pop(0)
    self.data.append(x)

  def getBuf(self):
    # return the whole buffer (list)
    return self.data

  def getLast(self):
    # return the most recently appended element
    print(repr(self.data[-1]))
    return self.data[-1]

class wwDataPoint(object):
  """
  object binding data to a timestamp
  timestamp: unix timestamp in sec as float
  data: current reading at timestamp
  """
  def __init__(self, data, timestamp=time.time()):
    self.timestamp = timestamp
    self.data = data

  def dictRepr(self):
    return dict(timestamp=self.timestamp, data=self.data)

class wwNodeSubscriber(object):
  """
  object binding web client name to a type of subscriptions
  name: web client id
  subscription (int): status (0), hour (1), day (2)
  """
  def __init__(self, name, subscription):
    self.name = name
    self.subscription = subscription


class wifiWattNode(object):
  def __init__(self, hostname):
    # remember your name
    self.hostname = hostname

    # define data buffers
    # daybuf holds 24hrs(86400s) of data at 1 point/5s
    self.daybuf = ringBuffer(17280)
    # hourbuf holds 1hrs(3600s) of data at 5 points/1s
    self.hourbuf = ringBuffer(18000)

    # define state
    self.relayOn = False;

    # define subscription lists
    self.subs = dict(
      status = [],
      hour = [],
      day = []
    )

  def __checkDayThresh(self, newDP):
    # return True if we're close to 5s or over (>4.8s)
    rawr = self.daybuf.getLast()
    oldTime = rawr.timestamp
    newTime = newDP.timestamp
    return (oldTime + 4.800) < newTime

  def __checkHourThresh(self, newDP):
    # return True if we're close to .2s or over (>.15s)
    rawr = self.hourbuf.getLast()
    oldTime = rawr.timestamp
    newTime = newDP.timestamp
    print(oldTime)
    print(newTime)
    return (oldTime + 0.150) < newTime

  def appendData(self, newDP):
    """
    take a new wwDataPoint, update the buffers, and fire the appropriate
    callbacks to send data to browsers
    newDP: wwDataPoint
    """
    # given a wwDataPoint, add it to the necessary lists
    # check if it has been long enough since the last hour point
    if(self.__checkHourThresh(newDP)):
      # print("added new hour buf data")
      self.hourbuf.append(newDP)

      # then, push this data to all subscribed connections
      for conn in self.subs["status"]:
        conn.statusCb( [newDP.dictRepr], self.hostname, self.relayOn)
      for conn in self.subs["hour"]:
        conn.hourCb( [newDP.dictRepr()], self.hostname)

    # check if it has been long enough since the last day point
    if(self.__checkDayThresh(newDP)):
      self.daybuf.append(newDP)

      # push to subscribers
      for conn in self.subs["day"]:
        conn.dayCb( [newDP.dictRepr()], self.hostname)


  def newSubscription(self, sockjsConn, type):
    """
    register a new subscription to a node's data
    name: web client id
    type: status, hour, day
    """
    # check message structure
    if(not(type == "status" or type == "day" or type == "hour")):
      print("Can't grant subscription for unknown type!")
    # ok? grant subscription
    self.subs[type].append(sockjsConn)
    # send back old data
    if(type == "status"):
      # grab last state
      sockjsConn.statusCb([self.hourbuf.getLast().dictRepr()], self.hostname,self.relayOn);
    elif(type == "hour"):
      # assemble the old data, then push back
      oldData = recallHistory(self.hourbuf)
      sockjsConn.hourCb(oldData, self.hostname)
    elif(type == "day"):
      # assemble the old data, then push back
      oldData = recallHistory(self.daybuf)
      sockjsConn.dayCb(oldData, self.hostname)
      

  def delSubscription(self, name, type):
    self.subs[type].remove(name)

  def powerOn(self):
    pass

  def powerOff(self):
    pass

  def recallHistory(self, buf):
    """
    take a type of history and return the 2D list of datapoint objects
    buf: a data buffer
    """
    # build the output list
    listOut = []
    for dp in buf.getBuf():
      listOut.append(dp.dictRepr())
    return listOut










