from tiktok_logic import TikTokManager

def log(msg):
    print(msg)

class FakeApp:
    def __init__(self):
        self.sw_comment = None
        self.sw_gift = None
        self.sw_join = None
        self.sw_like = None

        class Dummy:
            def get(self):
                return True

        self.read_mode = Dummy()
        self.speed_slider = Dummy()

# =========================

if __name__ == "__main__":
    manager = TikTokManager(log)
    app = FakeApp()

    username = input("Nhập TikTok username: ").strip().lstrip("@")

    if not username:
        print("❌ Bạn chưa nhập username!")
        exit()

    manager.connect(username, app)

    print("🚀 Đang chạy... (đọc comment + gift + like)")

    try:
        while True:
            input()
    except KeyboardInterrupt:
        manager.disconnect()
        print("👋 Đã thoát")