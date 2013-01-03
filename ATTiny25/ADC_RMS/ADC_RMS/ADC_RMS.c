/*
 * ADC_RMS.c
 *
 * Created: 1/1/2013 15:36:32 PM
 *  Author: bwasserm
 */ 


#include <avr/io.h>
#include "usiTwiSlave.h"

#define TWI_ADDRESS 42

int main(void)
{
	// Setup variables
	uint8_t count = 0;
	
	// Setup AVR
	
	// Setup ADC
	
	// Setup I2C
	usiTwiSlaveInit( (uint8_t)TWI_ADDRESS );
	
    while(1)
    {
        // Read ADC
		
		// Calculate RMS
		
		// Transmit Data
		if(usiTwiDataInTransmitBuffer() == false){
			usiTwiTransmitByte(count);
			count++;
		}			
    }
}