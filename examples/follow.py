import picar_4wd as fc

speed = 30

def main():
    while True:
        print("\n--- Starting new scan ---")
        scan_list = fc.scan_step(23)
        if not scan_list:
            print("Scan not complete yet, continuing...")
            continue

        scan_list = [str(i) for i in scan_list]
        scan_list = "".join(scan_list)
        print(f"Current scan pattern: {scan_list}")
        
        paths = scan_list.split("2")
        length_list = []
        for path in paths:
            length_list.append(len(path))
        print(f"Path lengths: {length_list}")
        
        if max(length_list) == 0:
            print("No clear path found, stopping")
            fc.stop() 
        else:
            i = length_list.index(max(length_list))
            pos = scan_list.index(paths[i])
            pos += (len(paths[i]) - 1) / 2
            # pos = int(pos)
            delta = len(scan_list) / 3
            # delta *= us_step/abs(us_step)
            
            print(f"Target position: {pos:.1f}, Delta threshold: {delta:.1f}")
            
            if pos < delta:
                print("Target on left side, turning left")
                fc.turn_left(speed)
            elif pos > 2 * delta:
                print("Target on right side, turning right")
                fc.turn_right(speed)
            else:
                if scan_list[int(len(scan_list)/2-1)] == "0":
                    print("Obstacle directly ahead, moving backward")
                    fc.backward(speed)
                else:
                    print("Clear path ahead, moving forward")
                    fc.forward(speed)

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
