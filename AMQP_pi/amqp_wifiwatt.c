#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <stdint.h>
#include <amqp.h>
#include <amqp_framing.h>

#include <assert.h>

#include "utils.h"

#define PI                "applepi"
#define HOSTNAME          "lambdadev.pc.cc.cmu.edu"
#define PORT              5672
#define EXCH_VALUE_NAME   "ww.valueUpdate"
#define EXCH_MESS_NAME    "ww.messages"
#define EXCH_VALUE_TYPE   "amq.fanout"
#define EXCH_MESS_TYPE    "amq.topic"
#define QUEUE_HAND_NAME   "node." PI ".handshake"
#define QUEUE_CMD_NAME    "node." PI ".cmd"
#define ROUTE_HAND_NAME   QUEUE_HAND_NAME
#define ROUTE_CMD_NAME    QUEUE_CMD_NAME

#define BUF_LEN           65536
#define HANDSHAKE_STR     "handshake test string"

#define ADC_MAX           255
#define ADC_VOLT          3.3
#define ADC_RES           300

// Global variables for names of things used in multiple functions
const amqp_bytes_t queue_hand_name;
const amqp_bytes_t queue_cmd_name;
const amqp_bytes_t exch_value_name;
const amqp_bytes_t exch_mess_name;
const amqp_bytes_t exch_value_type;
const amqp_bytes_t exch_mess_type;
const amqp_bytes_t route_hand_name;
const amqp_bytes_t route_cmd_name;

size_t get_body(amqp_connection_state_t conn, char* buf, size_t buf_len);
int perform_handshake(amqp_connection_state_t conn);
amqp_connection_state_t connect_server();

int main(int argc, char const * const *argv) {
  char buf[BUF_LEN];
  size_t mes_len;
  int sockfd;
  amqp_connection_state_t conn;
  amqp_frame_t frame;

  // Set global strings 
  queue_cmd_name = amqp_cstring_bytes(QUEUE_CMD_NAME);
  exch_value_name = amqp_cstring_bytes(EXCH_VALUE_NAME);
  exch_mess_name = amqp_cstring_bytes(EXCH_MESS_NAME);
  exch_value_type = amqp_cstring_bytes(EXCH_VALUE_TYPE);
  exch_mess_type = amqp_cstring_bytes(EXCH_MESS_TYPE);
  route_hand_name = amqp_cstring_bytes(ROUTE_HAND_NAME);
  route_cmd_name = amqp_cstring_bytes(ROUTE_CMD_NAME);

  conn = connect_server();
  perform_handshake(conn);

  if(fork() == 0){  // Child process
    uint8_t val;
    double current;

    while(1){
      //val = get_adc();
      val = rand() % 256;
      current = ((double) val / ADC_MAX * ADC_VOLT) / ADC_RES;
      sprintf(buf, "%f", current);

      // Publish values to server
      die_on_error(amqp_basic_publish(conn, 1, exch_value_name, 
        amqp_empty_bytes, 0, 0, NULL, buf), "Publishing");

      microsleep(2000);
    }
  }

  if(fork() == 0){  // Child process
    // Consume cmd queue
    amqp_basic_consume(conn, 1, queue_cmd_name, amqp_empty_bytes, 0, 0, 0, 
      amqp_empty_table);
    die_on_amqp_error(amqp_get_rpc_reply(conn), "Consuming cmd queue");

    while(1){
      amqp_frame_t frame;

      die_amap_error(amqp_simple_wait_frame(conn, &frame), 
        "waiting for header frame");

      if(frame.frame_type != AMQP_FRAME_METHOD || 
          frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD)
        continue;

      if((mes_len = get_body(conn, buf, BUF_LEN)) < 0){
        exit(1);
      }

      // TODO implement command
      printf("Command: %.*s\n", mes_len, buf);

      amqp_maybe_release_buffers(conn);
    }
  }

  while(1)
    ;

  die_on_amqp_error(amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS), "Closing channel");
  die_on_amqp_error(amqp_connection_close(conn, AMQP_REPLY_SUCCESS), "Closing connection");
  die_on_error(amqp_destroy_connection(conn), "Ending connection");

  return 0;
}



