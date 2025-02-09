import logging
import cv2
from picamera2 import Picamera2, Preview
from libcamera import Transform
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
from picar_4wd import detect_utils
import time
import threading
import queue

logging.basicConfig(level=logging.INFO)

class Detect:
    def __init__(self, model: str = 'efficientdet_lite0.tflite', width: int = 640, height: int = 480, num_threads: int = 4, enable_edgetpu: bool = False, detection_queue: queue.Queue = None, enable_preview: bool = False):
        self.width = width
        self.height = height
        self.model = model if not enable_edgetpu else 'efficientdet_lite0_edgetpu.tflite'
        self.num_threads = num_threads
        self.enable_edgetpu = enable_edgetpu
        self.enable_preview = enable_preview
        self.detection_queue = detection_queue if detection_queue else queue.Queue()
        self.picam2 = self.initialize_camera()
        self.detector = self.initialize_model()
        self.thread = threading.Thread(target=self.run)
        self.thread_flag = True
        self.seeStopSign = False  # Initialize the seeStopSign boolean
        self.seePerson = False
        self.person_missing_frames = 0  # Counter for frames without seeing a person
        self.person_timeout = 2.0
        self.last_person = None

    def initialize_camera(self) -> Picamera2:
        picam2 = Picamera2()
        if self.enable_preview:
            preview_config = picam2.create_preview_configuration(main={"size": (self.width, self.height)}, transform=Transform(hflip=0, vflip=1))
            picam2.configure(preview_config)
        picam2.start()
        return picam2

    def initialize_model(self):
        base_options = core.BaseOptions(file_name=self.model, use_coral=self.enable_edgetpu, num_threads=self.num_threads)
        detection_options = processor.DetectionOptions(max_results=3, score_threshold=0.3)
        options = vision.ObjectDetectorOptions(base_options=base_options, detection_options=detection_options)
        return vision.ObjectDetector.create_from_options(options)

    def process_frame(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_tensor = vision.TensorImage.create_from_array(rgb_image)
        detection_result = self.detector.detect(input_tensor)
        
        # Check if a stop sign is detected
        self.seeStopSign = any(detection.categories[0].category_name == 'stop sign' for detection in detection_result.detections)
        
        # Check if a person is detected
        if any(detection.categories[0].category_name == 'person' for detection in detection_result.detections):
            self.seePerson = True
            self.last_person = time.time()
            self.person_missing_frames = 0  # Reset the counter if a person is seen
        else:
            if self.last_person and (time.time() - self.last_person) > self.person_timeout:
                self.seePerson = False  # Set to False only if missing for 2 seconds

        return detection_result

    def run(self) -> None:
        """Continuously run inference on images acquired from the camera."""
        try:
            counter, fps = 0, 0
            start_time = time.time()
            fps_avg_frame_count = 10

            while self.thread_flag:
                image = self.picam2.capture_array()
                counter += 1
                detection_result = self.process_frame(image)
                self.detection_queue.put(detection_result)

                if self.enable_preview:
                    image = detect_utils.visualize(image, detection_result)
                    cv2.imshow('object_detector', image)
                    if cv2.waitKey(1) == 27:
                        break

                if counter % fps_avg_frame_count == 0:
                    end_time = time.time()
                    fps = fps_avg_frame_count / (end_time - start_time)
                    start_time = time.time()

                time.sleep(1.0)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            self.picam2.stop()
            cv2.destroyAllWindows()

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread_flag = False
        self.thread.join()

if __name__ == "__main__":
    detection_queue = queue.Queue()
    detect = Detect(detection_queue=detection_queue, enable_preview = False,width=640, height=480, num_threads = 2, enable_edgetpu=False)
    detect.start()

    try:
        while True:
            if not detection_queue.empty():
                detection_result = detection_queue.get()
                
                # Access the seeStopSign boolean
                if detect.seeStopSign:
                    print("Stop sign detected!")
                if detect.seePerson:
                    print("Person detected!")

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        detect.stop()
