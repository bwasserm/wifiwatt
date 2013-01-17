$(document).ready(function() {
  var conn = null;

  function log(text) {
    msg = '<div class="text">' + text + '</span>\n';
    var webConsole = $('#console');
    webConsole.html(webConsole.html() + msg);
  }

  function connect() {
    conn = new SockJS('http://' + window.location.host + '/socket');

    log('Connecting...');

    conn.onopen = function() {
      log('Connected.');
      // update_ui();
    };

    conn.onmessage = function(e) {
      log('Received: ' + e.data);
    };

    conn.onclose = function() {
      log('Disconnected.');
      conn = null;
      update_ui();
    };
  }

  connect();
});