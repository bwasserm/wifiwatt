#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <amqp.h>
#include <amqp_framing.h>
#include <sys/mman.h>
#include <fcntl.h>
#include "utils.h"
#include <assert.h>
#include <errno.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>

#define PAGE_SIZE (4*1024)
#define BLOCK_SIZE (4*1024)

// Pi values
#define PI                "applepi"
#define HOSTNAME          "lambdadev.pc.cc.cmu.edu"
#define PORT              5672
#define EXCH_VALUE_NAME   "ww.valueUpdate"
#define EXCH_MESS_NAME    "ww.messages"
#define EXCH_VALUE_TYPE   "fanout"
#define EXCH_MESS_TYPE    "topic"
#define QUEUE_HAND_NAME   "node." PI ".handshake"
#define QUEUE_CMD_NAME    "node." PI ".cmd"
#define ROUTE_HAND_NAME   QUEUE_HAND_NAME
#define ROUTE_CMD_NAME    QUEUE_CMD_NAME
#define ROUTE_HAND_SEND   "server.ANYHOST.handshake"

#define BUF_LEN           65536
#define HANDSHAKE_STR     "handshake test string"

#define ADC_MULT          0.0722735
#define ADC_MAX_LEN       200

// GPIO defines
#define BCM2708_PERI_BASE        0x20000000
#define GPIO_BASE                (BCM2708_PERI_BASE + 0x200000) /* GPIO controller */

// GPIO setup macros. Always use INP_GPIO(x) before using OUT_GPIO(x) or SET_GPIO_ALT(x,y)
#define INP_GPIO(g) *(gpio+((g)/10)) &= ~(7<<(((g)%10)*3))
#define OUT_GPIO(g) *(gpio+((g)/10)) |=  (1<<(((g)%10)*3))
#define SET_GPIO_ALT(g,a) *(gpio+(((g)/10))) |= (((a)<=3?(a)+4:(a)==4?3:2)<<(((g)%10)*3))

#define GPIO_SET *(gpio+7)  // sets bits which are 1 ignores bits which are 0
#define GPIO_CLR *(gpio+10) // clears bits which are 1 ignores bits which are 0
#define GPIO_READ *(gpio+13) // read bits which are 1

#define RELAY_NUM 14

// Location of i2c 
#define I2C_DEV "/dev/i2c-1"

// Address of device
#define ADDRESS 0x2a

// I2C sync constants
#define ZERO_MASK 0xFC

// GPIO variables
int  mem_fd;
unsigned *gpio_map;
volatile unsigned *gpio;

// Global variables for names of things used in multiple functions
amqp_bytes_t queue_hand_name;
amqp_bytes_t queue_cmd_name;
amqp_bytes_t exch_value_name;
amqp_bytes_t exch_mess_name;
amqp_bytes_t exch_value_type;
amqp_bytes_t exch_mess_type;
amqp_bytes_t route_hand_name;
amqp_bytes_t route_cmd_name;

ssize_t get_body(amqp_connection_state_t conn, char* buf, size_t buf_len);
int perform_handshake(amqp_connection_state_t conn);
amqp_connection_state_t connect_server(void);
int report_error(int x, char const *context);
int report_amqp_error(amqp_rpc_reply_t x, char const *context);
void setup_io(void);
int init_ADC(void);
int16_t get_ADC(int fd);

