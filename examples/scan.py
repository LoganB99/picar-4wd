import picar_4wd as fc

import time

def main():
    while True:
        # fc.servo.set_angle(0)
        # time.sleep(0.5)
        # fc.servo.set_angle(90)
        # time.sleep(0.5)
        # fc.servo.set_angle(-90)
        # time.sleep(0.5)
        print(fc.get_distance_at(0))
        # print(fc.get_current_angle())
        # fc.hello()
        

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
        print('Program stopped')
