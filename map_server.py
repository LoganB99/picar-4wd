from flask import Flask, request, send_file, render_template_string
import math
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import json
import threading

app = Flask(__name__)

# Map dimensions in cm
MAP_WIDTH = 600  
MAP_HEIGHT = 600
CAR_START_X = MAP_WIDTH // 2  # Car starts at middle bottom
CAR_START_Y = 0

# Point connection parameters
MAX_POINT_DISTANCE = 10 # Maximum distance in cm to connect points

# Visualization parameters
PLOT_WIDTH = 10
PLOT_HEIGHT = 6
CAR_MARKER_SIZE = 10
GOAL_MARKER_SIZE = 10

# Initialize empty map and visualization
map_array = np.zeros((MAP_HEIGHT, MAP_WIDTH))
fig = plt.figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT))

# Add mutex lock for thread safety
map_lock = threading.Lock()

# Car position tracking
car_x = CAR_START_X
car_y = CAR_START_Y

goal_x = CAR_START_X
goal_y = CAR_START_Y

def init_visualization():
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

def update_visualization():
    # Acquire lock before updating visualization
    with map_lock:
        x_min = max(0, car_x - 100)
        x_max = min(MAP_WIDTH, car_x + 100)
        y_min = max(0, car_y - 100)
        y_max = min(MAP_HEIGHT, car_y + 100)
        print(f"x_min: {x_min}, x_max: {x_max}, y_min: {y_min}, y_max: {y_max}")
        local_map_array = map_array[y_min:y_max, x_min:x_max]
        plt.clf()
        plt.imshow(local_map_array, extent=[x_min, x_max, y_min, y_max], origin='lower', cmap='binary')
        plt.title('Environment Map')
        plt.xlabel('X Position (cm)')
        plt.ylabel('Y Position (cm)')
        
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.plot(car_x, car_y, 'r^', markersize=CAR_MARKER_SIZE, label='Car')
        plt.plot(goal_x, goal_y, 'g^', markersize=GOAL_MARKER_SIZE, label='Goal')
        plt.legend()
        
        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        return buf

@app.route('/set_goal', methods=['POST'])
def set_goal():
    global goal_x, goal_y
    data = request.json
    goal_x = data['goal_x']
    goal_y = data['goal_y']
    return {'status': 'success'}

@app.route('/update_car_position', methods=['POST'])
def update_car_position():
    global car_x, car_y
    data = request.json
    car_x = data['x']
    car_y = data['y']
    return {'status': 'success'}

@app.route('/update_map', methods=['POST'])
def update_map():
    global map_array
    
    # Get map data from request
    data = request.json
    
    # Acquire lock before modifying map_array
    with map_lock:
        # Update map array with received data
        map_array = np.array(data['map'])

    return {'status': 'success'}

@app.route('/get_map')
def get_map():
    buf = update_visualization()
    return send_file(buf, mimetype='image/png')

@app.route('/reset_map', methods=['POST'])
def reset_map():
    global map_array, car_x, car_y
    # Acquire lock before resetting map
    with map_lock:
        map_array = np.zeros((MAP_HEIGHT, MAP_WIDTH))
        car_x = CAR_START_X
        car_y = CAR_START_Y
    return {'status': 'success'}

@app.route('/')
def home():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Map View</title>
        <style>
            body {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background-color: #f0f0f0;
            }
            img {
                max-width: 90vw;
                max-height: 90vh;
                object-fit: contain;
                border: 2px solid #333;
                border-radius: 8px;
                background-color: white;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Live Environment Map</h1>
        <img id="mapImage" src="/get_map" alt="Environment Map">
        <script>
            setInterval(function() {
                const img = document.getElementById('mapImage');
                img.src = '/get_map?' + new Date().getTime();
            }, 1000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    init_visualization()
    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Keep main thread running
    while True:
        time.sleep(1)