int main(void) {
  char buf[BUF_LEN];
  ssize_t mes_len;
  amqp_connection_state_t conn;

  // Set global strings 
  queue_hand_name = amqp_cstring_bytes(QUEUE_HAND_NAME);
  queue_cmd_name = amqp_cstring_bytes(QUEUE_CMD_NAME);
  exch_value_name = amqp_cstring_bytes(EXCH_VALUE_NAME);
  exch_mess_name = amqp_cstring_bytes(EXCH_MESS_NAME);
  exch_value_type = amqp_cstring_bytes(EXCH_VALUE_TYPE);
  exch_mess_type = amqp_cstring_bytes(EXCH_MESS_TYPE);
  route_hand_name = amqp_cstring_bytes(ROUTE_HAND_NAME);
  route_cmd_name = amqp_cstring_bytes(ROUTE_CMD_NAME);

  // Set up gpi pointer for direct register access
  setup_io();

  // Switch GPIO 7 to output mode
  INP_GPIO(RELAY_NUM);
  OUT_GPIO(RELAY_NUM);

  while(1){
    if((conn = connect_server()) == NULL){
      continue;
    }

    printf("Finish connect\n");

    if(!perform_handshake(conn)){
      continue;
    }
    printf("Finish handshake\n");

    if(fork() == 0){  // Child process
      uint8_t relay_state;
      int16_t val, adc_max;
      double current;
      int adc_fd;
      

      if((adc_fd = init_ADC()) < 0){
        fprintf(stderr, "Cannot open ADC fd\n");
        exit(1);
      }
  
      while(1){
        adc_max = 0;
        for(int i = 0; i < ADC_MAX_LEN; i++){
          if((val = get_ADC(adc_fd)) < 0){
            exit(1);
          }

          if(adc_max < val){
            adc_max = val;
          }
        }

        current = adc_max * ADC_MULT;
        relay_state = ((GPIO_READ >> RELAY_NUM) & 1);
        sprintf(buf, "{\"hostname\": \"%s\", \"current\": \"%f\", \"relayState\": \"%d\"}", 
          PI, current, relay_state & 1);
  
        // Publish values to server
        if(!report_error(amqp_basic_publish(conn, 1, exch_value_name, 
            amqp_empty_bytes, 0, 0, NULL, amqp_cstring_bytes(buf)), "Publishing")){
          exit(1);
        }
      }
    }
  
    if(fork() == 0){  // Child process
      // Consume cmd queue
      amqp_basic_consume(conn, 1, queue_cmd_name, amqp_empty_bytes, 0, 1, 0, 
        amqp_empty_table);
      if(!report_amqp_error(amqp_get_rpc_reply(conn), "consuming cmd queue")){
        exit(1);
      }
  
      while(1){
        amqp_frame_t frame;
  
        if(!report_error(amqp_simple_wait_frame(conn, &frame), 
            "waiting for header frame")){
          exit(1);
        }
  
        if(frame.frame_type != AMQP_FRAME_METHOD || 
            frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD)
          continue;
  
        if((mes_len = get_body(conn, buf, BUF_LEN)) < 0){
          exit(1);
        }
  
        if(buf[0] == '0'){
          GPIO_CLR = 1 << RELAY_NUM; 
        }else if(buf[0] == '1'){
          GPIO_SET = 1 << RELAY_NUM; 
        }else{
          fprintf(stderr, "Error: Unknown relay code %c\n", buf[0]);
        }
  
        amqp_maybe_release_buffers(conn);
      }
    }
  
    //TODO implement wait
    while(1)
      ;
  
  }

  die_on_amqp_error(amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS), "Closing channel");
  die_on_amqp_error(amqp_connection_close(conn, AMQP_REPLY_SUCCESS), "Closing connection");
  die_on_error(amqp_destroy_connection(conn), "Ending connection");
}



