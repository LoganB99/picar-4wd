import picar_4wd as fc
import random
import time

speed = 20

def main():
    while True:
        scan_list = fc.scan_step(35)
        if not scan_list:
            continue

        tmp = scan_list[3:7]
        print(tmp)
        if tmp != [2,2,2,2]:
            # Stop when obstacle detected
            fc.stop()
            fc.backward(speed)
            time.sleep(.5)
            
            # Pick random turn direction and duration
            turn_time = random.uniform(.5, 2.5)
            if random.random() < 0.5:
                print(f"Turning left for {turn_time:.1f} seconds")
                fc.turn_left(speed)
            else:
                print(f"Turning right for {turn_time:.1f} seconds")
                fc.turn_right(speed)
                
            # Turn for the chosen duration
            time.sleep(turn_time)
        else:
            fc.forward(speed)

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
