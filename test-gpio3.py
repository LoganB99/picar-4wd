import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# List of all BCM pins on Raspberry Pi 4
pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 
        19, 20, 21, 22, 23, 24, 25, 26, 27]

try:
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)  # Set as output
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)  # Small delay to ensure the change registers
        GPIO.output(pin, GPIO.LOW)
        
        print(f"Pin {pin}: working correctly")

except Exception as e:
    print(f"Error testing pin {pin}: {e}")

finally:
    GPIO.cleanup()  # Reset all pins to input mode

