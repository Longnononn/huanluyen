import os
import cv2
import yt_dlp
import numpy as np
import requests
import base64
import onnxruntime as ort
import yaml

class DataCollector:
    def __init__(self, model_path="yolov8n.onnx", imgbb_api_key=None):
        """
        Pure ONNX Data Collector: Loại bỏ Ultralytics để chạy mượt trên i5-6200U.
        """
        # Tải model nếu chưa có
        if not os.path.exists(model_path):
            url = "https://github.com/Longnononn/huanluyen/releases/download/v1.0/yolov8n.onnx"
            self._download_file(url, model_path)
            
        try:
            self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception as e:
            print(f"Lỗi khởi tạo ONNX: {e}")
            self.session = None

        self.imgbb_api_key = imgbb_api_key
        self.base_dir = "dataset"
        self.train_dir = os.path.join(self.base_dir, "train")
        self.review_dir = os.path.join(self.base_dir, "review")
        
        for d in [self.train_dir, self.review_dir, 
                  os.path.join(self.train_dir, "images"), 
                  os.path.join(self.train_dir, "labels")]:
            os.makedirs(d, exist_ok=True)

    def _download_file(self, url, dest):
        print(f"Đang tải: {url}")
        r = requests.get(url, stream=True)
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    def upload_to_imgbb(self, image_path):
        if not self.imgbb_api_key: return None
        url = "https://api.imgbb.com/1/upload"
        try:
            with open(image_path, "rb") as file:
                payload = {
                    "key": self.imgbb_api_key,
                    "image": base64.b64encode(file.read()).decode('utf-8'),
                }
                response = requests.post(url, payload, timeout=15)
                if response.status_code == 200:
                    return response.json()['data']['url']
        except: pass
        return None

    def download_video(self, url, output_name="input_video.mp4"):
        print(f"Đang tải video từ: {url}")
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_name,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_name

    def process_video(self, video_path, frame_interval=10, conf_threshold=0.8):
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        saved_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            if frame_count % frame_interval == 0:
                # Preprocess
                img = cv2.resize(frame, (400, 400))
                img_input = img.astype(np.float32) / 255.0
                img_input = np.transpose(img_input, (2, 0, 1))
                img_input = np.expand_dims(img_input, axis=0)
                
                # Inference
                outputs = self.session.run([self.output_name], {self.input_name: img_input})
                output = np.squeeze(outputs[0]).transpose()
                
                persons = []
                for i in range(len(output)):
                    conf = output[i][4] # Class 0: Person
                    if conf > 0.5:
                        persons.append({'box': output[i][0:4], 'conf': conf})
                
                if persons:
                    max_conf = max([p['conf'] for p in persons])
                    img_name = f"frame_{frame_count}.jpg"
                    
                    if max_conf >= conf_threshold:
                        img_path = os.path.join(self.train_dir, "images", img_name)
                        cv2.imwrite(img_path, frame)
                        if self.imgbb_api_key: self.upload_to_imgbb(img_path)
                        
                        label_path = os.path.join(self.train_dir, "labels", f"frame_{frame_count}.txt")
                        with open(label_path, "w") as f:
                            for p in persons:
                                if p['conf'] >= 0.5:
                                    x, y, w, h = p['box']
                                    f.write(f"0 {x/400} {y/400} {w/400} {h/400}\n")
                        saved_count += 1
            frame_count += 1
        cap.release()
        print(f"Hoàn tất! Đã lưu {saved_count} ảnh.")

    def create_dataset_yaml(self):
        data = {'path': os.path.abspath(self.base_dir), 'train': 'train/images', 'val': 'train/images', 'names': {0: 'person'}}
        with open(os.path.join(self.base_dir, "dataset.yaml"), 'w') as f:
            yaml.dump(data, f)
