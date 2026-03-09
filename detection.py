import os
import cv2
import numpy as np
import requests
import onnxruntime as ort

class Detection:
    def __init__(self, model_path="yolov8n.onnx", target_class=0):
        """
        Chiến thuật Pure ONNX: Loại bỏ Torch/Ultralytics để sửa lỗi DLL WinError 1114.
        """
        self.github_model_url = "https://github.com/Longnononn/huanluyen/releases/download/v1.0/yolov8n.onnx"
        
        # 1. Tải model từ GitHub nếu chưa có
        if not os.path.exists(model_path):
            self._download_from_github(self.github_model_url, model_path)
            
        # 2. Khởi tạo ONNX Runtime Session (chỉ dùng CPU để ổn định nhất)
        try:
            self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception as e:
            print(f"Lỗi khởi tạo ONNX Session: {e}")
            self.session = None

        self.target_class = target_class
        self.center_x = 208 # Tọa độ tâm của vùng 416x416
        self.center_y = 208

    def _download_from_github(self, url, dest_path):
        """Tải Model từ GitHub Releases (100% Free Storage)."""
        print(f"Đang tải AI Model từ GitHub Releases: {url}")
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Đã tải xong Model: {dest_path}")
            else:
                print(f"Không thể tải từ GitHub (Lỗi {response.status_code}).")
        except Exception as e:
            print(f"Lỗi hệ thống khi tải từ GitHub: {e}")

    def preprocess(self, img):
        # Resize về 416x416 (theo yêu cầu của model ONNX)
        img = cv2.resize(img, (416, 416))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1)) # HWC to CHW
        img = np.expand_dims(img, axis=0) # Add batch dimension
        return img

    def detect_enemies(self, frame):
        if self.session is None:
            return None, []

        # 1. Tiền xử lý
        input_tensor = self.preprocess(frame)
        
        # 2. Chạy Inference
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        
        # 3. Hậu xử lý (NMS đơn giản cho YOLOv8)
        # Output shape: [1, 84, 3360] (84 = 4 box + 80 class)
        output = np.squeeze(outputs[0])
        output = output.transpose() # [3360, 84]
        
        boxes = []
        confs = []
        
        for i in range(len(output)):
            # Lấy confidence của target_class
            # YOLOv8 format: x, y, w, h, cls0, cls1, ...
            conf = output[i][4 + self.target_class]
            if conf > 0.5:
                x, y, w, h = output[i][0:4]
                # Chuyển về tọa độ [0, 400]
                x1 = (x - w / 2)
                y1 = (y - h / 2)
                x2 = (x + w / 2)
                y2 = (y + h / 2)
                boxes.append([x1, y1, x2, y2])
                confs.append(float(conf))

        if not boxes:
            return None, []

        # Sắp xếp theo độ tin cậy và chọn đối tượng gần tâm nhất
        enemies = []
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            target_x = x1 + (x2 - x1) / 2
            target_y = y1 + (y2 - y1) / 4 # Ngắm vào đầu (top 25%)
            
            dist = np.sqrt((target_x - self.center_x)**2 + (target_y - self.center_y)**2)
            
            enemies.append({
                'coords': (target_x, target_y),
                'distance': dist,
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'conf': confs[i]
            })

        enemies.sort(key=lambda x: x['distance'])
        return enemies[0], enemies

if __name__ == "__main__":
    # Test
    det = Detection()
    test_img = np.zeros((400, 400, 3), dtype=np.uint8)
    best, all_e = det.detect_enemies(test_img)
    print("Pure ONNX Test OK!")
