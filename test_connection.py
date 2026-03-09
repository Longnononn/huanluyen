import requests

def test_trigger():
    url = "https://ai-backend-system.longnononpro.workers.dev/"
    payload = {
        "action": "trigger_training",
        "repo": "Longnononn/huanluyen"
    }
    
    print(f"🚀 Đang gửi lệnh test tới: {url}")
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Phản hồi từ Server: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ THÀNH CÔNG! Hãy vào GitHub của bạn, mục 'Actions' để xem nó đã bắt đầu Train chưa.")
        else:
            print("\n❌ THẤY LỖI! Có thể bạn chưa đặt GITHUB_TOKEN trong Cloudflare Secrets.")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    test_trigger()
