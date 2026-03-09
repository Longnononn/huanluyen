from ultralytics import YOLO
import os

def train_model(data_yaml="dataset/dataset.yaml", epochs=50, imgsz=400):
    """
    Huấn luyện AI Model YOLOv8 dựa trên bộ dữ liệu đã thu thập.
    """
    print(f"Bắt đầu huấn luyện với file: {data_yaml}")
    
    # 1. Khởi tạo model (Dùng bản nano cho nhẹ và nhanh)
    model = YOLO("yolov8n.pt")
    
    # 2. Bắt đầu huấn luyện
    # device=0 nếu có GPU NVIDIA, nếu không thì dùng 'cpu'
    model.train(
        data=data_yaml, 
        epochs=epochs, 
        imgsz=imgsz, 
        batch=16, 
        name="ai_assistant_v1",
        device='0' # Thay bằng 'cpu' nếu không có GPU
    )
    
    print("Huấn luyện hoàn tất! Model mới nằm trong thư mục 'runs/detect/ai_assistant_v1/weights/best.pt'")
    
    # 3. Xuất sang ONNX để tối ưu hiệu năng cho PC Assistant
    print("Đang xuất sang định dạng ONNX...")
    best_model_path = "runs/detect/ai_assistant_v1/weights/best.pt"
    if os.path.exists(best_model_path):
        trained_model = YOLO(best_model_path)
        trained_model.export(format="onnx", imgsz=imgsz)
        print(f"Đã tạo file ONNX: runs/detect/ai_assistant_v1/weights/best.onnx")
    else:
        print("Không tìm thấy file model sau khi train.")

if __name__ == "__main__":
    # Đảm bảo đã có file dataset.yaml trước khi chạy
    if os.path.exists("dataset/dataset.yaml"):
        train_model()
    else:
        print("Lỗi: Không tìm thấy thư mục 'dataset'. Hãy chạy 'run_data_collection.py' trước!")
