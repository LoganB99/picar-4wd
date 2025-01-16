import picar_4wd as fc
import sys
import tty
import termios
import asyncio
import time

power_val = 100
key = 'status'
print("If you want to quit.Please press q")
def readchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)

def turn_left_90_deg():
    print("Turning left 90 degrees")
    fc.turn_left(power_val)
    if power_val != 0:
        time_asleep = -0.015 * power_val + 2
        time.sleep(time_asleep)  # Adjust the time based on power_val to achieve a 90-degree turn
    fc.stop()

def turn_right_90_deg():
    print("Turning right 90 degrees")
    fc.turn_right(power_val)
    if power_val != 0:
        time_asleep = -0.015 * power_val + 2
        time.sleep(time_asleep)  # Adjust the time based on power_val to achieve a 90-degree turn
    fc.stop()


def Keyborad_control():
    while True:
        global power_val
        key=readkey()
        if key=='6':
            if power_val <=90:
                power_val += 10
                print("power_val:",power_val)
        elif key=='4':
            if power_val >=10:
                power_val -= 10
                print("power_val:",power_val)
        if key=='w':
            fc.forward(power_val)
        elif key=='a':
            fc.turn_left(power_val)
        elif key=='s':
            fc.backward(power_val)
        elif key=='d':
            fc.turn_right(power_val)
        elif key=='l':
            turn_left_90_deg()
        elif key=='r':
            turn_right_90_deg()
        else:
            fc.stop()
        if key=='q':
            print("quit")  
            break  
if __name__ == '__main__':
    Keyborad_control()
