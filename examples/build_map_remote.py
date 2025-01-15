import math
import numpy as np
import time
import requests
import json
import picar_4wd as fc
import random

# Map dimensions in cm
MAP_WIDTH = 200  
MAP_HEIGHT = 100
CAR_START_X = MAP_WIDTH // 2  # Car starts at middle bottom
CAR_START_Y = 0

# Scanning parameters
SCAN_START_ANGLE = -89
SCAN_END_ANGLE = 89
SCAN_ANGLE_STEP = 8
ANGLES_TO_SCAN = list(range(SCAN_START_ANGLE, SCAN_END_ANGLE, SCAN_ANGLE_STEP))

SPEED = 50
SCAN_REF = 35
GRAYSCALE_REF = 400
FORWARD_SCAN_RANGE = slice(3,7)  # Indices for forward-facing sensors

# Server settings
SERVER_URL = "http://192.168.1.108:5000"

# Car position tracking
car_x = CAR_START_X
car_y = CAR_START_Y
last_update_time = time.time()

def get_complete_scan():
    """Helper function to get a complete scan"""
    scan_list = False
    while not scan_list:
        scan_list = fc.scan_step(SCAN_REF)
    return scan_list

def check_path_clear(scan_list):
    """Check if path ahead is clear of obstacles"""
    is_clear = all(x == 2 for x in scan_list[FORWARD_SCAN_RANGE])
    print(f"Checking forward path: {'Clear' if is_clear else 'Blocked'}")
    print(f"Forward scan values: {scan_list[FORWARD_SCAN_RANGE]}")
    return is_clear

def try_random_unstuck():
    """Randomly try to unstuck with 20% chance"""
    if random.random() < 0.2:
        print("\nTrying random unstuck maneuver")
        fc.turn_right(SPEED)
        time.sleep(0.1)
        fc.stop()
        return True
    return False

def turn_for_path(turn_func, max_turn_time=0.25):
    """Turn until path is clear or we've turned too long
    Args:
        turn_func: Turn direction to try (fc.turn_left or fc.turn_right)
        max_turn_time: Base time for turns
    Returns:
        float: Time spent turning in seconds, or -1 if no clear path found
    """
    direction = "right" if turn_func == fc.turn_right else "left"
    print(f"\nAttempting to turn {direction} for up to {max_turn_time} seconds")
    start_time = time.time()
    while time.time() - start_time < max_turn_time:
        turn_func(SPEED)
        scan_list = get_complete_scan()
        if check_path_clear(scan_list):
            turn_time = time.time() - start_time
            print(f"Found clear path after turning {direction} for {turn_time:.2f} seconds")
            return turn_time
    fc.stop()
    print(f"No clear path found after turning {direction}")
    scan_data_to_map()
    return -1

def update_car_position():
    global car_x, car_y, last_update_time
    current_time = time.time()
    elapsed_time = current_time - last_update_time
    
    # Get current speed in mm/s and convert to cm/s
    speed = fc.speed_val() / 10
    
    # Calculate distance traveled in cm
    distance = speed * elapsed_time
    
    # Update Y position (assuming forward motion)
    car_y += distance
    
    last_update_time = current_time
    
    print(f"Updated position - X: {car_x:.1f}, Y: {car_y:.1f}, Speed: {speed:.1f} cm/s")
    
    # Send position update to server
    try:
        response = requests.post(
            f"{SERVER_URL}/update_car_position",
            json={'x': car_x, 'y': car_y},
            timeout=5
        )
    except requests.exceptions.RequestException:
        print("Failed to send position update to server")
        pass

def scan_data_to_map():
    global car_x, car_y, last_update_time
    
    print("\n--- Starting new environment scan ---")
    
    # Reset car position when scanning
    car_x = CAR_START_X
    car_y = CAR_START_Y
    last_update_time = time.time()
    
    scan_data = []  # Store scan measurements
        
    # Scan left to right and collect points
    print("Scanning left to right...")
    for angle in ANGLES_TO_SCAN:
        distance = fc.get_distance_at(angle)
        if distance > 0:  # Only record valid measurements
            # print(f"Angle: {angle}°, Distance: {distance}cm")
            scan_data.append({
                'angle': angle,
                'distance': distance,
            })
    #reset but do not scan
    # fc.get_distance_at(ANGLES_TO_SCAN[0])
    # Scan right to left
    print("Scanning right to left...")
    for angle in reversed(ANGLES_TO_SCAN[:-1]): # Skip last angle since we just scanned it
        distance = fc.get_distance_at(angle)
        if distance > 0:  # Only record valid measurements
            # print(f"Angle: {angle}°, Distance: {distance}cm")
            scan_data.append({
                'angle': angle,
                'distance': distance,
            })

    # Send scan data to server
    try:
        response = requests.post(
            f"{SERVER_URL}/update_map",
            json=scan_data,
            timeout=5
        )
        if response.status_code != 200:
            print(f"Error sending data: {response.status_code}")
        else:
            print("Successfully sent scan data to server")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to server: {e}")
        time.sleep(1)  # Wait before retrying

def main():
    fc.start_speed_thread()
    print("Starting autonomous navigation...")
    scan_data_to_map()
    while True:
        # gs_list = fc.get_grayscale_list()
        # if fc.get_line_status(GRAYSCALE_REF, gs_list) == 0:
        #     print("\nLINE DETECTED - VICTORY LAP!")
        #     fc.turn_left(100)
        #     time.sleep(4)
        #     fc.stop()
        #     break

        print("\n--- Starting new navigation cycle ---")
        start_time = time.time()
        while time.time() - start_time < 5:
            update_car_position()
            scan_list = get_complete_scan()
            print(f"Scan list: {scan_list}")
            if not check_path_clear(scan_list):
                print("\nPath blocked - executing avoidance maneuver")
                fc.stop()
                
                if try_random_unstuck():
                    continue
                    
                print("Moving backward briefly")
                fc.backward(SPEED)
                time.sleep(.25)
                fc.stop()
                
                right_time = turn_for_path(fc.turn_right, 4)
                if right_time != -1:
                    print("\nExecuting S-curve maneuver")
                    print("Moving forward")
                    fc.forward(SPEED)
                    time.sleep(right_time*.5)
                    fc.stop()
                    print("Correcting course left")
                    fc.turn_left(SPEED)
                    time.sleep(right_time*.5)
                    fc.stop()
                else:
                    print("Failed to find clear path - restarting navigation cycle")
                    break
            else:
                print("Path clear - moving forward")
                fc.forward(SPEED)
            time.sleep(0.1)  # Small delay between position updates
        
        fc.stop()
        scan_data_to_map()

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
        fc.left_rear_speed.deinit()
        fc.right_rear_speed.deinit()
        print('Program stopped')
