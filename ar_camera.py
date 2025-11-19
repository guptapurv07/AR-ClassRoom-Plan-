import cv2
import threading
import time

class ARCamera:
    def __init__(self):
        self.running = False
        self.thread = None
        self.cap = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_camera_feed, daemon=True)
        self.thread.start()

    def _run_camera_feed(self):
        print("Starting camera feed...")
        self.cap = cv2.VideoCapture(0) 

        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            self.running = False
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            with self.frame_lock:
                self.latest_frame = frame
            
            time.sleep(0.01)
        
        if self.cap:
            self.cap.release()
        print("Camera feed stopped.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def is_running(self):
        return self.running

    def get_frame(self):
        frame = None
        with self.frame_lock:
            if self.latest_frame is not None:
                frame = self.latest_frame.copy()
        return frame