/*
 * ADC_RMS.c
 *
 * Created: 1/1/2013 15:36:32 PM
 *  Author: bwasserm
 */ 


#include <avr/io.h>
#include <avr/interrupt.h>
#include "usiTwiSlave.h"

#define TWI_ADDRESS 2
#define LED_TOGGLE() (PINB |= (1<<PINB1))

int main(void)
{
	// Setup variables
	uint8_t count = 0;
	int8_t adc_val = 0;
	uint16_t led_counter = 0;
	
	// Setup AVR
	DDRB |= (1<<PB1);							// Set debugging LED output pin
	
	// Setup ADC
	// Set ADC Mux
	ADMUX = (0<<REFS2)|(0<<REFS1)|(0<<REFS0)|	// Use VCC as Vref, disconnected from AREF pin (which is in use as SDA for TWI)
			(1<<ADLAR)|							// Left-shift the ADC result, so the first 8 bits can be read from a single register (ADCH)
//			(0<<MUX3)|(1<<MUX2)|(1<<MUX1)|(0<<MUX0);	// Use difference between PB4 and PB3, with gain of 1x. Use 0111 for 20x gain
			(0<<MUX3)|(0<<MUX2)|(1<<MUX1)|(0<<MUX0);	// Read ADC2 (PB4)
	// Set ADC Control Register A
	ADCSRA = (1<<ADEN)|							// Enable ADC
			(0<<ADSC)|							// Don't start conversion yet
			(0<<ADATE)|							// Disable triggering //so Free Running mode can be set
			(0<<ADIF)|(0<<ADIE)|				// Don't use the ADC interrupt
			(1<<ADPS2)|(1<<ADPS1)|(0<<ADPS0);	// Set the clock prescaler to 64, so the 8MHz CPU clock gets scaled to 125kHz
	// Set ADC Control Register B
	ADCSRB |= (1<<BIN)|							// Enable bipolar input mode, so we can measure positive and negative voltages (for AC)
			(0<<ACME)|							// Disable analog comparator
			(0<<IPR)|							// Don't enable polarity reversal. It doesn't do us any good
			(0<<ADTS2)|(0<<ADTS1)|(0<<ADTS0);	// Set ADC to free running mode, so it continually samples
	// Disable digital pins being used by ADC
	DIDR0 |= (1<<ADC3D)|(1<<ADC2D)|				// Disable digital pins being used by ADC
			(0<<ADC1D)|(0<<ADC0D);				// Leave enabled pins being used for digital
	
	// Setup I2C (TWI)
	usiTwiSlaveInit( (uint8_t)TWI_ADDRESS );
	sei();
	
	// Start ADC conversion
	ADCSRA = ADCSRA | (1<<ADSC);
	
    while(1)
    {
        // Read ADC
		adc_val = ADCH;
		ADCSRA = ADCSRA | (1<<ADSC);		// Reinable for next conversion to happen
		
		// Calculate RMS
		
		
		// Transmit Data
		if(usiTwiDataInTransmitBuffer() == false){
			// Transmit count for testing
			//usiTwiTransmitByte(count);
			count++;
		}
		if(usiTwiDataInTransmitBuffer() == false){
			// Transmit ADC value
			usiTwiTransmitByte((uint8_t)adc_val);
			count++;
		}
		
		// Toggle LED heartbeat
		if(adc_val < 64){
			if(led_counter++ == 0){
				LED_TOGGLE();
			}
		}						
 
    }
}