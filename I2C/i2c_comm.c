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
    char buf[4] = {0};

    // Using I2C Read
    if(read(fd, buf, 2) != 2) {
        return -1;
    }

    return (int16_t)(((buf[0] & 0b0011) << 8) | buf[1]);
}

int main(){
    int16_t data;
    int fd;

    if((fd = init_ADC()) < 0){
        printf("Failed to open bus: %s\n", strerror(errno));
    }

    while(1){
        if((data = get_ADC(fd)) < 0)
            printf("Failed to read data: %s\n", strerror(errno));
        else
            printf("Data: %d\n", data);
    }

    if(close(fd) < 0)
        printf("Failed to close file: %s\n", strerror(errno));
}
