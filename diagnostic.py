import RPi.GPIO as GPIO
import subprocess

# Check I2C bus using i2cdetect
def check_i2c():
    try:
        result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
        print("I2C devices found:\n", result.stdout)
    except Exception as e:
        print("I2C error:", e)

# Check GPIO pin states
def check_gpio(pins):
    GPIO.setmode(GPIO.BCM)
    for pin in pins:
        GPIO.setup(pin, GPIO.IN)
        state = GPIO.input(pin)
        print(f"Pin {pin} state: {state}")

if __name__ == "__main__":
    motor_pins = [23, 24, 19, 20]  # Corresponding GPIO numbers for D4, D5, D11, D15
    check_i2c()
    check_gpio(motor_pins)