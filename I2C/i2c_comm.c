// Set up I2C on raspberry pi using http://blog.chrysocome.net/2012/11/raspberry-pi-i2c.html

// This code is based on code found at http://elinux.org/Interfacing_with_I2C_Devices

#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdint.h>

// Location of i2c 
#define I2C_DEV "/dev/i2c-1"

// Address of device
#define ADDRESS 0x2a

// I2C sync constants
#define ZERO_MASK 0xFC

// Open fd and set up as i2c (-1 on error)
int init_ADC(void){
    int fd;

    // Open file for read and write
    if((fd = open(I2C_DEV, O_RDWR)) < 0){
        return -1;
    }

    // Set up for i2c with slave at the address
    if(ioctl(fd, I2C_SLAVE, ADDRESS) < 0){
        return -1;
    }

    return fd;
}

// Get the 16 bit value from the ADC (-1 on error)
int16_t get_ADC(int fd){
    char buf[2] = {0};

    // Using I2C Read
    if(read(fd, buf, 2) != 2) {
        return -1;
    }

    return (int16_t)(((buf[0] & 0b0011) << 8) | buf[1]);
}

// Get a 1 byte value from the ADC
uint8_t get_ADC_byte(int fd){
    uint8_t byte = 0;

    // Using I2C read
    read(fd, &byte, 1);
    return byte;
}

int main(){
    uint8_t data;
    uint8_t h_byte = 0;
    uint8_t l_byte = 0;
    int fd;

    if((fd = init_ADC()) < 0){
        printf("Failed to open bus: %s\n", strerror(errno));
    }

    while(1){
      // Read in 2 bytes
      data = get_ADC_byte(fd);

/*      // Check for sync errors
      h_byte = (uint8_t)(data >> 8);
      l_byte = (uint8_t)(data);

      if((h_byte & ZERO_MASK) != 0){
        // The first byte shouldn't be a high byte.
        if((l_byte & ZERO_MASK) != 0){
          // There is most likely a missing byte. Throw out current data
          printf("Sync error: can't recover. Resyncing...\n");
          continue;
        }
        else{
          // It is possible that the second byte is supposed to be a high byte.
          // Try resyncing by reading one more byte
          printf("Sync error: resyncing...\n");
          h_byte = l_byte;
          l_byte = get_ADC_byte(fd);
        }
      }
*/
      printf("Data: %d\t%x\n", data, data);

/*
** The sync code doesn't support error codes. The AVR doesn't send them anyways
      if((data = get_ADC(fd)) < 0)
            printf("Failed to read data: %s\n", strerror(errno));
        else
            printf("Data: %d\n", data);
*/
    }

    if(close(fd) < 0)
        printf("Failed to close file: %s\n", strerror(errno));
}
