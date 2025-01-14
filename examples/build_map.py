import math
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from IPython import display

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

# Point connection parameters
MAX_POINT_DISTANCE = 3  # Maximum distance in cm to connect points

# Visualization parameters
PLOT_WIDTH = 10
PLOT_HEIGHT = 6
CAR_MARKER_SIZE = 10

def get_xy_coords(angle, distance):
    # Convert angle from degrees to radians for math functions
    angle_rad = math.radians(angle)
    # Get x,y relative to car position
    x = distance * math.sin(angle_rad)
    y = distance * math.cos(angle_rad)
    # Convert to map coordinates (car at CAR_START_X,CAR_START_Y)
    map_x = int(CAR_START_X + x)
    # Y coordinate starts from bottom now
    map_y = int(y)
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

def visualize_map(map_array):
    plt.clf()  # Clear the current figure
    plt.imshow(map_array, origin='lower', cmap='binary')  # Set origin='lower' to flip y-axis
    plt.title('Environment Map')
    plt.xlabel('X Position (cm)')
    plt.ylabel('Y Position (cm)')
    
    # Add grid lines
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add major axis lines
    plt.axhline(y=CAR_START_Y, color='r', linestyle='-', alpha=0.5)
    plt.axvline(x=CAR_START_X, color='r', linestyle='-', alpha=0.5)
    
    # Mark car position at bottom
    plt.plot(CAR_START_X, CAR_START_Y, 'r^', markersize=CAR_MARKER_SIZE, label='Car')
    plt.legend()
    plt.savefig('map.png')  # Save to file instead of displaying
    plt.close()  # Close the figure to free memory

def main():
    # Initialize empty map
    map_array = np.zeros((MAP_HEIGHT, MAP_WIDTH))
    
    # Set up the plot
    plt.figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT))
    
    while True:
        points = []  # Store (x,y) coordinates of detected points
        
        # Scan left to right and collect points
        for angle in ANGLES_TO_SCAN:
            distance = fc.get_distance_at(angle)
            if distance > 0:  # Only record valid measurements
                x, y = get_xy_coords(angle, distance)
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    points.append((x, y))
                    map_array[y, x] = 1
        
        # Scan right to left
        for angle in reversed(ANGLES_TO_SCAN[:-1]): # Skip last angle since we just scanned it
            distance = fc.get_distance_at(angle)
            if distance > 0:  # Only record valid measurements
                x, y = get_xy_coords(angle, distance)
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    points.append((x, y))
                    map_array[y, x] = 1
        
        # Connect nearby points
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                x1, y1 = points[i]
                x2, y2 = points[j]
                
                # Calculate distance between points
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if dist <= MAX_POINT_DISTANCE:  # Points within threshold
                    # Calculate slope for visualization
                    if x2 - x1 != 0:
                        slope = (y2 - y1) / (x2 - x1)
                        print(f"Connecting points with slope: {slope:.2f}")
                    
                    # Connect the points with a line
                    connect_points(map_array, x1, y1, x2, y2)
        
        # Update visualization
        visualize_map(map_array)

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
        plt.close('all')
        print('Program stopped')
