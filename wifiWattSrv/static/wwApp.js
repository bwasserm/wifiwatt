$(document).ready(function() {
  var conn = null;

  // web console call
  // function log(text) {
  //   msg = '<div class="text">' + text + '</span>\n';
  //   var webConsole = $('#console');
  //   webConsole.html(webConsole.html() + msg);
  //   console.log(text)
  // }
  function log(text) {}

  // sockJS
  function connect(handlers, app) {
    conn = new SockJS('http://' + window.location.host + '/socket');

    log('Connecting...');

    conn.onopen = function() {
      log('Connected.');
      app.conn = conn;
    };

    conn.onmessage = function(e) {
      // log and parse the message
      
      log('Received: (' + ') ' + e.data);
      var newMsg = JSON.parse(e.data);
      // sanity check for message validity
      if("type" in newMsg) {
        // dispatch message to proper handler
        var type = newMsg["type"]
        if(type == "newNodes") {
          handlers.newNodes(newMsg);
        }
        else if(type == "newData") {
          handlers.newData(newMsg);
        }
        else if(type == "timeFix") {
          app.timeFixHandler(newMsg)
        }
      }
      else {
        log("Received message without type!");
      }
    };

    conn.onclose = function() {
      log('Disconnected.');
      conn = null;
      update_ui();
    };

    conn.sendJson = function(msgObj) {
      jsonMsg = JSON.stringify(msgObj);
      conn.send(jsonMsg);
    }
    conn.reqSubscription = function(type, nodeObj) {
      request = new Object();
      request.type = "subscription";
      request.hostname = nodeObj.name;
      request.subType = type;
      conn.sendJson(request);
    }
    conn.delSubscription = function(type, nodeObj) {
      request = new Object();
      request.type = "delSubscription";
      request.hostname = nodeObj.name;
      request.subType = type;
      conn.sendJson(request);
    }
    conn.powerCmd = function(nodeObj, newPwrVal) {
      request = new Object();
      request.type = "nodePower";
      request.pwrVal = newPwrVal;
      request["nodeName"] = nodeObj.name; //"applepi"; 
      request.rawr = "Rawr!"
      conn.sendJson(request)
    }
  }

  app = new Object();
  // holds local current data caches
  app.statusData = new Object();
  app.hourData = new Object();
  app.detailData = new Object();
  app.dayData = new Object();

  // manages what our current nodes are
  app.nodes = new Object(); // holds nodeObj(Object)
  app.selectedNodes = new Array(); // holds jQuery Objects

  // state memory
  app.graphWindow = "null"
  app.conn = null;

  // time skew fix
  app.serverTimeSkew = 0
  app.timeFixHandler = function(msgJson) {
    serverTime = parseFloat(msgJson.serverTime);
    serverTimeMS = serverTime * 1000;
    var d = new Date();
    var clientTime = d.getTime();
    app.serverTimeSkew = clientTime - serverTimeMS;
    console.log(app.serverTimeSkew);
  };


  app.addNode = function(hostname) {
    // create the new object and fill in fields
    nodeObj = new Object();
    nodeObj.id = "node-" + hostname;
    nodeObj.pwrId = "power-" + hostname;
    nodeObj.contId = "cont-" + hostname;
    nodeObj.name = hostname;
    nodeObj.pwrState = false; // 0 = off, 1 = on, 2 = transitory
    // add obj to app's node list
    if(hostname in app.nodes) {
      log("Already had " + hostname + "in node list! Not adding.");
      // grab the existing node object
      nodeObj = null;
    } else {
      log("Added node "+ hostname + ".");
      app.nodes[hostname] = nodeObj;
    }
    return nodeObj;
  };

  app.getNodeFromId = function(id) {
    hostname = id.slice(5); // truncate the node- prefix
    return app.getNodeFromHN(hostname);
  };
  app.getNodeFromPwrId = function(pwrId) {
    hostname = pwrId.slice(6); // truncate the node- prefix
    return app.getNodeFromHN(hostname);
  };
  app.getNodeFromHN = function(hostname) {
    // lookup if exists
    if(!(hostname in app.nodes)) {
      log("Request for node with mystery hostname!")
      return -1;
    }
    return app.nodes[hostname];
  };

  // what subscriptions we have
  app.addSubscription = function(type, nodeObj) {
    log("added subscription");
    // make a timeline element
    var newDetailSeries = new TimeSeries()
    var newSeries = new TimeSeries();
    if(type == "hour") {
      app.detailData[nodeObj.name] = newDetailSeries;
      app.hourData[nodeObj.name] = newSeries;
    } else if(type == "day") {
      app.dayData[nodeObj.name] = newSeries;
    }
    // add to graph
    opts = { strokeStyle:'rgb(0, 168, 0)', fillStyle:'rgba(0, 168, 0, 0.2)', lineWidth:3 };
    detailSmoothie.addTimeSeries(newDetailSeries, opts);
    smoothie.addTimeSeries(newSeries, opts);
    // send message to server
    conn.reqSubscription(type, nodeObj);
  };

  app.delSubscription = function(type, nodeObj) {
    log("removed subscription");
    // delete timeline element/remove from graph
    dts = app.detailData[nodeObj.name];
    ts = app.hourData[nodeObj.name];
    detailSmoothie.removeTimeSeries(dts);
    smoothie.removeTimeSeries(ts);
    delete app.hourData[nodeObj.name];
    // send notification to server
    conn.delSubscription(type, nodeObj);
  };

  // deal with power commands in the interface
  app.toggleNodePwr = function(nodeObj, nodePwrStatus) {
    log("Disabling " + nodeObj.name + "'s power control.");
    // disable control and set state
    // nodeObj.pwrState = 2;
    $("div#nodeList input#" + nodeObj.pwrId + "").attr("disabled", true)
    // send request
    conn.powerCmd(nodeObj, nodePwrStatus);
  }
  app.enableNodePwr = function(nodeObj, nodePwrStatus) {
    // update the power part of the ui
    // check if we're in a transition
    inTrans = $("div#nodeList input#" + nodeObj.pwrId + "");
    // console.log("nodePwrStatus: " + nodePwrStatus + " nodeObj.pwrState: " + nodeObj.pwrState);

    if(nodePwrStatus != nodeObj.pwrState) {
      // the node successfully changed state; enable and update state
      // caveot: this could be triggered by someone else. no harm done.
      $("div#nodeList input.nodePower#" + nodeObj.pwrId + "")
        .removeAttr("disabled")
        .attr("checked", nodePwrStatus);
      nodeObj.pwrState = nodePwrStatus;
    }
  }
  app.updateNodeStatus = function(nodeObj, msgData) {
    // update power btn
    app.enableNodePwr(nodeObj, msgData.relayState);
    // update text
    current = msgData.dataPoints[0].data;
    power = current * 120; // assume 120V system
    current = Math.round(current*100) / 100; // round current
    power = Math.round(power*10) / 10;
    statusText = "Current: " + current + "A&nbsp;&nbsp;&nbsp;&nbsp;Power: " + power + "W";

    $("div#nodeList div#"+nodeObj.contId+" div.currentVal").html(statusText);
    // update color indicator
    if(nodeObj.pwrState == false) {
      // device is off. grey indicator
      color = "#cccccc"
    } else if (current < 7.5) {
      color = "#00FF00"
    } else if (current < 12.5) {
      color = "#FFFF00"
    } else {
      color = "#FF0000"
    }
    $("div#nodeList div#"+nodeObj.contId+"").css("border-left-color", color);
  }



  handlers = new Object();

  handlers.newNodes = function(msg) {
    // check message structure
    if(!("nodes" in msg)) {
      log("No nodes in newNodes message!");
      return -1;
    }
    log("Got new nodes!");

    // update the ui list
    for (var i = msg.nodes.length - 1; i >= 0; i--) {
      // parse hostname
      hostname = msg["nodes"][i];

      // make node object
      newNodeObj = app.addNode(hostname);
      if(newNodeObj == null) {
        return -1;
      }

      // add to the ui
      nodeListElem = $('#nodeList');
      newNodeHTML = '      <div class="nodeContainer" id="'+newNodeObj.contId+'">\
        <div class="nodeGraphCtrl">Graph\
          <div class="squaredTwo">\
            <input type="checkbox" class="nodeSelect" name="'+newNodeObj.id+'" id="'+newNodeObj.id+'" value="" />\
            <label for="'+newNodeObj.id+'" class="nodeLabel"></label>\
          </div>\
        </div>\
          <h1 class="nodeName">'+newNodeObj.name+'</h1>\
          <div class="currentVal">0.00</div>\
        <div class="nodePowerCtrl">Power\
          <div class="squaredOne"><input type="checkbox" class="nodePower" name="'+newNodeObj.pwrId+'" id="'+newNodeObj.pwrId+'" value="" /><label for="'+newNodeObj.pwrId+'"></label></div>\
        </div>\
      </div>\n';
      nodeListElem.append(newNodeHTML);
    };
    ui.rehandleNodeList()

    // ask for status subscription
    // app.addSubscription("status", newNodeElem);
    // just kidding. the server handles this when a new sockjs conn opens
  };

  handlers.newData = function(msgData) {
    if(!("subType" in msgData && "nodeName" in msgData)) {
      log("New data message malformed!");
      return -1;
    }
    if(msgData.subType == "status") {
      // never need to ignore this
      // check hostname
      nodeObj = app.getNodeFromHN(msgData.nodeName);
      if(nodeObj == -1) {
        log("Status update from unknown node " + msgData.nodeName + "!");
        return -1;
      }
      // call app node updater
      app.updateNodeStatus(nodeObj, msgData)

    } else if (msgData.subType == "hour") {

      // ignore unnecessary data
      if(app.graphWindow != "hour") {
        return -1;
      }
      // get node and timeline obj
      nodeObj = app.getNodeFromHN(msgData.nodeName);
      if(nodeObj == -1) {
        log("Status update from unknown node " + msgData.nodeName + "!");
        return -1;
      }
      dts = app.detailData[nodeObj.name];
      ts = app.hourData[nodeObj.name];
      // plot the points on the graph
      points = msgData.dataPoints;
      for (var i = points.length - 1; i >= 0; i--) {
        // convert from server time (floats sec)
        timestampS = points[i].timestamp;
        timestampMS = timestampS * 1000;
        timestampMS = timestampMS + app.serverTimeSkew;
        // var d = new Date();
        // var time = d.getTime();
        // console.log("server: " + timestampMS + " client: " + time);
        dts.append(timestampMS, points[i].data);
        ts.append(timestampMS, points[i].data);
      };


    } else if (msgData.subType == "day") {
      
      // ignore unnecessary data
      if(app.graphWindow != "day") {
        return -1;
      }
      // get node and timeline obj
      nodeObj = app.getNodeFromHN(msgData.nodeName);
      if(nodeObj == -1) {
        log("Status update from unknown node " + msgData.nodeName + "!");
        return -1;
      }
      ts = app.dayData[nodeObj.name];
      // plot the points on the graph
      points = msgData.dataPoints;
      for (var i = points.length - 1; i >= 0; i--) {
        // convert from server time (floats sec)
        timestampS = points[i].timestamp;
        timestampMS = timestampS * 1000;
        timestampMS = timestampMS + app.serverTimeSkew;
        ts.append(timestampMS, points[i].data);
      };

    }
  };

  handlers.uiNodeSelect = function(e) {
    log("new node selected");
    // grab node object
    nodeId = $(this).attr("name");
    nodeSubStatus = $(this).is(":checked");
    nodeObj = app.getNodeFromId(nodeId);
    if(nodeSubStatus) {
      // request a subscription
      app.addSubscription(app.graphWindow, nodeObj);
    }
    else {
      // delete the subscription
      app.delSubscription(app.graphWindow, nodeObj);
    }
    
  };

  handlers.uiNodePower = function(e) {
    log("new power command");
    // grab node object
    nodePwr = $(this).attr("name");
    nodePwrStatus = $(this).is(":checked"); // return True = on
    nodeObj = app.getNodeFromPwrId(nodePwr);
    log(nodeObj);
    app.toggleNodePwr(nodeObj, nodePwrStatus);
  }

  handlers.uiGraphWindowChange = function(e) {
    // alert($("input#graphWindow[type=checked]").is(':checked'));
    if($("div#graphWindowSel input#graphWindow[type=checkbox]").attr('checked')) {
      app.graphWindow = "hour"
    } else {
      app.graphWindow = "day"
    }
    console.log("Set graph type to " + app.graphWindow + ".");
    // tell server
    // remove timelines from graph
    // destroy timeline cache
    // build new timelines
    // scale graph
    // add new timelines to graph
  }

  handlers.uiSelectAll = function(e) {
    $(this)
  }

  handlers.uiSelectNone = function(e) {
    $(this)
  }

  // ui handler installations //////////////////////////////////////////////////
  ui = new Object();

  // data window
  $("div#nodeList form").submit(function() {return false;}); // disable submit
  $("div#graphWindowSel input#graphWindow[type=checkbox]")
    .change(handlers.uiGraphWindowChange)
    .trigger("change");
  // handlers.uiGraphWindowChange(null);
  

  // node list
  $("div#nodeList #form").submit(function() {return false;});
  ui.rehandleNodeList = function() {
    $("div#nodeList input").unbind();
    $("div#nodeList input.nodeSelect").change(handlers.uiNodeSelect);
    $("div#nodeList input.nodePower").change(handlers.uiNodePower);
  };
  ui.rehandleNodeList();

  // node list selection btns
  $("a#nodeListSA").click(handlers.uiSelectAll);
  $("a#nodeListSN").click(handlers.uiSelectNone);
  

  // sockjs handler installations //////////////////////////////////////////////
  connect(handlers, app);

  // smoothie chart inits //////////////////////////////////////////////////////
  detailOpts = {
    "maxValue": "20",
    "minValue": "0",
    "millisPerPixel": 60,
    "grid": {
      fillStyle: '#333',
      strokeStyle: '#555',
      lineWidth: 1,
      millisPerLine: 960,
      verticalSections: 4 
    }
  }
  opts = {
    "maxValue": "20",
    "minValue": "0",
    "millisPerPixel": 600,
    "grid": {
      fillStyle: '#333',
      strokeStyle: '#555',
      lineWidth: 1,
      millisPerLine: 9600,
      verticalSections: 4 
    }
  }
  var detailSmoothie = new SmoothieChart(detailOpts);
  detailSmoothie.streamTo(document.getElementById("detailGraphCanvas"), 400);
  var smoothie = new SmoothieChart(opts);
  smoothie.streamTo(document.getElementById("graphCanvas"), 400);

});




