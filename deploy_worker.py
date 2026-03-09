import subprocess
import os

def deploy_worker():
    """
    Tự động đăng nhập và cập nhật Worker lên Cloudflare sử dụng Wrangler CLI.
    Không cần điền Token hay Account ID thủ công vào mã nguồn.
    """
    worker_dir = "worker"
    
    if not os.path.exists(worker_dir):
        print(f"❌ LỖI: Không tìm thấy thư mục {worker_dir}")
        return

    print("--- ☁️ CLOUDFLARE WORKER DEPLOYMENT ---")
    
    try:
        # 1. Kiểm tra trạng thái đăng nhập
        print("🔍 Đang kiểm tra trạng thái đăng nhập...")
        # Sử dụng npx wrangler whoami để kiểm tra
        # Thêm encoding='utf-8' và errors='ignore' để tránh lỗi Unicode trên Windows
        login_proc = subprocess.run(
            ["npx", "wrangler", "whoami"], 
            capture_output=True, 
            text=True, 
            shell=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # Kiểm tra an toàn stdout
        is_logged_in = False
        if login_proc.stdout and "Not logged in" not in login_proc.stdout:
            is_logged_in = True
            
        if not is_logged_in or login_proc.returncode != 0:
            print("⚠️ Bạn chưa đăng nhập. Đang mở trình duyệt để đăng nhập Cloudflare...")
            subprocess.run(["npx", "wrangler", "login"], check=True, shell=True)
        else:
            print("✅ Đã đăng nhập vào Cloudflare.")

        # 2. Triển khai Worker
        print(f"🚀 Đang đẩy mã nguồn lên Cloudflare từ thư mục '{worker_dir}'...")
        # Chạy wrangler deploy bên trong thư mục worker
        deploy_proc = subprocess.run(
            ["npx", "wrangler", "deploy"], 
            cwd=worker_dir, 
            check=True,
            shell=True # Cần thiết trên Windows
        )
        
        if deploy_proc.returncode == 0:
            print("\n✅ THÀNH CÔNG! Worker đã được cập nhật và kích hoạt.")
            print("🔗 Bạn có thể kiểm tra trên Cloudflare Dashboard.")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ LỖI trong quá trình xử lý: {e}")
    except Exception as e:
        print(f"\n❌ Lỗi hệ thống: {e}")

if __name__ == "__main__":
    deploy_worker()
