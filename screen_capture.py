import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self, width=400, height=400):
        self.sct = mss.mss()
        self.width = width
        self.height = height
        
        # Calculate screen center
        screen_width = self.sct.monitors[1]["width"]
        screen_height = self.sct.monitors[1]["height"]
        
        self.monitor = {
            "top": (screen_height - self.height) // 2,
            "left": (screen_width - self.width) // 2,
            "width": self.width,
            "height": self.height,
        }

    def capture(self):
        # Capture the screen
        screenshot = self.sct.grab(self.monitor)
        
        # Convert to numpy array and remove alpha channel (BGRA to BGR)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

if __name__ == "__main__":
    # Test capture speed
    import time
    sc = ScreenCapture()
    start_time = time.time()
    for _ in range(100):
        img = sc.capture()
    end_time = time.time()
    print(f"Average capture time: {(end_time - start_time) / 100 * 1000:.2f}ms")
    cv2.imshow("Test", img)
    cv2.waitKey(0)
