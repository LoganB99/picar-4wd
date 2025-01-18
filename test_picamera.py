from picamera2 import Picamera2
import time

def main():
    # Initialize Picamera2
    picam2 = Picamera2()

    # Configure camera
    preview_config = picam2.create_preview_configuration()
    picam2.configure(preview_config)

    # Start camera preview
    picam2.start()

    print("Camera is running. Press Ctrl+C to exit.")
    time.sleep(5)  # Keep the preview active for 5 seconds

    # Capture an image
    output_path = "test_image.jpg"
    picam2.capture_file(output_path)
    print(f"Image captured and saved to {output_path}")

    # Stop the camera
    picam2.stop()

if __name__ == "__main__":
    main()

