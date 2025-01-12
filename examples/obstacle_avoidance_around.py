import picar_4wd as fc
import random
import time
import math

speed = 20

def check_path_clear(scan_list):
    """Check if path ahead is clear of obstacles"""
    return all(x == 2 for x in scan_list[3:7])

def try_direction(turn_func, turn_time):
    """Try turning in specified direction and check if path is clear
    Args:
        turn_func: Function to execute turn (fc.turn_left or fc.turn_right)
        turn_time: How long to turn for in seconds
    Returns:
        bool: True if path is clear after turn, False otherwise
    """
    turn_func(speed)
    time.sleep(turn_time)
    fc.stop()
    scan_list = fc.scan_step(35)
    return check_path_clear(scan_list) if scan_list else False

def turn_for_path(turn_func, max_turn_time=0.25):
    """Turn until path is clear or we've turned too long
    Args:
        turn_func: Turn direction to try (fc.turn_left or fc.turn_right)
        max_turn_time: Base time for turns
    Returns:
        float: Time spent turning in seconds, or -1 if no clear path found
    """
    # Keep turning until path is clear or we've turned too long
    start_time = time.time()
    max_total_turn = max_turn_time  # Maximum seconds to keep trying turns
    while time.time() - start_time < max_total_turn:
        turn_func(speed)
        # time.sleep(0.1)  # Turn in small increments
        # fc.stop()
        
        scan_list = fc.scan_step(35)
        if scan_list and check_path_clear(scan_list):
            # print("Path clear")
            return time.time() - start_time
            
    # print("Could not find clear path")
    return -1

    # # Go forward past obstacle
    # fc.forward(speed)
    # time.sleep(0.5)
    
    # # Turn back toward original path (twice as long)
    # opposite_turn_func(speed)
    # time.sleep(turn_time * 2)
    
    # # Go forward
    # fc.forward(speed)
    # time.sleep(0.5)
    
    # # Final turn to align with original direction
    # initial_turn_func(speed)
    # time.sleep(turn_time)
    
    # # Check if path is clear
    # fc.stop()
    # scan_list = fc.scan_step(35)
    # return check_path_clear(scan_list) if scan_list else False

def main():
    while True:
        #get grayscale sensor values
        gs_list = fc.get_grayscale_list()
        print(gs_list)
        if fc.get_line_status(400, gs_list) == 0:
            print("Line detected - you win")
            fc.turn_left(100)
            time.sleep(4)
            fc.stop()
            break
        # Get distance readings
        scan_list = fc.scan_step(35)
        # print(scan_list)
        if not scan_list:
            continue

        tmp = scan_list[3:7]
        # print(tmp)
        
        # # If obstacle detected
        if not check_path_clear(scan_list):
            # print("Obstacle detected")
        #     # Back up slightly
            fc.stop()
            fc.backward(speed)
            time.sleep(.25)
            fc.stop()
            right_time = -1
            left_time = -1
        #     # Try going around right first
            right_time = turn_for_path(fc.turn_right, 4)
            if right_time != -1:
                # Scale forward time between 0.25 and 1 second based on turn time
                # Assuming max turn time is around 4 seconds
                continue
            else:
                # print("Failed to go around right")
                break
            # elif turn_for_path(fc.turn_left, 8):
            #     print("Successfully went around left")
            #     break
            # else:
            #     print("Failed to go around")
            #     break
                # fc.forward(speed)
        #     # Then try left
        #     elif try_go_around(fc.turn_left, fc.turn_right):
        #         fc.forward(speed)
        #     # If both fail, back up more
        #     else:
        #         try_direction(fc.turn_right, 0.25)
        #         fc.backward(speed)
        #         time.sleep(.5)
        #         fc.stop()
        else:
            # print("Path clear")
            fc.forward(speed)
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        fc.stop()
        print("Motors stopped")
