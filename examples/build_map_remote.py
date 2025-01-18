import math
import numpy as np
import time
import requests
import json
import picar_4wd as fc
import queue
import random

# Map dimensions in cm
MAP_WIDTH = 200  
MAP_HEIGHT = 100
CAR_START_X = MAP_WIDTH // 2  # Car starts at middle bottom
CAR_START_Y = 0

# Scanning parameters
SCAN_START_ANGLE = -89
SCAN_END_ANGLE = 89
SCAN_ANGLE_STEP = 10
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
direction = 'N'  # N, E, S, W

detect = None

# todo: is south really south, once map updates, make sure we are going right direction

def turn_left_90_deg():
    global direction
    print("Turning left 90 degrees")
    fc.turn_left(SPEED)
    time.sleep(1)  # Adjust the time based on power_val to achieve a 90-degree turn
    fc.stop()
    direction = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}[direction]

def turn_right_90_deg():
    global direction
    print("Turning right 90 degrees")
    fc.turn_right(SPEED)
    time.sleep(1)  # Adjust the time based on power_val to achieve a 90-degree turn
    fc.stop()
    direction = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}[direction]

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

def update_car_position():
    global car_x, car_y, last_update_time
    current_time = time.time()
    elapsed_time = current_time - last_update_time
    
    # Get current speed in mm/s and convert to cm/s
    speed = fc.speed_val() / 10
    
    # Calculate distance traveled in cm
    distance = speed * elapsed_time
    
    # Update position based on direction
    if direction == 'N':
        car_y += distance
    elif direction == 'E':
        car_x += distance
    elif direction == 'S':
        car_y -= distance
    elif direction == 'W':
        car_x -= distance
    
    last_update_time = current_time
    
    print(f"Updated position - X: {car_x:.1f}, Y: {car_y:.1f}, Speed: {speed:.1f} cm/s, Direction: {direction}")
    
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
    global detect
    fc.start_speed_thread()
    detection_queue = queue.Queue()
    detect = fc.Detect(detection_queue=detection_queue, enable_edgetpu=False, num_threads = 4)
    detect.start()
    print("Starting autonomous navigation...")
    scan_data_to_map()
    print("hello")
    while True:
        print(detection_queue.get())

        print("\n--- Starting new navigation cycle ---")
        time.sleep(5)

        update_car_position()
            # if not check_path_clear(scan_list):
            #     print("\nPath blocked - executing avoidance maneuver")
            #     fc.stop()
                
            #     if try_random_unstuck():
            #         continue
                    
            #     print("Moving backward briefly")
            #     fc.backward(SPEED)
            #     time.sleep(.25)
            #     fc.stop()
                
            #     turn_right_90_deg()
            #     scan_list = get_complete_scan()
            #     if not check_path_clear(scan_list):
            #         turn_left_90_deg()
            #         turn_left_90_deg()
            #         scan_list = get_complete_scan()
            #         if not check_path_clear(scan_list):
            #             turn_right_90_deg()
            #             print("Failed to find clear path - restarting navigation cycle")
            #             break
            #         else:
            #             print("Path clear after turning left twice - moving forward")
            #             fc.forward(SPEED)
            #     else:
            #         print("Path clear after turning right - moving forward")
            #         fc.forward(SPEED)
            # else:
            #     print("Path clear - moving forward")
            #     fc.forward(SPEED)
            # time.sleep(0.1)  # Small delay between position updates
        
        fc.stop()
        scan_data_to_map()

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
        if detect:
            detect.stop()
        fc.left_rear_speed.deinit()
        fc.right_rear_speed.deinit()
        print('Program stopped')
