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

  def getListObj(self):
    return [self.timestamp, self.data]

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

  def appendData(self, newDP, statusCallback = None, hourCallback = None,
    dayCallback = None):
    """
    take a new wwDataPoint, update the buffers, and fire the appropriate
    callbacks to send data to browsers
    newDP: wwDataPoint
    """
    # given a wwDataPoint, add it to the necessary lists
    if(self.__checkHourThresh(newDP)):
      print("added new hour buf data")
      # print(repr(self.hourbuf.getBuf()))
      self.hourbuf.append(newDP)
      # then, fire optional callbacks to push data to browser
      if(statusCallback != None):
        statususCallback(newDP)
      if(hourCallback != None):
        hourCallback(newDP)
    if(self.__checkDayThresh(newDP)):
      self.daybuf.append(newDP)


  def newSubscription(self, name, type):
    """
    register a new subscription to a node's data
    name: web client id
    type: status, hour, day
    """
    self.subs[type].append(name)

  def delSubscription(self, name, type):
    self.subs[type].remove(name)

  def powerOn(self):
    pass

  def powerOff(self):
    pass

  def recallHistory(self, type):
    """
    take a type of history and return the 2D list of datapoint objects
    type: day, hour
    """
    # pick a buffer
    if(type == "day"):
      buf = self.daybuf
    else:
      buf = self.hourbuf
    # build the output list
    listOut = []
    for dp in buf.getBuf():
      listOut.append(dp.getListObj)
    return listOut










