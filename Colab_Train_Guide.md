# Hướng dẫn Huấn luyện YOLOv8 trên Google Colab (MIỄN PHÍ GPU)

Bạn hãy copy từng ô code dưới đây vào [Google Colab](https://colab.research.google.com/) để bắt đầu huấn luyện. 
**Lưu ý:** Trước khi chạy, hãy nén thư mục `dataset/` thành file `dataset.zip` và tải lên Google Drive của bạn.

**QUAN TRỌNG:** Khi copy, chỉ lấy nội dung **BÊN TRONG** các khối code, không copy chữ `python` ở đầu mỗi khối.

---

### **Ô 1: Cài đặt thư viện & Kiểm tra GPU**
```python
!pip install ultralytics
import torch
print(f"Sẵn sàng huấn luyện trên: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

### **Ô 2: Kết nối với Google Drive**
```python
from google.colab import drive
drive.mount('/content/drive')
```

### **Ô 3: Giải nén Dataset (Giả sử bạn để file dataset.zip ở thư mục gốc của Drive)**
```python
!unzip /content/drive/MyDrive/dataset.zip -d /content/
```

### **Ô 4: Bắt đầu Huấn luyện**
```python
from ultralytics import YOLO

# 1. Khởi tạo model nano (Nhẹ & Nhanh)
model = YOLO('yolov8n.pt')

# 2. Huấn luyện (Data.yaml phải có đường dẫn đúng trong Colab)
# Bạn có thể cần sửa file dataset.yaml trên Drive thành:
# path: /content/dataset/
model.train(data='/content/dataset/dataset.yaml', epochs=50, imgsz=400, device=0, workers=8, batch=16)
```

### **Ô 5: Xuất sang ONNX & Tải về**
```python
# Tìm file best.pt sau khi train xong
import os
best_model_path = '/content/runs/detect/train/weights/best.pt'

if os.path.exists(best_model_path):
    # Load model đã train và xuất sang ONNX
    trained_model = YOLO(best_model_path)
    trained_model.export(format='onnx', imgsz=400)
    
    # Download file về máy tính
    from google.colab import files
    files.download('/content/runs/detect/train/weights/best.onnx')
    print("Đang tải file ONNX về máy của bạn...")
else:
    print("Không tìm thấy model sau khi train. Hãy kiểm tra lại thư mục 'runs'.")
```

---

### **Các bước thực hiện nhanh:**
1.  **Nén:** Chuột phải vào thư mục `dataset/` trên máy tính -> Chọn "Send to Compressed (zipped) folder".
2.  **Tải lên:** Kéo file `dataset.zip` vào Google Drive.
3.  **Mở Colab:** Vào [Colab](https://colab.research.google.com/), chọn "New Notebook".
4.  **Cấu hình GPU:** Vào `Edit` -> `Notebook settings` -> `Hardware accelerator` -> Chọn **T4 GPU** -> Nhấn `Save`.
5.  **Chạy:** Copy và chạy lần lượt 5 ô code ở trên.