amqp_connection_state_t connect_server(){
  int sockfd;
  amqp_connection_state_t conn = amqp_new_connection();

  // Open socket and set fd
  if(!report_error(sockfd = amqp_open_socket(HOSTNAME, PORT), "Opening socket")){
    return NULL;
  }
  amqp_set_sockfd(conn, sockfd);

  // Set login creds
  if(!report_amqp_error(amqp_login(conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN, 
    "guest", "guest"), "Logging in")){
    return NULL;
  }

  // Open channel 1 and check it went through
  amqp_channel_open(conn, 1);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Opening channel")){
    return NULL;
  }

  // Declare handshake queue
  amqp_queue_declare(conn, 1, queue_hand_name, 0, 0, 0, 0, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Declaring handshake queue")){
    return NULL;
  }

  // Declare cmd queue
  amqp_queue_declare(conn, 1, queue_cmd_name, 0, 0, 0, 0, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Declaring cmd queue")){
    return NULL;
  }

  // Declare value exchange
  amqp_exchange_declare(conn, 1, exch_value_name, exch_value_type, 0, 0, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Declaring value exchange")){
    return NULL;
  }

  // Declare messages exchange
  amqp_exchange_declare(conn, 1, exch_mess_name, exch_mess_type, 0, 0, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Declaring messages exchange")){
    return NULL;
  }

  // Bind handshake queue to messages exchange
  amqp_queue_bind (conn, 1, queue_hand_name, exch_mess_name, route_hand_name, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Bind handshake queue to messages exchange")){
    return NULL;
  }

  // Bind command queue to messages exchange
  amqp_queue_bind (conn, 1, queue_cmd_name, exch_mess_name, route_cmd_name, amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "Bind cmd queue to messages exchange")){
    return NULL;
  }

  return conn;
}

// Return 0 on error, 1 on success
int perform_handshake(amqp_connection_state_t conn){
  ssize_t mes_len;
  char buf[BUF_LEN];
  amqp_frame_t frame;

  // Publish handshake to server
  if(!report_error(amqp_basic_publish(conn, 1, exch_mess_name, 
      amqp_cstring_bytes(ROUTE_HAND_SEND), 0, 
      0, NULL, amqp_cstring_bytes(PI)), "Message Publish")){
    return 0;
  }

  printf("publish message\n");

  amqp_basic_consume(conn, 1, queue_hand_name, amqp_empty_bytes, 0, 1, 0, 
    amqp_empty_table);
  if(!report_amqp_error(amqp_get_rpc_reply(conn), "consuming cmd queue")){
    return 0;
  }

  if(!report_error(amqp_simple_wait_frame(conn, &frame),
    "waiting for header frame")){
    return 0;
  }

  if(frame.frame_type != AMQP_FRAME_METHOD || 
      frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD)
    fprintf(stderr, "Error: handshake wrong frame or method\n");

  if((mes_len = get_body(conn, buf, BUF_LEN)) < 0){
    fprintf(stderr, "Error: handshake get body\n");
  }

  printf("Handshake: %.*s\n", mes_len, buf);

  amqp_maybe_release_buffers(conn);

  return 1;
}

ssize_t get_body(amqp_connection_state_t conn, char* buf, size_t buf_len){
  size_t body_remaining, body_size;
  amqp_frame_t frame;

  if(buf == NULL || buf_len < 50){
    return -1;
  }

  // Get next frame
  if(amqp_simple_wait_frame(conn, &frame) < 0){
    fprintf(stderr, "Error: Waiting for header frame.\n");
    return -1;
  }

  // Make sure frame is header
  if(frame.frame_type != AMQP_FRAME_HEADER){
    fprintf(stderr, "Error: Expected header, got frame type 0x%X.\n", frame.frame_type);
    return -1;
  }
  
  body_size = frame.payload.properties.body_size;
  body_remaining = body_size;

  // Copy the whole body into the buffer
  while(body_remaining){
    // Get next frame
    if(amqp_simple_wait_frame(conn, &frame) < 0){
      fprintf(stderr, "Error: Waiting for body frame.\n");
      return -1;
    }

    // Make sure frame is body
    if(frame.frame_type != AMQP_FRAME_BODY){
      fprintf(stderr, "Error: Expected body, got frame type 0x%X.\n", frame.frame_type);
      return -1;
    }

    if(buf_len < frame.payload.body_fragment.len){
      fprintf(stderr, "Error: Not enough space in buffer for body.\n");
      return -1;
    }

    memcpy(buf, frame.payload.body_fragment.bytes, frame.payload.body_fragment.len);

    buf_len -= frame.payload.body_fragment.len;
    body_remaining -= frame.payload.body_fragment.len;
  }

  return (ssize_t)body_size;
}

