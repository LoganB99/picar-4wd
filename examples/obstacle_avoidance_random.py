import picar_4wd as fc
import random
import time

speed = 10
turn_speed = 50
def main():
    while True:
        scan_list = False
        while not scan_list:
            scan_list = fc.scan_step(35)
        tmp = scan_list[3:7]
        if tmp != [2,2,2,2]:
            # Stop when obstacle detected
            fc.stop()
            fc.backward(speed)
            time.sleep(.25)
            
            # Pick random turn direction and duration
            turn_time = random.uniform(.5, 2.5)
            if random.random() < 0.5:
                print(f"Turning left for {turn_time:.1f} seconds")
                fc.turn_left(turn_speed)
            else:
                print(f"Turning right for {turn_time:.1f} seconds")
                fc.turn_right(turn_speed)
                
            # Turn for the chosen duration
            time.sleep(turn_time)
            fc.stop()
        else:
            fc.forward(speed)

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
