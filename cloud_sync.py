import requests
import json
import os

class CloudSync:
    def __init__(self, api_endpoint="https://ai-backend-system.longnononpro.workers.dev/"):
        """
        Chiến thuật Hybrid (100% Free): 
        Config được lưu trữ tại Cloudflare Workers (D1) - Miễn phí, không cần thẻ.
        Model lưu trữ tại GitHub Releases.
        """
        self.api_endpoint = api_endpoint
        self.config_file = "pc_config.json"
        self.github_repo = "Longnononn/huanluyen" # Thay bằng repo của bạn
        self.default_config = {
            "sensitivity": 0.35,
            "smoothness": 0.6,
            "recoil_compensation": 1.2,
            "target_class": 0, # Person
            "auto_aim_key": "right_click",
            "model_version": "v1.0"
        }

    def check_for_model_update(self, current_version):
        """Kiểm tra GitHub Releases xem có model 'best.onnx' mới hơn không."""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name']
                
                if latest_version != current_version:
                    print(f"🚀 Tìm thấy Model mới ({latest_version})! Đang tải...")
                    for asset in release_data['assets']:
                        if asset['name'] == 'best.onnx':
                            download_url = asset['browser_download_url']
                            self._download_model(download_url, "best.onnx")
                            return latest_version
            return current_version
        except Exception as e:
            print(f"❌ Lỗi kiểm tra GitHub Release: {e}")
            return current_version

    def _download_model(self, url, dest):
        print(f"📥 Đang tải Model từ: {url}")
        try:
            r = requests.get(url, stream=True)
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("✅ Đã cập nhật Model mới thành công!")
        except Exception as e:
            print(f"❌ Lỗi tải Model: {e}")

    def trigger_cloud_training(self):
        """Kích hoạt GitHub Action 'Auto Train' thông qua Cloudflare Worker."""
        try:
            # Gửi yêu cầu tới Worker để Worker thay mặt ta gọi GitHub API (Bảo mật hơn)
            payload = {"action": "trigger_training", "repo": self.github_repo}
            response = requests.post(self.api_endpoint, json=payload, timeout=15)
            if response.status_code == 200:
                print("🚀 Đã yêu cầu Server bắt đầu Huấn luyện AI mới!")
                return True
            else:
                print(f"❌ Server từ chối yêu cầu (Code {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Lỗi kích hoạt Cloud Training: {e}")
            return False

    def fetch_config(self):
        """Tải cấu hình từ Cloudflare Workers D1."""
        try:
            # Gửi request GET tới Worker để lấy dữ liệu từ D1 Database
            response = requests.get(self.api_endpoint, timeout=10)
            if response.status_code == 200:
                remote_config = response.json()
                
                # Gộp cấu hình mặc định với cấu hình từ Cloud để tránh thiếu key (như target_class)
                config = self.default_config.copy()
                config.update(remote_config)
                
                # Lưu vào file local để dự phòng
                with open(self.config_file, 'w') as f:
                    json.dump(config, f)
                print(f"Đã đồng bộ config từ Cloudflare D1: {config}")
                return config
            else:
                print(f"Lỗi phản hồi từ Worker (Code {response.status_code}). Sử dụng cache.")
            
            # Giả lập đọc file cục bộ nếu không có mạng hoặc lỗi server
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return self.default_config
        except Exception as e:
            print(f"Lỗi kết nối Cloudflare D1: {e}. Sử dụng config mặc định.")
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_config

    def send_telemetry(self, gun, offset, kill_time):
        """Gửi dữ liệu phân tích sau pha giao tranh về Cloudflare (Nếu Worker hỗ trợ)."""
        data = {
            "type": "telemetry",
            "gun": gun,
            "offset": offset,
            "kill_time": kill_time
        }
        try:
            # response = requests.post(self.api_endpoint, json=data, timeout=5)
            # return response.status_code == 200
            print(f"Đã gửi telemetry giả lập: {data}")
            return True
        except Exception as e:
            print(f"Lỗi gửi telemetry: {e}")
            return False

    def update_remote_config(self, new_config):
        """Cập nhật cấu hình lên Cloudflare D1 (Nếu Worker hỗ trợ POST)."""
        try:
            response = requests.post(self.api_endpoint, json=new_config, timeout=10)
            if response.status_code == 200:
                print(f"Đã cập nhật Cloudflare D1 thành công: {new_config}")
                return True
            else:
                print(f"Lỗi cập nhật D1 (Code {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"Lỗi hệ thống khi cập nhật D1: {e}")
            return False

if __name__ == "__main__":
    cs = CloudSync()
    print("Fetching config...")
    config = cs.fetch_config()
    print(f"Config: {config}")
    print("Sending test telemetry...")
    cs.send_telemetry("AK-47", 15.5, 2.3)
