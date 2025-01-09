import picar_4wd as fc
import time
def drive_in_circle(power, multiplier):
    """
    Drives the robot in a circle by setting a different power on the left vs. right side.

    power      : Base power level.
    multiplier : Ratio for the left side power (relative to 'power').
                 The smaller this multiplier, the tighter the turn.
                 The closer it is to 1.0, the wider the turn.
    """
    left_power = multiplier * power
    right_power = power

    fc.set_motor_power(1, left_power)   # Left front
    fc.set_motor_power(3, left_power)   # Left rear
    fc.set_motor_power(2, right_power)  # Right front
    fc.set_motor_power(4, right_power)  # Right rear


if __name__ == '__main__':
    # fc.start_speed_thread()
    try:
        while True:
            # drive_in_circle(50, 0)
            drive_in_circle(power=70, multiplier=.3)
    finally:
        fc.stop()