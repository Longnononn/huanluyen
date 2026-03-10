import sys
import os
import threading
import time
import keyboard
import win32api
import win32con
import cv2

# QUAN TRỌNG: Phải import Detection (onnxruntime) TRƯỚC PyQt5 
# để tránh lỗi DLL initialization routine failed (WinError 1114)
from detection import Detection

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor

from screen_capture import ScreenCapture
from mouse_control import MouseControl
from cloud_sync import CloudSync

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Center of screen (416x416 area cho model YOLO)
        self.capture_size = 416
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            (screen.width() - self.capture_size) // 2,
            (screen.height() - self.capture_size) // 2,
            self.capture_size,
            self.capture_size
        )
        
        self.enemies = []
        self.show_debug = True
        
    def set_enemies(self, enemies):
        self.enemies = enemies
        self.update()

    def paintEvent(self, event):
        if not self.show_debug:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw target boxes
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)
        
        for enemy in self.enemies:
            x1, y1, x2, y2 = enemy['bbox']
            painter.drawRect(x1, y1, x2-x1, y2-y1)
            
            # Draw aim point
            tx, ty = enemy['coords']
            painter.setBrush(QColor(255, 0, 0))
            painter.drawEllipse(int(tx)-3, int(ty)-3, 6, 6)

class AIAssistant:
    def __init__(self):
        # 1. Load Config & Check for updates
        self.cloud = CloudSync()
        self.config = self.cloud.fetch_config()
        
        # 2. Tự động kiểm tra bản cập nhật "Bộ não" AI
        current_v = self.config.get('model_version', 'v1.0')
        new_v = self.cloud.check_for_model_update(current_v)
        if new_v != current_v:
            self.config['model_version'] = new_v
            # Cập nhật lại config mới cho server
            self.cloud.update_remote_config(self.config)

        # 3. Modules
        model_path = "best.onnx" if os.path.exists("best.onnx") else "yolov8n.onnx"
        self.sc = None # Sẽ khởi tạo trong main_loop thread
        self.det = Detection(model_path=model_path, target_class=self.config['target_class'])
        self.mc = MouseControl(
            sensitivity=self.config['sensitivity'], 
            smoothness=self.config['smoothness']
        )
        
        self.running = True
        self.aim_active = False
        self.debug_mode = True
        self.auto_shoot = True # Tự động bóp cò
        self.auto_afk = True   # Chế độ treo máy tự di chuyển
        self.is_dead = False
        self.hard_case_count = 0 # Đếm số ca khó để tự động train
        
        # Overlay
        self.app = QApplication(sys.argv)
        self.overlay = OverlayWindow()
        self.overlay.show()
        
        # Hotkeys
        keyboard.add_hotkey('f9', self.toggle_menu)
        keyboard.add_hotkey('f10', self.capture_hard_case) # Phím để Bot tự học lỗi sai
        
        self.current_frame = None
        
        # Start main loop in thread
        self.loop_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.loop_thread.start()
        
        # Start AFK movement loop
        self.afk_thread = threading.Thread(target=self.afk_movement_loop, daemon=True)
        self.afk_thread.start()
        
        # UI Loop
        sys.exit(self.app.exec_())

    def toggle_menu(self):
        self.debug_mode = not self.debug_mode
        self.overlay.show_debug = self.debug_mode
        print(f"Debug Mode: {self.debug_mode}")

    def capture_hard_case(self):
        if self.current_frame is not None:
            # 1. Lưu local để dự phòng
            os.makedirs("dataset/hard_cases", exist_ok=True)
            img_name = f"fail_{int(time.time())}.jpg"
            img_path = os.path.join("dataset/hard_cases", img_name)
            cv2.imwrite(img_path, self.current_frame)
            
            # 2. Upload tự động lên ImgBB (Sử dụng API Key của bạn)
            api_key = "c68e2c6a926f63a42b151bb0b1a1a786" 
            print(f"--- Đang gửi 'Bằng chứng lỗi' lên Server... ---")
            
            def upload_task():
                try:
                    import base64
                    import requests
                    import pydirectinput
                    with open(img_path, "rb") as file:
                        url = "https://api.imgbb.com/1/upload"
                        payload = {
                            "key": api_key,
                            "image": base64.b64encode(file.read()).decode('utf-8'),
                        }
                        res = requests.post(url, payload, timeout=15)
                        if res.status_code == 200:
                            img_url = res.json()['data']['url']
                            print(f"✅ Đã Up lên Cloud: {img_url}")
                            # Gửi link về Cloudflare D1 để quản lý
                            self.cloud.send_telemetry("ERROR_LOG", img_url, "AI_MISSED_TARGET")
                            
                            # TỰ ĐỘNG KÍCH HOẠT TRAIN KHI ĐỦ 10 CA KHÓ
                            self.hard_case_count += 1
                            if self.hard_case_count >= 10:
                                print("🔥 Đã tích lũy đủ 10 ca lỗi. Đang kích hoạt Huấn luyện AI tự động...")
                                if self.cloud.trigger_cloud_training():
                                    self.hard_case_count = 0 # Reset sau khi kích hoạt
                        else:
                            print(f"❌ Lỗi Upload: {res.text}")
                    
                    # 3. TỰ ĐỘNG HỒI SINH (Nhấn phím sau 5 giây để tiếp tục leo rank)
                    if self.auto_afk:
                        time.sleep(5)
                        print("--- 🔄 Đang tự động nhấn phím Hồi sinh (Enter/Space)... ---")
                        pydirectinput.press('enter')
                        pydirectinput.press('space')
                except Exception as e:
                    print(f"❌ Hệ thống Cloud lỗi: {e}")

            # Chạy upload ngầm để không làm lag game
            threading.Thread(target=upload_task, daemon=True).start()

    def afk_movement_loop(self):
        """Luồng di chuyển tự động để Bot không đứng yên một chỗ."""
        import pydirectinput
        import random
        keys = ['w', 'a', 's', 'd', 'space']
        
        while self.running:
            if self.auto_afk and not self.is_dead:
                # Ngẫu nhiên chọn một phím di chuyển
                key = random.choice(keys)
                duration = random.uniform(0.1, 0.5)
                pydirectinput.keyDown(key)
                time.sleep(duration)
                pydirectinput.keyUp(key)
                # Chờ một lúc trước khi di chuyển tiếp
                time.sleep(random.uniform(1, 3))
            else:
                time.sleep(1)

    def check_death_screen(self, frame):
        """Tự động phát hiện khi nhân vật chết bằng cách quét màu sắc."""
        # Ví dụ: Kiểm tra pixel ở tâm (208, 208) xem có màu đỏ sẫm đặc trưng của death screen không
        # Bạn có thể thay đổi tọa độ và màu sắc này tùy vào game của bạn
        center_pixel = frame[208, 208] 
        # BGR: Red > 150, Green < 50, Blue < 50 (Đây là màu đỏ máu)
        if center_pixel[2] > 180 and center_pixel[1] < 60 and center_pixel[0] < 60:
            if not self.is_dead:
                print("--- ⚠️ PHÁT HIỆN NHÂN VẬT ĐÃ CHẾT! Đang tự động báo cáo lỗi... ---")
                self.is_dead = True
                self.capture_hard_case() # Tự động chụp và upload lên Cloud
        else:
            self.is_dead = False

    def main_loop(self):
        # QUAN TRỌNG: MSS (ScreenCapture) phải được khởi tạo bên trong luồng sử dụng nó
        self.sc = ScreenCapture(width=416, height=416)
        
        import pydirectinput # Để giả lập chuột trái
        pydirectinput.PAUSE = 0 # Tối ưu tốc độ click
        
        print("Bot Tự Trị Đã Bật. F9: Menu | Auto-Aim & Auto-Shoot: ON")
        
        while self.running:
            # 1. Screen Capture
            frame = self.sc.capture()
            self.current_frame = frame
            
            # 2. Tự động nhận diện cái chết để báo cáo lỗi
            self.check_death_screen(frame)
            
            # 3. AI Detection
            best_enemy, all_enemies = self.det.detect_enemies(frame)
            
            # 4. Update Overlay
            if self.debug_mode:
                self.overlay.set_enemies(all_enemies)
            else:
                self.overlay.set_enemies([])
            
            # 5. Tự động ngắm & bắn (Auto-Aim & Auto-Shoot)
            if best_enemy:
                tx, ty = best_enemy['coords']
                conf = best_enemy['conf']
                
                # Tự động di chuyển chuột
                self.mc.smooth_move(tx, ty)
                
                # Tự động bóp cò nếu độ tin cậy > 90% (AI chắc chắn là địch)
                if self.auto_shoot and conf > 0.90:
                    pydirectinput.click() # Tự động bắn!
                
            # FPS Control (Sleep to avoid CPU saturation)
            time.sleep(0.005) # ~200 iterations per sec

if __name__ == "__main__":
    assistant = AIAssistant()
