from machine import Pin, ADC
import time


# Create an ADC object linked to pin 36
adc = ADC(Pin(36, mode=Pin.IN))

while True:

    # Read ADC and convert to voltage
    val = adc.read()
    val = val * (3.3 / 4095)
    print(round(val, 2), "V") # Keep only 2 digits

    # Wait a bit before taking another reading
    time.sleep_ms(100)