// Return 0 on error, 1 on no error
int report_error(int x, char const *context) {
  if (x < 0) {
    char *errstr = amqp_error_string(-x);
    fprintf(stderr, "%s: %s\n", context, errstr);
    free(errstr);
    return 0;
  }

  return 1;
}

// Return 0 on error, 1 on no error
int report_amqp_error(amqp_rpc_reply_t x, char const *context) {
  switch (x.reply_type) {
    case AMQP_RESPONSE_NORMAL:
      return 1;

    case AMQP_RESPONSE_NONE:
      fprintf(stderr, "%s: missing RPC reply type!\n", context);
      break;

    case AMQP_RESPONSE_LIBRARY_EXCEPTION:
      fprintf(stderr, "%s: %s\n", context, amqp_error_string(x.library_error));
      break;

    case AMQP_RESPONSE_SERVER_EXCEPTION:
      switch (x.reply.id) {
        case AMQP_CONNECTION_CLOSE_METHOD: {
          amqp_connection_close_t *m = (amqp_connection_close_t *) x.reply.decoded;
          fprintf(stderr, "%s: server connection error %d, message: %.*s\n",
            context, m->reply_code, (int) m->reply_text.len, (char *) m->reply_text.bytes);
          break;
        }
        case AMQP_CHANNEL_CLOSE_METHOD: {
          amqp_channel_close_t *m = (amqp_channel_close_t *) x.reply.decoded;
          fprintf(stderr, "%s: server channel error %d, message: %.*s\n",
          context, m->reply_code, (int) m->reply_text.len, (char *) m->reply_text.bytes);
          break;
        }
        default:
          fprintf(stderr, "%s: unknown server error, method id 0x%08X\n", context, x.reply.id);
          break;
      }
      break;
  }

  return 0;
}

//
// Set up memory regions to access GPIO
//
void setup_io()
{
  /* open /dev/mem */
  if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) 
  {
    printf("can't open /dev/mem \n");
    exit(-1);
  }

  /* mmap GPIO */
  gpio_map = (unsigned *)mmap(
      NULL,             //Any adddress in our space will do
      BLOCK_SIZE,       //Map length
      PROT_READ|PROT_WRITE,// Enable reading & writting to mapped memory
      MAP_SHARED,       //Shared with other processes
      mem_fd,           //File to map
      GPIO_BASE         //Offset to GPIO peripheral
      );

  close(mem_fd); //No need to keep mem_fd open after mmap

  if ((long)gpio_map < 0) {
    printf("Error: GPIO mmap error %d\n", (int)gpio_map);
    exit(-1);
  }

  // Always use volatile pointer!
  gpio = (volatile unsigned *)gpio_map;    

} // setup_io

// Open fd and set up as i2c (-1 on error)
int init_ADC(void){
    int fd;

    // Open file for read and write
    if((fd = open(I2C_DEV, O_RDWR)) < 0){
        fprintf(stderr, "Error: Init ADC error - %s\n", strerror(errno));
        return -1;
    }

    // Set up for i2c with slave at the address
    if(ioctl(fd, I2C_SLAVE, ADDRESS) < 0){
        fprintf(stderr, "Error: ADC ioctl error - %s\n", strerror(errno));
        return -1;
    }

    return fd;
}

// Get the 16 bit value from the ADC (-1 on error)
int16_t get_ADC(int fd){
    char buf[2] = {0};

    // Using I2C Read
    if(read(fd, buf, 1) != 1) {
        fprintf(stderr, "Error: Get ADC read error - %s\n", strerror(errno));
        return -1;
    }

    return (int16_t)((uint16_t) buf[0]);
}
