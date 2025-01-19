import picar_4wd as fc
import time

# Global constants
SPEED = 10
TURN_SPEED = 50
SCAN_REF = 35
GRAYSCALE_REF = 400
FORWARD_SCAN_RANGE = slice(3,7)  # Indices for forward-facing sensors

def check_path_clear(scan_list):
    """Check if path ahead is clear of obstacles"""
    return all(x == 2 for x in scan_list[FORWARD_SCAN_RANGE])

def try_direction(turn_func, turn_time):
    """Try turning in specified direction and check if path is clear
    Args:
        turn_func: Function to execute turn (fc.turn_left or fc.turn_right)
        turn_time: How long to turn for in seconds
    Returns:
        bool: True if path is clear after turn, False otherwise
    """
    turn_func(TURN_SPEED)
    time.sleep(turn_time)
    fc.stop()
    scan_list = fc.scan_step(SCAN_REF)
    while not scan_list:
        scan_list = fc.scan_step(SCAN_REF)
    return check_path_clear(scan_list)

def turn_for_path(turn_func, max_turn_time=0.25):
    """Turn until path is clear or we've turned too long
    Args:
        turn_func: Turn direction to try (fc.turn_left or fc.turn_right)
        max_turn_time: Base time for turns
    Returns:
        float: Time spent turning in seconds, or -1 if no clear path found
    """
    start_time = time.time()
    while time.time() - start_time < max_turn_time:
        turn_func(SPEED)
        scan_list = fc.scan_step(SCAN_REF)
        if scan_list and check_path_clear(scan_list):
            return time.time() - start_time
    return -1

def main():
    while True:
        gs_list = fc.get_grayscale_list()
        if fc.get_line_status(GRAYSCALE_REF, gs_list) == 0:
            print("Line detected - you win")
            fc.turn_left(100)
            time.sleep(4)
            fc.stop()
            break

        scan_list = fc.scan_step(SCAN_REF)
        if not scan_list:
            continue

        if not check_path_clear(scan_list):
            fc.stop()
            fc.backward(SPEED)
            time.sleep(.25)
            fc.stop()

            # right_time = turn_for_path(fc.turn_right, 4)
            # if right_time != -1:
            #     time.sleep(right_time*.5)
            #     fc.stop()
            #     fc.turn_left(SPEED)
            #     time.sleep(right_time*.5)
            #     fc.stop()
            # try right
            check_right = try_direction(fc.turn_right, 0.9)
            if check_right:
                fc.forward(SPEED)
                time.sleep(1)
                fc.stop()
                try_direction(fc.turn_left, 0.9)
            else:
                fc.turn_left(TURN_SPEED)
                time.sleep(.9)
                fc.stop()
                # try left
                check_left = try_direction(fc.turn_left, 0.9)
                if check_left:
                    fc.forward(SPEED)
                    time.sleep(1)
                    fc.stop()
                    try_direction(fc.turn_right(.9)
                else: #both failed, turn around
                    fc.turn_left(TURN_SPEED)
                    time.sleep(.9)
                    fc.stop()
                    break
        else:
            fc.forward(SPEED)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        fc.stop()
        print("Motors stopped")
