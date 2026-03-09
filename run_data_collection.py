from data_collector import DataCollector
import sys

def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python run_data_collection.py <YOUTUBE_URL>")
        return

    url = sys.argv[1]
    # Tích hợp API Key ImgBB từ người dùng
    imgbb_key = "c68e2c6a926f63a42b151bb0b1a1a786"
    collector = DataCollector(imgbb_api_key=imgbb_key)
    
    # 1. Tải video
    video_file = collector.download_video(url)
    
    # 2. Xử lý video: lấy frame và gán nhãn tự động
    # frame_interval=10 (cứ 10 frame lấy 1)
    # conf_threshold=0.8 (độ tự tin > 80% lưu vào /train)
    collector.process_video(video_file, frame_interval=10, conf_threshold=0.8)
    
    # 3. Tạo cấu hình dataset
    collector.create_dataset_yaml()

if __name__ == "__main__":
    main()
