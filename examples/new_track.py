import picar_4wd as fc
import time

# Configuration constants
TRACK_LINE_SPEED = 20
TURN_SPEED = 20
LINE_THRESHOLD = 400
SEARCH_ROTATION_TIME = 5  # Full rotation time during line search
NO_LINE_MAX_COUNT = 5

no_line_count = 0
search_complete = False


def check_obstacles():
    """Scan for obstacles in the front area."""
    scan_list = fc.scan_step(30)  # Increased to 40cm for earlier detection
    if not scan_list:
        return False
    # Check wider front area (4:6 instead of 3:7)
    front_scan = scan_list[4:6]
    return front_scan != [2, 2]


def turn_around():
    """Perform a 180-degree turn."""
    print("Turning around...")
    initial_speed = fc.speed_val()
    target_rotation = 180  # degrees
    wheel_base = 15  # cm - distance between wheels
    
    # Calculate required rotation time based on angular velocity
    # Angular velocity (deg/s) = (wheel speed * 360) / (2 * pi * wheel_base)
    angular_velocity = (TURN_SPEED * 360) / (2 * 3.14159 * wheel_base)
    rotation_time = target_rotation / angular_velocity
    
    turn_start = time.time()
    while time.time() - turn_start < rotation_time:
        fc.turn_right(TURN_SPEED)
    fc.stop()


def search_line():
    """Search for the line by rotating the robot."""
    print("No line detected. Searching...")
    search_start_time = time.time()
    while time.time() - search_start_time < SEARCH_ROTATION_TIME:
        fc.turn_right(TURN_SPEED)
        gs_list = fc.get_grayscale_list()
        if fc.get_line_status(LINE_THRESHOLD, gs_list) in [-1, 0, 1]:
            print("Line found during search")
            return True
    print("No line found after complete rotation")
    return False


def track_line():
    """Track the line based on grayscale sensor readings."""
    global no_line_count, search_complete

    gs_list = fc.get_grayscale_list()
    print(f"Grayscale sensor values: {gs_list}")
    line_status = fc.get_line_status(LINE_THRESHOLD, gs_list)
    print(f"Line status: {line_status}")

    # # Check for obstacles first
    # if check_obstacles():
    #     print("Obstacle detected - turning around")
    #     fc.stop()
    #     turn_around()
    #     return

    # 
    if line_status == 0:
        print("Line detected - moving forward")
        fc.forward(TRACK_LINE_SPEED)
        no_line_count = 0
    elif line_status == -1:
        print("Line on right - turning left")
        fc.turn_left(TRACK_LINE_SPEED)
        no_line_count = 0
    elif line_status == 1:
        print("Line on left - turning right")
        fc.turn_right(TRACK_LINE_SPEED)
        no_line_count = 0
    else:
        no_line_count += 1
        if no_line_count >= 5:
            print("No line detected for 5 cycles - searching for line")
            fc.stop()
            # Search for line by turning in place
            search_start_time = time.time()
            while time.time() - search_start_time < 4:  # 4 seconds for full rotation
                fc.turn_right(TRACK_LINE_SPEED)
                gs_list = fc.get_grayscale_list()
                if fc.get_line_status(400,gs_list) in [-1, 0, 1]:
                    print("Line found during search")
                    no_line_count = 0
                    return
            print("No line found after complete rotation")
            search_complete = True


if __name__ == '__main__':
    try:
        print("Starting line tracking program...")
        while not search_complete:
            track_line()
    finally:
        fc.stop()
        print('Program stopped')
