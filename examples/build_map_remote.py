import math
import numpy as np
import time
import requests
import json
import picar_4wd as fc

# Map dimensions in cm
MAP_WIDTH = 200  
MAP_HEIGHT = 100
CAR_START_X = MAP_WIDTH // 2  # Car starts at middle bottom
CAR_START_Y = 0

# Scanning parameters
SCAN_START_ANGLE = -90
SCAN_END_ANGLE = 91
SCAN_ANGLE_STEP = 10
ANGLES_TO_SCAN = list(range(SCAN_START_ANGLE, SCAN_END_ANGLE, SCAN_ANGLE_STEP))

# Server settings
SERVER_URL = "http://192.168.1.108:5000"

def main():
    while True:
        scan_data = []  # Store scan measurements
        
        # Scan left to right and collect points
        for angle in ANGLES_TO_SCAN:
            distance = fc.get_distance_at(angle)
            if distance > 0:  # Only record valid measurements
                scan_data.append({
                    'angle': angle,
                    'distance': distance
                })
        
        # Scan right to left
        for angle in reversed(ANGLES_TO_SCAN[:-1]): # Skip last angle since we just scanned it
            distance = fc.get_distance_at(angle)
            if distance > 0:  # Only record valid measurements
                scan_data.append({
                    'angle': angle,
                    'distance': distance
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
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to server: {e}")
            time.sleep(1)  # Wait before retrying

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
        print('Program stopped')
