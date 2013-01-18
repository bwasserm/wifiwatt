#!/bin/bash

WIFIWATT="/home/pi/wifiwatt"
PROG="$WIFIWATT/AMQP_pi/amqp_wifiwatt.c"
COMP="$WIFIWATT/rabbitmq-c/examples/amqp_listen.c"
RUN="$WIFIWATT/rabbitmq-c/examples/amqp_listen"
MAKE="$WIFIWATT/rabbitmq-c/"
CUR=`pwd`
FINAL="$WIFIWATT/wifiwatt"

cp $PROG $COMP
cd $MAKE
make
cd $CUR
sudo $RUN
