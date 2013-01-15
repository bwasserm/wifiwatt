wifiwatt
========

Build18 Project to make a TCP/IP based current monitoring and circuit switching devices.

Members:
Ben (bwasserm@)
Neil (nabcouwe@)
Ian (ihartwig@)
Andrew (amort@)


I've been using the following guide for programming the ADC functionality:
http://www.avrfreaks.net/index.php?name=PNphpBB2&file=viewtopic&t=56429

Notes:
The Clock on TWI runs at 100.0kHz. This means that it can transmit 2 bytes idealy at 3.7kHz (but probably less due to numerous factors).
The ADC can read samples at a rate of 9.6kHz. Since they are so close in speed, its probably not worth it to do RMS math on the AVR.
This means there are about 33 clock cycles on the AVR to do any math between TWI transmits. This could be enough to average the latest 3 readings, and transmit that, producing slightly better data.
