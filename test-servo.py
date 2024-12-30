from picar_4wd.servo import Servo
from picar_4wd.pwm import PWM

# Initialize the PWM object with the appropriate pin
pwm = PWM("P0")  # Replace "P0" with the correct pin if needed

# Pass the PWM object to the Servo constructor
servo = Servo(pwm)

# Move servo to 90 degrees (center)
servo.set_angle(90)

# Move back to 0 degrees
servo.set_angle(0)