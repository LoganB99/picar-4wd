import math
import numpy as np
import time
import requests
import json
import picar_4wd as fc
import queue
import random
import sys

# Map dimensions in cm
MAP_WIDTH = 600  
MAP_HEIGHT = 600
CAR_START_X = MAP_WIDTH // 2  # Car starts at middle bottom
CAR_START_Y = 0

# Scanning parameters
SCAN_START_ANGLE = -90
SCAN_END_ANGLE = 90
SCAN_ANGLE_STEP = 10
ANGLES_TO_SCAN = list(range(SCAN_START_ANGLE, SCAN_END_ANGLE, SCAN_ANGLE_STEP))

SPEED = 10  # Set car speed to 10
TURN_SPEED = 50  # Set turn speed to 50
SCAN_REF = 35
GRAYSCALE_REF = 400
FORWARD_SCAN_RANGE = slice(3,7)  # Indices for forward-facing sensors
TURN_SLEEP = .88

SERVER_URL = "http://192.168.1.108:5000"

# Car position tracking
car_x = CAR_START_X
car_y = CAR_START_Y
last_update_time = time.time()
direction = 'N'

detect = None

# Map array for local calculations
map_array = np.zeros((MAP_HEIGHT, MAP_WIDTH))

def turn_and_move(angle, duration):
    global direction, last_update_time
    print(f"Turning {angle} degrees and moving")
    if angle > 0:
        fc.turn_right(TURN_SPEED)
    else:
        fc.turn_left(TURN_SPEED)
    time.sleep(TURN_SLEEP)
    fc.stop()
    
    # Update direction
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    current_index = directions.index(direction)
    new_index = (current_index + angle // 45) % 8
    direction = directions[new_index]
    
    start_time = time.time()
    # Move forward
    fc.forward(SPEED)
    time.sleep(duration)
    
    # Update car position while moving
    update_car_position(moving=True, start_time=start_time)
    
    fc.stop()

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
        fc.turn_right(TURN_SPEED)
        time.sleep(0.1)
        fc.stop()
        return True
    return False

def update_car_position(moving=False, start_time=None):
    global car_x, car_y
    current_time = time.time()
    elapsed_time = current_time - start_time
    
    # Get current speed in mm/s and convert to cm/s
    speed = fc.speed_val() / 10 if moving else 0
    
    # Calculate distance traveled in cm
    distance = speed * elapsed_time
    
    # Update position based on direction
    if direction == 'N':
        car_y += distance
    elif direction == 'NE':
        car_x += distance / math.sqrt(2)
        car_y += distance / math.sqrt(2)
    elif direction == 'E':
        car_x += distance
    elif direction == 'SE':
        car_x += distance / math.sqrt(2)
        car_y -= distance / math.sqrt(2)
    elif direction == 'S':
        car_y -= distance
    elif direction == 'SW':
        car_x -= distance / math.sqrt(2)
        car_y -= distance / math.sqrt(2)
    elif direction == 'W':
        car_x -= distance
    elif direction == 'NW':
        car_x -= distance / math.sqrt(2)
        car_y += distance / math.sqrt(2)
    
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

def get_xy_coords(angle, distance):
    # Convert angle from degrees to radians for math functions
    angle_rad = math.radians(angle)
    # Get x,y relative to car position
    x = distance * math.sin(angle_rad)
    y = distance * math.cos(angle_rad)
    # Convert to map coordinates (car at current position)
    map_x = int(car_x + x)
    # Y coordinate starts from bottom now
    map_y = int(car_y + y)
    return (map_x, map_y)

def connect_points(map_array, x1, y1, x2, y2):
    # Get slope between points
    if x2 - x1 == 0:  # Vertical line
        slope = float('inf')
    else:
        slope = (y2 - y1) / (x2 - x1)
    
    # Draw line between points using Bresenham's algorithm
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    
    if dx > dy:
        err = dx / 2.0
        while x != x2:
            map_array[int(y), int(x)] = 1
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y2:
            map_array[int(y), int(x)] = 1
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    map_array[int(y2), int(x2)] = 1

def a_star_search(map_array, start, goal):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    # maintain an open set of nodes to explore. lowest f-score is explored first
    open_set = queue.PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    # g-score is the cost from 
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while not open_set.empty():
        current = open_set.get()[1]
        if current == goal:
            # reconstruct path
            # initially empty path
            path = []
            # while the goal node is in the came_from dictionary
            while current in came_from:
                # add the current node to the path
                path.append(current)
                # set the current node to the node that came before it
                current = came_from[current]
            # no more current nodes, add the start node
            path.append(start)
            # reverse the path to get the correct order
            path.reverse()
            # return the path
            return path
        
        # Get neighbors (Manhattan distance)
        neighbors = [
            (current[0] + dx, current[1] + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        ]

        for neighbor in neighbors:
            tentative_g_score = g_score[current] + 1
            if 0 <= neighbor[0] < len(map_array) and 0 <= neighbor[1] < len(map_array[0]):
                if map_array[neighbor[1]][neighbor[0]] == 1:
                    continue
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    # lowest f-score is highest priority
                    open_set.put((f_score[neighbor], neighbor))
    print("No path found")
    return None

def scan_data_to_map():
    global car_x, car_y, last_update_time, map_array
    
    print("\n--- Starting new environment scan ---")
    
    # Clear the map
    map_array = np.zeros((MAP_HEIGHT, MAP_WIDTH))
    points = []  # Store processed points for connecting
        
    # Scan left to right and collect points
    print("Scanning left to right...")
    for angle in ANGLES_TO_SCAN:
        distance = fc.get_distance_at(angle)
        if distance > 0:  # Only record valid measurements
            # Clear points along the ray until obstacle
            for d in range(int(distance)):
                x, y = get_xy_coords(angle, d)
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    map_array[y, x] = 0
                    
            # Mark the obstacle point
            x, y = get_xy_coords(angle, distance)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                points.append((x, y))
                map_array[y, x] = 1

    # Scan right to left
    print("Scanning right to left...")
    for angle in reversed(ANGLES_TO_SCAN[:-1]):
        distance = fc.get_distance_at(angle)
        if distance > 0:
            # Process point same as above
            for d in range(int(distance)):
                x, y = get_xy_coords(angle, d)
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    map_array[y, x] = 0
                    
            x, y = get_xy_coords(angle, distance)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                points.append((x, y))
                map_array[y, x] = 1

    # Connect nearby points
    MAX_POINT_DISTANCE = 10  # Maximum distance in cm to connect points
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            x1, y1 = points[i]
            x2, y2 = points[j]
            
            # Calculate distance between points
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            if dist <= MAX_POINT_DISTANCE:
                connect_points(map_array, x1, y1, x2, y2)
    
    # Send processed map data to server
    try:
        response = requests.post(
            f"{SERVER_URL}/update_map",
            json={'map': map_array.tolist()},  # Convert numpy array to list for JSON
            timeout=5
        )
        if response.status_code != 200:
            print(f"Error sending data: {response.status_code}")
        else:
            print("Successfully sent map data to server")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to server: {e}")
        time.sleep(1)

def main():
    global detect, car_x, car_y
    fc.start_speed_thread()
    detection_queue = queue.Queue()
    detect = fc.Detect(detection_queue=detection_queue, enable_edgetpu=False, num_threads = 4)
    detect.start()
    print("Starting autonomous navigation...")
    
    
    # Get goal from arguments
    if len(sys.argv) != 3:
        print("Usage: python build_map_remote.py <forward_distance> <left_or_right_distance>")
        sys.exit(1)
    
    forward_distance = int(sys.argv[1])
    left_or_right_distance = int(sys.argv[2])
    
    goal_x = car_x + forward_distance
    goal_y = car_y + left_or_right_distance

    print(f"Goal: {goal_x}, {goal_y}")

    scan_data_to_map()

    path = a_star_search(map_array, (car_x, car_y), (goal_x, goal_y))
    print(path)
    
    # Send goal to server
    try:
        response = requests.post(
            f"{SERVER_URL}/set_goal",
            json={'goal_x': goal_x, 'goal_y': goal_y},
            timeout=5
        )
        if response.status_code != 200:
            print(f"Error sending goal: {response.status_code}")
        else:
            print("Successfully sent goal to server")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to server: {e}")
    
    
    steps_before_rescan = 10
    while True:
        break
        # Check if an obstacle is detected
        # if not detection_queue.empty():
        #     detection_result = detection_queue.get()
        #     for detection in detection_result.detections:
        #         if detection.categories[0].category_name == 'person':
        #             print("Person detected")
        #             fc.stop()
        #         elif detection.categories[0].category_name == 'stop sign':
        #             print("Stop sign detected")

        # Check if car is within 5 cm of the goal
        # if abs(car_x - goal_x) <= 5 and abs(car_y - goal_y) <= 5:
        #     print("Goal reached!")
        #     break

        # Check if we need to rescan
        # if steps_before_rescan == 0:
        #     scan_data_to_map()
        #     steps_before_rescan = 10
        # steps_before_rescan -= 1


        
            
        
        
        # fc.stop()
        # scan_data_to_map()

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
