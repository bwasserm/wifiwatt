$(document).ready(function() {
  var conn = null;

  // web console call
  function log(text) {
    msg = '<div class="text">' + text + '</span>\n';
    var webConsole = $('#console');
    webConsole.html(webConsole.html() + msg);
    console.log(text)
  }

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
      log('Received: ' + e.data);
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
      request.hostname = nodeObj.name
      request.subType = type;
      conn.sendJson(request);
    }
    conn.delSubscription = function() {
      request = new Object();
      request.type = "delSubscription";
      request.hostname = nodeObj.name
      request.subType = type;
      conn.sendJson(request);
    }
  }

  app = new Object();
  // holds local current data caches
  app.statusData = new Object();
  app.hourData = new Object();
  app.dayData = new Object();

  // manages what our current nodes are
  app.nodes = new Object(); // holds nodeObj(Object)
  app.selectedNodes = new Array(); // holds jQuery Objects

  // state memory
  app.graphWindow = "null"
  app.conn = null;

  app.addNode = function(hostname) {
    // create the new object and fill in fields
    nodeObj = new Object();
    nodeObj.id = "node-" + hostname;
    nodeObj.pwrId = "power-" + hostname;
    nodeObj.name = hostname;
    // add obj to app's node list
    if(hostname in app.nodes) {
      log("Already had " + hostname + "in node list! Not adding.");
      return;
    } else {
      log("Added node "+ hostname + ".");
      app.nodes[hostname] = nodeObj;
    }
  };

  app.getNodeFromId = function(id) {
    hostname = id.slice(5); // truncate the node- prefix
    return app.getNodeFromHN(hostname);
  };
  app.getNodeFromPwrId = function(pwrId) {
    hostname = id.slice(5); // truncate the node- prefix
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
    // send message to server
    conn.reqSubscription(type, nodeObj);
  };

  app.delSubscription = function(type, nodeObj) {
    log("removed subscription");
    // delete timeline element/remove from graph
    // send notification to server
    conn.delSubscription(type, nodeObj);
  };



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
      hostname = msg["nodes"][i];
      nodeListElem = $('#nodeList');
      newNodeElem = '      <div class="nodeContainer">\
        <label>\
          <input type="checkbox" class="nodeSelect" name="node-'+hostname+'" id="node-'+hostname+'" value="" />\
          <span class="nodeName">'+hostname+'</span>\
        </label>\
        <input type="checkbox" class="nodePower" name="power-'+hostname+'" id="power-'+hostname+'" value="" />\
      </div>\n';
      nodeListElem.append(newNodeElem);
    };
    ui.rehandleNodeList()

    // ask for status subscription
    // app.addSubscription("status", newNodeElem);
    // just kidding. the server handles this when a new sockjs conn opens
  };

  handlers.newData = function(e) {
    log("new message: " + e.data);
  };

  handlers.uiNodeSelect = function(e) {
    log("new node selected");
  };

  handlers.uiNodePower = function(e) {
    log("new power command");
  }

  handlers.uiGraphWindowChange = function(e) {
    // alert($("input#graphWindow[type=checked]").is(':checked'));
    if($("div#graphWindowSel input#graphWindow[type=checkbox]").attr('checked')) {
      app.graphWindow = "hour"
    } else {
      app.graphWindow = "day"
    }
    log("Set graph type to " + app.graphWindow + ".");
    // tell server
    // remove timelines from graph
    // destroy timeline cache
    // build new timelines
    // scale graph
    // add new timelines to graph
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
    $("div#nodeList input.nodeSelect").change(handlers.uiNodeSelect);
    $("div#nodeList input.nodePower").change(handlers.uiNodePower);
  };
  ui.rehandleNodeList();
  

  // sockjs handler installations //////////////////////////////////////////////
  connect(handlers, app);
});