import ctypes
import time
import numpy as np

# Windows API constants
MOUSEEVENTF_MOVE = 0x0001

class MouseControl:
    def __init__(self, sensitivity=1.0, smoothness=0.2):
        self.sensitivity = sensitivity
        self.smoothness = smoothness # 0.0 to 1.0, higher is smoother

    def _move_mouse(self, dx, dy):
        # Using ctypes for low-level mouse movement (avoids common anti-cheat detection)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

    def _bezier_curve(self, start, end, control, t):
        # Quadratic Bezier Curve: (1-t)^2*P0 + 2*(1-t)*t*P1 + t^2*P2
        return (1-t)**2 * start + 2*(1-t)*t * control + t**2 * end

    def smooth_move(self, target_x, target_y, screen_center_x=200, screen_center_y=200):
        # Calculate relative distance from center
        dx = (target_x - screen_center_x) * self.sensitivity
        dy = (target_y - screen_center_y) * self.sensitivity
        
        if abs(dx) < 1 and abs(dy) < 1:
            return

        # Bezier Smooth Aim implementation
        # We simulate a curve by breaking the movement into small steps
        steps = 5 # Number of steps to reach target
        
        # Control point for quadratic Bezier (adds a slight curve)
        # We offset the control point slightly from the linear path
        ctrl_x = dx / 2 + (np.random.random() - 0.5) * 5
        ctrl_y = dy / 2 + (np.random.random() - 0.5) * 5
        
        last_x, last_y = 0, 0
        for i in range(1, steps + 1):
            t = i / steps
            # Bezier formula
            curr_x = self._bezier_curve(0, dx, ctrl_x, t)
            curr_y = self._bezier_curve(0, dy, ctrl_y, t)
            
            # Relative move
            move_x = curr_x - last_x
            move_y = curr_y - last_y
            
            # Apply smoothness factor (slow down the movement)
            self._move_mouse(move_x * (1 - self.smoothness), move_y * (1 - self.smoothness))
            
            last_x, last_y = curr_x, curr_y
            # Small delay between steps for smoothness
            time.sleep(0.001)

if __name__ == "__main__":
    # Test mouse movement
    mc = MouseControl(sensitivity=0.5, smoothness=0.5)
    print("Moving mouse smoothly in 2 seconds...")
    time.sleep(2)
    # Simulate move to (250, 250) from (200, 200)
    for _ in range(10):
        mc.smooth_move(250, 250)
        time.sleep(0.01)