amqp_connection_state_t connect_server(){
  amqp_connection_state_t conn = amqp_new_connection();

  // Open socket and set fd
  die_on_error(sockfd = amqp_open_socket(HOSTNAME, PORT), "Opening socket");
  amqp_set_sockfd(conn, sockfd);

  // Set login creds
  die_on_amqp_error(amqp_login(conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN, 
    "guest", "guest"), "Logging in");

  // Open channel 1 and check it went through
  amqp_channel_open(conn, 1);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Opening channel");

  // Declare handshake queue
  amqp_queue_declare(conn, 1, queue_hand_name, 0, 0, 0, 0, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Declaring handshake queue");

  // Declare cmd queue
  amqp_queue_declare(conn, 1, queue_cmd_name, 0, 0, 0, 0, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Declaring cmd queue");

  // Declare value exchange
  amqp_exchange_declare(conn, 1, exch_value_name, exch_value_type, 0, 0, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Declaring value exchange");

  // Declare messages exchange
  amqp_exchange_declare(conn, 1, exch_mess_name, exch_exchange_type, 0, 0, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Declaring messages exchange");

  // Bind handshake queue to messages exchange
  amqp_queue_bind (conn, 1, queue_hand_name, exch_mess_name, route_hand_name, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Bind handshake queue to messages exchange");

  // Bind command queue to messages exchange
  amqp_queue_bind (conn, 1, queue_cmd_name, exch_mess_name, route_cmd_name, amqp_empty_table);
  die_on_amqp_error(amqp_get_rpc_reply(conn), "Bind cmd queue to messages exchange");

  return conn;
}

int perform_handshake(amqp_connection_state_t conn){
  // Publish handshake to server
  die_on_error(amqp_basic_publish(conn, 1, exch_mess_name, amqp_empty_bytes, 0, 
    0, NULL, amqp_cstring_bytes(HANDSHAKE_STR)), "Publishing handshake");

  amqp_rpc_reply_t r;

  r = amqp_basic_get(conn, 1, queue_hand_name, 1);
  die_rpc(r, "basic.get");

  if(r.reply.id == AMQP_BASIC_GET_EMPTY_METHOD){
    printf("Error: Handshake empty method");
  }

  if((mes_len = get_body(conn, buf, BUF_LEN)) < 0){
    exit(1);
  }

  //TODO act on message
  printf("Handshake: %.*s\n", mes_len, buf);

  return 0;
}

size_t get_body(amqp_connection_state_t conn, char* buf, size_t buf_len){
  size_t body_remaining, body_size;
  amqp_frame_t frame;

  if(buf == NULL || buf_len < 50){
    return -1;
  }

  // Get next frame
  if(amqp_simple_wait_frame(conn, &frame) < 0){
    printf("Error: Waiting for header frame.\n");
    return -1;
  }

  // Make sure frame is header
  if(frame.frame_type != AMQP_FRAME_HEADER){
    printf("Error: Expected header, got frame type 0x%X.\n", frame.frame_type);
    return -1;
  }
  
  body_size = frame.payload.properties.body_size;
  body_remaining = body_size;

  // Copy the whole body into the buffer
  while(body_remaining){
    // Get next frame
    if(amqp_simple_wait_frame(conn, &frame) < 0){
      printf("Error: Waiting for body frame.\n");
      return -1;
    }

    // Make sure frame is body
    if(frame.frame_type != AMQP_FRAME_BODY){
      printf("Error: Expected body, got frame type 0x%X.\n", frame.frame_type);
      return -1;
    }

    if(buf_len < frame.payload.body_fragment.len){
      printf("Error: Not enough space in buffer for body.\n");
      return -1;
    }

    memcpy(buf, frame.payload.body_fragment, frame.payload.body_fragment.len);

    buf_len -= frame.payload.body_fragment.len;
    body_remaining -= frame.payload.body_fragment.len;
  }

  return body_size;
}
