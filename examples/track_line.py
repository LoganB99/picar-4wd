import picar_4wd as fc
import time

Track_line_speed = 30
no_line_count = 0
search_complete = False

def Track_line():
    global no_line_count, search_complete
    gs_list = fc.get_grayscale_list()
    print(f"Grayscale sensor values: {gs_list}")
    line_status = fc.get_line_status(400,gs_list)
    print(f"Line status: {line_status}")
    
    if line_status == 0:
        print("Line detected - moving forward")
        fc.forward(Track_line_speed)
        no_line_count = 0
    elif line_status == -1:
        print("Line on right - turning left")
        fc.turn_left(Track_line_speed)
        no_line_count = 0
    elif line_status == 1:
        print("Line on left - turning right")
        fc.turn_right(Track_line_speed)
        no_line_count = 0
    else:
        no_line_count += 1
        if no_line_count >= 5:
            print("No line detected for 5 cycles - searching for line")
            fc.stop()
            # Search for line by turning in place
            search_start_time = time.time()
            while time.time() - search_start_time < 4:  # 4 seconds for full rotation
                fc.turn_right(Track_line_speed)
                gs_list = fc.get_grayscale_list()
                if fc.get_line_status(400,gs_list) in [-1, 0, 1]:
                    print("Line found during search")
                    no_line_count = 0
                    return
            print("No line found after complete rotation")
            search_complete = True

if __name__=='__main__':
    try:
        print("Starting line tracking program...")
        while not search_complete:
            Track_line()
    finally:
        fc.stop()
        print('Program stop')