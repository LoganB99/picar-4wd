import picar_4wd as fc

Track_line_speed = 10

def Track_line():
    gs_list = fc.get_grayscale_list()
    line_status = fc.get_line_status(1400,gs_list)
    print(f"Grayscale readings: {gs_list}")
    print(f"Line status: {line_status}")
    if line_status == 0:
        print("Line detected straight ahead - moving forward")
        fc.forward(Track_line_speed) 
    elif line_status == -1:
        print("Line detected on left - turning left")
        fc.turn_left(Track_line_speed)
    elif line_status == 1:
        print("Line detected on right - turning right") 
        fc.turn_right(Track_line_speed)
    else:
        print("Unexpected line status - stopping")
        fc.stop()

if __name__=='__main__':
    try:
        print("Starting line tracking program...")
        while True:
            Track_line()
    finally:
        fc.stop()
        print('Program stop')