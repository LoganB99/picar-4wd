import picar_4wd as fc
import sys
import tty
import termios
import asyncio
import time

forward_speed = 10
turn_speed = 50
turn_time = .9
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
    fc.turn_left(turn_speed)
    time.sleep(turn_time)
    fc.stop()

def turn_right_90_deg():
    print("Turning right 90 degrees")
    fc.turn_right(turn_speed)
    time.sleep(turn_time)
    fc.stop()

def Keyborad_control():
    while True:
        key = readkey()
        if key == 'w':
            fc.forward(forward_speed)
        elif key == 'a':
            fc.turn_left(turn_speed)
        elif key == 's':
            fc.backward(forward_speed)
        elif key == 'd':
            fc.turn_right(turn_speed)
        elif key == 'l':
            turn_left_90_deg()
        elif key == 'r':
            turn_right_90_deg()
        elif key == 't':
            print("Moving forward for half a second")
            fc.forward(forward_speed)
            time.sleep(0.5)
            fc.stop()
        else:
            fc.stop()
        if key == 'q':
            print("quit")  
            break  
#bla
if __name__ == '__main__':
    Keyborad_control()
