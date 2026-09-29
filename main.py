import customtkinter as ctk
import data_manager as dm
from PIL import Image
import os
import re
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("TikTok TTS - Dashboard Professional")

        icon_path = os.path.join("data", "icon", "icon.ico")
        if os.path.exists(icon_path):
            self.after(200, lambda: self.iconbitmap(icon_path))

        # --- BIẾN KIỂM SOÁT MODAL ---
        self.opened_modal = None

        # --- TỰ ĐỘNG TÍNH KÍCH THƯỚC MÀN HÌNH ---
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        app_w = int(screen_w * 0.9)
        app_h = int(screen_h * 0.85)
        self.geometry(f"{app_w}x{app_h}+50+20")

        # --- TRẠNG THÁI & LOGIC ---
        self.is_connected = False
        self.frames = {}
        self.nav_buttons = []
        self.connect_buttons = []

        self.settings = {
            "read_comment": True,
            "read_gift": True,
            "read_join": False,
            "read_like": False,
            "read_mode": "Chỉ đọc nội dung CMT",
            "speed": 1.0,
            "volume": 1.0,
            "theme": "Light"
        }

        self.read_comment_var = ctk.BooleanVar(value=True)
        self.read_gift_var = ctk.BooleanVar(value=True)
        self.read_join_var = ctk.BooleanVar(value=False)
        self.read_like_var = ctk.BooleanVar(value=False)
        self.read_mode_var = ctk.StringVar(value="Chỉ đọc nội dung CMT")
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.volume_var = ctk.DoubleVar(value=1.0)
        self.theme_var = ctk.StringVar(value="Light")
        
        self.tpl_comment_var = ctk.StringVar(value="{name} nói: {comment}")
        self.tpl_gift_var = ctk.StringVar(value="{name} tặng {gift}")
        self.tpl_join_var = ctk.StringVar(value="{name} đã vào phòng")
        self.tpl_like_var = ctk.StringVar(value="{name} thả {count} tim")

        # Alias variables expected by TikTokManager (keeps backward compatibility)
        self.sw_comment_var = self.read_comment_var
        self.sw_gift_var = self.read_gift_var
        self.sw_join_var = self.read_join_var
        self.sw_like_var = self.read_like_var

        self.session_stats = {
            "comments": 0,
            "gifts": 0,
            "joins": 0,
            "likes": 0,
            "gift_history": [],
            "top_gifters": {}
        }

        # ✅ Khởi tạo TikTokManager sớm để dùng add_log
        from tiktok_logic import TikTokManager
        self.tiktok_manager = TikTokManager(self.add_log)

        self.load_settings()

        # --- CẤU TRÚC LƯỚI TỔNG THỂ ---
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # --- KHỞI TẠO GIAO DIỆN ---
        self.setup_sidebar()

        self.main_view = ctk.CTkFrame(self, fg_color=("#f2f2f7", "#000000"), corner_radius=0)
        self.main_view.grid(row=0, column=1, sticky="nsew")

        self.setup_frames()
        self.setup_right_settings()

        self.show_frame("Dashboard")

        self.sidebar_frame.grid_propagate(False)
# CTkScrollableFrame manages its own size — no grid_propagate needed

    # ==============================
    # ✅ HÀM ADD_LOG
    # ==============================
    def add_log(self, message):
        """Ghi log vào ô nhật ký Live một cách an toàn từ bất kỳ thread nào"""
        def _write():
            if hasattr(self, "log_box"):
                self.log_box.configure(state="normal")
                self.log_box.insert("end", f"{message}\n")
                self.log_box.see("end")
        self.after(0, _write)

    def load_settings(self):
        data = dm.load_json(dm.CONFIG_FILE)
        if not isinstance(data, dict):
            return

        self.settings.update(data)
        self.read_comment_var.set(self.settings.get("read_comment", True))
        self.read_gift_var.set(self.settings.get("read_gift", True))
        self.read_join_var.set(self.settings.get("read_join", False))
        self.read_like_var.set(self.settings.get("read_like", False))
        self.read_mode_var.set(self.settings.get("read_mode", "Chỉ đọc nội dung CMT"))
        self.speed_var.set(self.settings.get("speed", 1.0))
        self.volume_var.set(self.settings.get("volume", 1.0))
        self.theme_var.set(self.settings.get("theme", "Light"))
        self.tpl_comment_var.set(self.settings.get("text_template_comment", "{name} nói: {comment}"))
        self.tpl_gift_var.set(self.settings.get("text_template_gift", "{name} tặng {gift}"))
        self.tpl_join_var.set(self.settings.get("text_template_join", "{name} đã vào phòng"))
        self.tpl_like_var.set(self.settings.get("text_template_like", "{name} thả {count} tim"))
        ctk.set_appearance_mode(self.theme_var.get().lower())
        if hasattr(self, 'tiktok_manager'):
            self.tiktok_manager.set_speed(self.speed_var.get())
            self.tiktok_manager.set_volume(self.volume_var.get())

    def save_settings(self):
        self.settings.update({
            "read_comment": self.read_comment_var.get(),
            "read_gift": self.read_gift_var.get(),
            "read_join": self.read_join_var.get(),
            "read_like": self.read_like_var.get(),
            "read_mode": self.read_mode_var.get(),
            "speed": round(self.speed_var.get(), 1),
            "volume": round(self.volume_var.get(), 2),
            "theme": self.theme_var.get(),
            "text_template_comment": self.tpl_comment_var.get(),
            "text_template_gift": self.tpl_gift_var.get(),
            "text_template_join": self.tpl_join_var.get(),
            "text_template_like": self.tpl_like_var.get()
        })
        dm.save_json(dm.CONFIG_FILE, self.settings)

    def on_live_connected(self, username):
        self.is_connected = True
        self.update_ui_state()
        self.update_admin_page()
        self.add_log(f"✅ Đã kết nối tới @{username}")

    # ==============================
    # SIDEBAR
    # ==============================
    def setup_sidebar(self):
        icon_path = os.path.join("data", "icon")
        icon_size = (20, 20)

        try:
            img_dash  = ctk.CTkImage(Image.open(os.path.join(icon_path, "dashboard.ico")), size=icon_size)
            img_gift  = ctk.CTkImage(Image.open(os.path.join(icon_path, "gift.ico")),      size=icon_size)
            img_admin = ctk.CTkImage(Image.open(os.path.join(icon_path, "user.ico")),      size=icon_size)
            img_ban   = ctk.CTkImage(Image.open(os.path.join(icon_path, "ban.ico")),       size=icon_size)
            img_stats = ctk.CTkImage(Image.open(os.path.join(icon_path, "chart.ico")),     size=icon_size)
            img_note  = ctk.CTkImage(Image.open(os.path.join(icon_path, "note.ico")),      size=icon_size)
        except Exception as e:
            print(f"Lỗi nạp icon sidebar: {e}")
            img_dash = img_gift = img_admin = img_ban = img_stats = img_note = None

        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=("#ffffff", "#000000"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=25, padx=20)
        
        ctk.CTkLabel(header_frame, text="🎵 TikTok TTS", font=("Arial", 20, "bold"), 
                     text_color="#fe2c55").pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Dashboard Pro", font=("Arial", 10), 
                     text_color="#888").pack(anchor="w", pady=(2, 0))

        # Divider
        ctk.CTkLabel(self.sidebar_frame, text="", fg_color=("#e5e5ea", "#1c1c1e"), height=1).pack(fill="x", padx=15, pady=(0, 15))

        self.btn_dash      = self.create_nav_btn(" Dashboard",       img_dash,  lambda: self.show_frame("Dashboard"),     active=True)
        self.btn_gift      = self.create_nav_btn(" Lịch sử quà",     img_gift,  lambda: self.show_frame("Lịch sử quà"))
        self.btn_admin     = self.create_nav_btn(" Quản trị viên",    img_admin, lambda: self.show_frame("Quản trị viên"))
        self.btn_blacklist = self.create_nav_btn(" Từ khóa bị cấm",  img_ban,   lambda: self.show_frame("Từ khóa bị cấm"))
        self.btn_stats     = self.create_nav_btn(" Thống kê",         img_stats, lambda: self.show_frame("Thống kê"))
        self.btn_templates = self.create_nav_btn(" Văn bản tùy chỉnh",img_note,  lambda: self.show_frame("Văn bản tùy chỉnh"))

        ctk.CTkLabel(self.sidebar_frame, text="Phiên bản 2.0.1",
                     font=("Arial", 11), text_color="#444444").pack(side="bottom", pady=15)

    def create_nav_btn(self, text, image, command, active=False):
        btn = ctk.CTkButton(
            self.sidebar_frame, text=text, image=image, anchor="w",
            height=48, corner_radius=12, font=("Arial", 13, "bold"),
            fg_color="#fe2c55" if active else "transparent",
            text_color="#ffffff" if active else ("#000000", "#ffffff"), 
            hover_color="#ff5577" if active else ("#f2f2f7", "#1c1c1e"),
            command=command
        )
        btn.pack(fill="x", padx=12, pady=6)
        self.nav_buttons.append(btn)
        return btn

    # ==============================
    # FRAMES
    # ==============================
    def setup_frames(self):
        icon_path = os.path.join("data", "icon")
        size = (20, 20)

        try:
            img_gift_hist = ctk.CTkImage(Image.open(os.path.join(icon_path, "gift.ico")),  size=size)
            img_admin     = ctk.CTkImage(Image.open(os.path.join(icon_path, "user.ico")),  size=size)
            img_ban       = ctk.CTkImage(Image.open(os.path.join(icon_path, "ban.ico")),   size=size)
            img_stats     = ctk.CTkImage(Image.open(os.path.join(icon_path, "chart.ico")), size=size)
            img_note      = ctk.CTkImage(Image.open(os.path.join(icon_path, "note.ico")),  size=size)
        except Exception as e:
            print(f"Lỗi nạp icon frames: {e}")
            img_gift_hist = img_admin = img_ban = img_stats = img_note = None

        # 1. Dashboard
        dash_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_dashboard_content(dash_f)
        self.frames["Dashboard"] = dash_f

        # 2. Lịch sử quà
        gift_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_gift_history_content(gift_f, img_gift_hist)
        self.frames["Lịch sử quà"] = gift_f

        # 3. Quản trị viên
        admin_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_admin_content(admin_f, img_admin)
        self.frames["Quản trị viên"] = admin_f

        # 4. Từ khóa bị cấm
        black_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_blacklist_content(black_f, img_ban)
        self.frames["Từ khóa bị cấm"] = black_f

        # 5. Thống kê
        stats_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_stats_content(stats_f, img_stats)
        self.frames["Thống kê"] = stats_f

        # 6. Văn bản tùy chỉnh
        tpl_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.create_templates_content(tpl_f, img_note)
        self.frames["Văn bản tùy chỉnh"] = tpl_f

    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        if name in self.frames:
            self.frames[name].pack(fill="both", expand=True)
        for btn in self.nav_buttons:
            if name in btn.cget("text"):
                btn.configure(fg_color=("#ff4d6d", "#fe2c55"))
            else:
                btn.configure(fg_color="transparent")

    # ==============================
    # DASHBOARD
    # ==============================
    def create_dashboard_content(self, parent):
        icon_size = (20, 20)
        icon_path = os.path.join("data", "icon")

        try:
            img_gift   = ctk.CTkImage(Image.open(os.path.join(icon_path, "gift.ico")),          size=icon_size)
            img_key    = ctk.CTkImage(Image.open(os.path.join(icon_path, "keyword.ico")),        size=icon_size)
            img_emoji  = ctk.CTkImage(Image.open(os.path.join(icon_path, "emoji.ico")),          size=icon_size)
            img_pause  = ctk.CTkImage(Image.open(os.path.join(icon_path, "pause.ico")),          size=icon_size)
            img_trash  = ctk.CTkImage(Image.open(os.path.join(icon_path, "trash.ico")),          size=icon_size)
            img_report = ctk.CTkImage(Image.open(os.path.join(icon_path, "report_history.ico")), size=icon_size)
        except Exception as e:
            print(f"Lỗi nạp icon Dashboard: {e}")
            img_gift = img_key = img_emoji = img_pause = img_trash = img_report = None

        # Top Bar
        top_bar = ctk.CTkFrame(parent, height=110, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        top_bar.pack(fill="x", padx=15, pady=15)
        top_bar.pack_propagate(False)

        # Quick Actions Frame
        actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        ctk.CTkLabel(actions_frame, text="Hành động nhanh", font=("Arial", 11, "bold"),
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", pady=(0, 8))

        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")

        ctk.CTkButton(buttons_frame, text=" Quà tặng", image=img_gift, compound="left", width=100, height=50, corner_radius=14, fg_color="#fe2c55",
                      hover_color="#e11d48", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Quà tặng")).pack(side="left", padx=5)

        ctk.CTkButton(buttons_frame, text=" Từ khóa", image=img_key, compound="left", width=100, height=50, corner_radius=14, fg_color="#0a84ff",
                      hover_color="#007aff", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Từ khóa")).pack(side="left", padx=5)

        ctk.CTkButton(buttons_frame, text=" Emoji", image=img_emoji, compound="left", width=100, height=50, corner_radius=14, fg_color="#ff9f0a",
                      hover_color="#ff9500", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Emoji")).pack(side="left", padx=5)

        btn_conn = ctk.CTkButton(top_bar, text="Kết nối Live", width=140, height=40, corner_radius=20,
                                 fg_color="#fe2c55", hover_color="#e11d48",
                                 text_color="#fff", font=("Arial", 13, "bold"),
                                 command=self.toggle_connection)
        btn_conn.pack(side="right", padx=15, pady=15)
        self.connect_buttons.append(btn_conn)

        # Log Area
        log_container = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        log_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        header = ctk.CTkFrame(log_container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(header, text=" 📋 Nhật ký Live", 
                     text_color=("#000000", "#ffffff"),
                     font=("Arial", 18, "bold")).pack(side="left")

        self.status_label = ctk.CTkLabel(header, text="● Offline",
                                         text_color="#8e8e93",
                                         font=("Arial", 13, "bold"))
        self.status_label.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            log_container,
            fg_color=("#f2f2f7", "#000000"),
            text_color=("#000000", "#ffffff"),
            border_width=0,
            corner_radius=14, font=("Consolas", 12)
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        footer = ctk.CTkFrame(log_container, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(footer, text="⏸ Tạm dừng TTS", corner_radius=18,
                      fg_color="#ff9500", text_color="#fff",
                      hover_color="#ff9f0a", height=38, font=("Arial", 12, "bold"),
                      command=self.toggle_pause).pack(side="left", padx=5)

        ctk.CTkButton(footer, text="🗑 Xóa nhật ký", corner_radius=18,
                      fg_color="#ff3b30", text_color="#fff",
                      hover_color="#ff453a", height=38, font=("Arial", 12, "bold"),
                      command=lambda: self.log_box.delete("1.0", "end")).pack(side="left", padx=5)

    # ==============================
    def create_gift_history_content(self, parent, icon):
        header = ctk.CTkFrame(parent, height=70, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🎁 Lịch sử quà tặng", 
                     text_color=("#000000", "#ffffff"), font=("Arial", 18, "bold")).pack(side="left", padx=15, pady=15)
        
        ctk.CTkButton(header, text="🗑 Xóa lịch sử", fg_color="#ff3b30", hover_color="#ff453a",
                      text_color="#fff", width=140, corner_radius=15, font=("Arial", 12, "bold"),
                      command=self.clear_gift_history).pack(side="right", padx=15, pady=15)

        self.gift_history_box = ctk.CTkTextbox(parent, fg_color=("#ffffff", "#1c1c1e"), text_color=("#000000", "#ffffff"),
                                                border_width=0, corner_radius=20, font=("Consolas", 12))
        self.gift_history_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.gift_history_box.insert("0.0", "📭 Chưa có quà tặng nào")
        self.gift_history_box.configure(state="disabled")

        self.render_gift_history()

    def create_admin_content(self, parent, icon):
        header = ctk.CTkFrame(parent, height=70, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="👤 Quản trị viên", 
                     text_color=("#000000", "#ffffff"), font=("Arial", 18, "bold")).pack(side="left", padx=15, pady=15)

        main = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        main.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.admin_status = ctk.CTkLabel(main, text="📊 Trạng thái: Chưa kết nối",
                                         font=("Arial", 14, "bold"), text_color=("#333333", "#dddddd"))
        self.admin_status.pack(anchor="w", padx=20, pady=(20, 10))

        self.admin_details = ctk.CTkTextbox(main, fg_color=("#f2f2f7", "#000000"), text_color=("#000000", "#ffffff"),
                                            border_width=0, corner_radius=12, font=("Consolas", 13), height=200)
        self.admin_details.pack(fill="both", expand=True, padx=20, pady=10)
        self.admin_details.insert("0.0", "ℹ️ Thông tin phiên live sẽ hiển thị tại đây.")
        self.admin_details.configure(state="disabled")

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(footer, text="🔄 Tải lại", fg_color="#3b82f6", hover_color="#2563eb",
                      text_color="#fff", font=("Arial", 10, "bold"),
                      command=self.load_settings).pack(side="left", padx=5)
        
        ctk.CTkButton(footer, text="🗑 Cache", fg_color="#f59e0b", hover_color="#d97706",
                      text_color="#fff", font=("Arial", 10, "bold"),
                      command=self.clear_audio_cache).pack(side="left", padx=5)
        
        ctk.CTkButton(footer, text="↻ Reset", fg_color="#10b981", hover_color="#059669",
                      text_color="#fff", font=("Arial", 10, "bold"),
                      command=self.reset_statistics).pack(side="left", padx=5)

        self.update_admin_page()

    def create_stats_content(self, parent, icon):
        header = ctk.CTkFrame(parent, height=70, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="📊 Thống kê phiên Live",
                     text_color=("#000000", "#ffffff"), font=("Arial", 18, "bold")).pack(side="left", padx=15, pady=15)

        body = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        body.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        stat_frame = ctk.CTkFrame(body, fg_color="transparent", corner_radius=12)
        stat_frame.pack(fill="x", padx=20, pady=20)

        self.stats_labels = {}
        stat_items = ["Bình luận", "Quà tặng", "Vào phòng", "Lượt thích"]
        
        for label_text in stat_items:
            frame = ctk.CTkFrame(stat_frame, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=16, height=90)
            frame.pack(side="left", expand=True, fill="both", padx=8, pady=5)
            frame.pack_propagate(False)
            
            ctk.CTkLabel(frame, text=label_text, font=("Arial", 13, "bold"),
                         text_color=("#8e8e93", "#8e8e93")).pack(anchor="center", pady=(18, 5))
            
            self.stats_labels[label_text] = ctk.CTkLabel(frame, text="0", font=("Arial", 28, "bold"),
                                                          text_color=("#0a84ff", "#0a84ff"))
            self.stats_labels[label_text].pack(anchor="center", pady=(0, 10))

        self.stats_detail = ctk.CTkTextbox(body, fg_color=("#f2f2f7", "#000000"), text_color=("#000000", "#ffffff"),
                                           border_width=0, corner_radius=12, font=("Consolas", 13))
        self.stats_detail.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.stats_detail.insert("0.0", "🏆 Top tặng quà sẽ được cập nhật tự động.")
        self.stats_detail.configure(state="disabled")

        self.render_stats_page()

    def create_templates_content(self, parent, icon):
        header = ctk.CTkFrame(parent, height=70, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="📝 Văn bản tùy chỉnh",
                     text_color=("#000000", "#ffffff"), font=("Arial", 18, "bold")).pack(side="left", padx=15, pady=15)
                     
        ctk.CTkButton(header, text="💾 Lưu cài đặt", fg_color="#34c759", hover_color="#30d158",
                      text_color="#fff", width=140, corner_radius=15, font=("Arial", 12, "bold"),
                      command=self.save_settings).pack(side="right", padx=15, pady=15)

        body = ctk.CTkScrollableFrame(parent, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        body.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # --- Comment ---
        self._create_template_input(body, "Bình luận (Comment)", self.tpl_comment_var, "Ví dụ: {name} nói: {comment}\nCác biến hỗ trợ: {name}, {comment}")
        
        # --- Gift ---
        self._create_template_input(body, "Tặng quà (Gift)", self.tpl_gift_var, "Ví dụ: {name} tặng {gift}\nCác biến hỗ trợ: {name}, {gift}")
        
        # --- Join ---
        self._create_template_input(body, "Vào phòng (Join)", self.tpl_join_var, "Ví dụ: {name} đã vào phòng\nCác biến hỗ trợ: {name}")
        
        # --- Like ---
        self._create_template_input(body, "Lượt thích (Like)", self.tpl_like_var, "Ví dụ: {name} thả {count} tim\nCác biến hỗ trợ: {name}, {count}")

    def _create_template_input(self, parent, title, variable, hint):
        frame = ctk.CTkFrame(parent, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=12)
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame, text=title, font=("Arial", 14, "bold"), text_color=("#000", "#fff")).pack(anchor="w", padx=15, pady=(15, 5))
        
        entry = ctk.CTkEntry(frame, textvariable=variable, width=500, height=40, font=("Arial", 13), border_width=0, fg_color=("#ffffff", "#1c1c1e"))
        entry.pack(anchor="w", padx=15, pady=5)
        
        ctk.CTkLabel(frame, text=hint, font=("Arial", 11), text_color=("#666", "#aaa"), justify="left").pack(anchor="w", padx=15, pady=(0, 15))

    def register_live_event(self, event_type, data=None):
        if event_type == "comment":
            self.session_stats["comments"] += 1
        elif event_type == "gift":
            self.session_stats["gifts"] += 1
            self.session_stats["gift_history"].insert(0, f"{data['nickname']} tặng {data['gift']}")
            self.session_stats["gift_history"] = self.session_stats["gift_history"][0:100]
            self.session_stats["top_gifters"][data["nickname"]] = self.session_stats["top_gifters"].get(data["nickname"], 0) + 1
        elif event_type == "join":
            self.session_stats["joins"] += 1
        elif event_type == "like":
            self.session_stats["likes"] += data.get("count", 1)

        self.render_stats_page()
        self.render_gift_history()
        self.update_admin_page()

    def update_admin_page(self):
        if hasattr(self, "admin_status"):
            status_text = "Trạng thái: Đang kết nối" if self.is_connected else "Trạng thái: Offline"
            if getattr(self, "tiktok_manager", None) and self.tiktok_manager.connected_username:
                status_text += f" | @{self.tiktok_manager.connected_username}"
            self.admin_status.configure(text=status_text)

        if hasattr(self, "admin_details"):
            detail_text = (
                f"Tài khoản: @{self.tiktok_manager.connected_username}\n"
                f"Đã đọc: {self.session_stats['comments']} bình luận, {self.session_stats['gifts']} quà, "
                f"{self.session_stats['joins']} lượt vào, {self.session_stats['likes']} like\n"
                f"Tốc độ: {self.speed_var.get()}x | Âm lượng: {int(self.volume_var.get()*100)}%\n"
                f"Chế độ đọc: {self.read_mode_var.get()}\n"
                f"Blacklist: {len(dm.load_json(dm.BLACKLIST_FILE))} mục\n"
            )
            self.admin_details.configure(state="normal")
            self.admin_details.delete("1.0", "end")
            self.admin_details.insert("0.0", detail_text)
            self.admin_details.configure(state="disabled")

    def render_gift_history(self):
        if not hasattr(self, "gift_history_box"):
            return
        self.gift_history_box.configure(state="normal")
        self.gift_history_box.delete("1.0", "end")
        if self.session_stats["gift_history"]:
            for item in self.session_stats["gift_history"]:
                self.gift_history_box.insert("end", f"• {item}\n")
        else:
            self.gift_history_box.insert("end", "Chưa có quà tặng nào")
        self.gift_history_box.configure(state="disabled")

    def render_stats_page(self):
        if not hasattr(self, "stats_labels"):
            return
        self.stats_labels["Bình luận"].configure(text=str(self.session_stats["comments"]))
        self.stats_labels["Quà tặng"].configure(text=str(self.session_stats["gifts"]))
        self.stats_labels["Vào phòng"].configure(text=str(self.session_stats["joins"]))
        self.stats_labels["Lượt thích"].configure(text=str(self.session_stats["likes"]))

        if hasattr(self, "stats_detail"):
            top_gifters = sorted(self.session_stats["top_gifters"].items(), key=lambda x: x[1], reverse=True)[:5]
            details = "Top tặng quà:\n"
            if top_gifters:
                for name, count in top_gifters:
                    details += f" - {name}: {count} lần\n"
            else:
                details += " Chưa có người tặng quà nào\n"
            self.stats_detail.configure(state="normal")
            self.stats_detail.delete("1.0", "end")
            self.stats_detail.insert("end", details)
            self.stats_detail.configure(state="disabled")

    def clear_gift_history(self):
        self.session_stats["gift_history"] = []
        self.session_stats["top_gifters"] = {}
        self.session_stats["gifts"] = 0
        self.render_gift_history()
        self.render_stats_page()
        self.update_admin_page()

    def clear_audio_cache(self):
        try:
            for file_name in os.listdir(dm.CACHE_DIR):
                file_path = os.path.join(dm.CACHE_DIR, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.add_log("🗑️ Đã xóa cache TTS.")
        except Exception as e:
            self.add_log(f"❌ Xóa cache thất bại: {e}")

    def reset_statistics(self):
        self.session_stats = {"comments": 0, "gifts": 0, "joins": 0, "likes": 0, "gift_history": [], "top_gifters": {}}
        self.render_stats_page()
        self.render_gift_history()
        self.update_admin_page()

    # ==============================
    # GENERIC CONTENT
    # ==============================
    def create_generic_content(self, parent, title_text, icon, placeholder_text):
        icon_size = (20, 20)
        icon_path = os.path.join("data", "icon")

        try:
            img_gift  = ctk.CTkImage(Image.open(os.path.join(icon_path, "gift.ico")),    size=icon_size)
            img_key   = ctk.CTkImage(Image.open(os.path.join(icon_path, "keyword.ico")), size=icon_size)
            img_emoji = ctk.CTkImage(Image.open(os.path.join(icon_path, "emoji.ico")),   size=icon_size)
            img_trash = ctk.CTkImage(Image.open(os.path.join(icon_path, "trash.ico")),   size=icon_size)
        except Exception:
            img_gift = img_key = img_emoji = img_trash = None

        top_bar = ctk.CTkFrame(parent, height=65, fg_color=("#ffffff", "#1e1e1e"), corner_radius=10)
        top_bar.pack(fill="x", padx=15, pady=15)
        top_bar.pack_propagate(False)

        ctk.CTkButton(top_bar, text=" Quà tặng", image=img_gift, compound="left",
                      width=110, height=35,
                      fg_color=("#f0f0f0", "#2a2a2a"), text_color=("#000", "#fff"),
                      hover_color=("#e5e5e5", "#3a3a3a"),
                      command=lambda: self.open_modal("Quà tặng")).pack(side="left", padx=10, pady=12)

        ctk.CTkButton(top_bar, text=" Từ khóa", image=img_key, compound="left",
                      width=110, height=35,
                      fg_color=("#f0f0f0", "#2a2a2a"), text_color=("#000", "#fff"),
                      hover_color=("#e5e5e5", "#3a3a3a"),
                      command=lambda: self.open_modal("Từ khóa")).pack(side="left", padx=5, pady=12)

        ctk.CTkButton(top_bar, text=" Emoji", image=img_emoji, compound="left",
                      width=110, height=35,
                      fg_color=("#f0f0f0", "#2a2a2a"), text_color=("#000", "#fff"),
                      hover_color=("#e5e5e5", "#3a3a3a"),
                      command=lambda: self.open_modal("Emoji")).pack(side="left", padx=5, pady=12)

        btn_conn = ctk.CTkButton(top_bar, text="▶ Kết nối Live", width=120, height=35,
                                 fg_color=("#fe2c55", "#fe2c55"), hover_color=("#e11d48", "#e11d48"),
                                 text_color="#fff", command=self.toggle_connection)
        btn_conn.pack(side="right", padx=15, pady=12)
        self.connect_buttons.append(btn_conn)

        content_container = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1e1e1e"), corner_radius=15)
        content_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        header = ctk.CTkFrame(content_container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(header, text=title_text, image=icon, compound="left",
                     text_color=("#000", "#fff"),
                     font=("Arial", 16, "bold")).pack(side="left")

        display_box = ctk.CTkTextbox(
            content_container,
            fg_color=("#fcfcfc", "#121212"), text_color=("#000", "#fff"),
            border_width=1, border_color=("#eee", "#333"), corner_radius=8
        )
        display_box.pack(fill="both", expand=True, padx=20, pady=5)
        display_box.insert("0.0", placeholder_text)

        footer = ctk.CTkFrame(content_container, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(footer, text=" Xóa nhật ký", image=img_trash, compound="left",
                      fg_color=("#ef4444", "#dc2626"), text_color="#fff",
                      hover_color=("#dc2626", "#b91c1c"),
                      command=lambda: display_box.delete("1.0", "end")).pack(side="left", padx=5)

    # ==============================
    # BLACKLIST
    # ==============================
    def create_blacklist_content(self, parent, icon):
        icon_size = (20, 20)
        icon_path = os.path.join("data", "icon")

        try:
            img_gift  = ctk.CTkImage(Image.open(os.path.join(icon_path, "gift.ico")),    size=icon_size)
            img_key   = ctk.CTkImage(Image.open(os.path.join(icon_path, "keyword.ico")), size=icon_size)
            img_emoji = ctk.CTkImage(Image.open(os.path.join(icon_path, "emoji.ico")),   size=icon_size)
        except Exception:
            img_gift = img_key = img_emoji = None

        top_bar = ctk.CTkFrame(parent, height=110, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        top_bar.pack(fill="x", padx=15, pady=15)
        top_bar.pack_propagate(False)

        # Quick Actions Frame
        actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        ctk.CTkLabel(actions_frame, text="⚡ Hành động nhanh", font=("Arial", 11, "bold"),
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", pady=(0, 8))

        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")

        ctk.CTkButton(buttons_frame, text=" Quà tặng", image=img_gift, compound="left", width=100, height=50, corner_radius=14, fg_color="#fe2c55",
                      hover_color="#e11d48", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Quà tặng")).pack(side="left", padx=5)

        ctk.CTkButton(buttons_frame, text=" Từ khóa", image=img_key, compound="left", width=100, height=50, corner_radius=14, fg_color="#0a84ff",
                      hover_color="#007aff", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Từ khóa")).pack(side="left", padx=5)

        ctk.CTkButton(buttons_frame, text=" Emoji", image=img_emoji, compound="left", width=100, height=50, corner_radius=14, fg_color="#ff9f0a",
                      hover_color="#ff9500", text_color="#fff", font=("Arial", 14, "bold"),
                      command=lambda: self.open_modal("Emoji")).pack(side="left", padx=5)

        btn_conn = ctk.CTkButton(top_bar, text="▶ Kết nối Live", width=140, height=40, corner_radius=20,
                                 fg_color="#fe2c55", hover_color="#e11d48",
                                 text_color="#fff", font=("Arial", 13, "bold"),
                                 command=self.toggle_connection)
        btn_conn.pack(side="right", padx=15, pady=15)
        self.connect_buttons.append(btn_conn)

        main_container = ctk.CTkFrame(parent, fg_color=("#ffffff", "#1c1c1e"), corner_radius=20)
        main_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="🚫 Danh sách từ khóa đang chặn",
                     text_color=("#000000", "#ffffff"), font=("Arial", 18, "bold")).pack(side="left")

        self.blacklist_scroll = ctk.CTkScrollableFrame(main_container, fg_color=("#f2f2f7", "#000000"), 
                                                       corner_radius=14)
        self.blacklist_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # ✅ ĐÚNG
        footer_input = ctk.CTkFrame(main_container, fg_color="transparent", height=70)
        footer_input.pack(fill="x", padx=20, pady=15)
        footer_input.pack_propagate(False)

        self.new_ban_entry = ctk.CTkEntry(footer_input, placeholder_text="Nhập từ khóa mới muốn chặn...",
                                          width=400, height=40, border_width=0, corner_radius=12,
                                          fg_color=("#f2f2f7", "#2c2c2e"))
        self.new_ban_entry.pack(side="left", padx=15, pady=15)
        self.new_ban_entry.bind("<Return>", lambda e: self.add_blacklist_word())

        ctk.CTkButton(footer_input, text="➕ Thêm từ khóa", fg_color="#34c759", hover_color="#30d158",
                      width=140, height=40, corner_radius=12, font=("Arial", 12, "bold"),
                      text_color="#fff", command=self.add_blacklist_word).pack(side="left", padx=10, pady=15)

        self.render_blacklist()

    def render_blacklist(self):
        for widget in self.blacklist_scroll.winfo_children():
            widget.destroy()

        try:
            data = dm.load_json(dm.BLACKLIST_FILE)
            words = list(data.keys()) if isinstance(data, dict) else data
        except Exception:
            words = []

        if not words:
            empty_label = ctk.CTkLabel(self.blacklist_scroll, text="📭 Chưa có từ khóa nào bị chặn",
                                       font=("Arial", 13), text_color=("#999", "#666"))
            empty_label.pack(pady=20)
            return

        for word in words:
            row = ctk.CTkFrame(self.blacklist_scroll, fg_color=("#f8f8f8", "#2a2a2a"), 
                               corner_radius=8, height=45)
            row.pack(fill="x", pady=3, padx=3)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"🚫 {word}", font=("Arial", 12), 
                         text_color=("#333", "#ddd")).pack(side="left", padx=12, pady=10)
            
            ctk.CTkButton(row, text="✕", width=35, height=28,
                          fg_color="#ef4444", hover_color="#dc2626", text_color="#fff",
                          font=("Arial", 11, "bold"),
                          command=lambda w=word: self.delete_blacklist_word(w)).pack(side="right", padx=8, pady=8)

    def add_blacklist_word(self):
        word = self.new_ban_entry.get().strip()
        if word:
            data = dm.load_json(dm.BLACKLIST_FILE)
            if isinstance(data, list):
                if word not in data:
                    data.append(word)
            else:
                data[word] = word
            dm.save_json(dm.BLACKLIST_FILE, data)
            self.new_ban_entry.delete(0, "end")
            self.render_blacklist()

    def delete_blacklist_word(self, word):
        data = dm.load_json(dm.BLACKLIST_FILE)
        if isinstance(data, list) and word in data:
            data.remove(word)
        elif word in data:
            del data[word]
        dm.save_json(dm.BLACKLIST_FILE, data)
        self.render_blacklist()

    # ==============================
    # RIGHT SETTINGS PANEL
    # ==============================
    def setup_right_settings(self):
        icon_path = os.path.join("data", "icon")
        icon_size = (18, 18)

        try:
            img_setting = ctk.CTkImage(Image.open(os.path.join(icon_path, "setting.ico")), size=(20, 20))
            img_audio   = ctk.CTkImage(Image.open(os.path.join(icon_path, "audio.ico")),   size=icon_size)
            img_note    = ctk.CTkImage(Image.open(os.path.join(icon_path, "note.ico")),    size=icon_size)
            img_paint   = ctk.CTkImage(Image.open(os.path.join(icon_path, "paint.ico")),   size=icon_size)
        except Exception as e:
            print(f"Lỗi nạp icon settings: {e}")
            img_setting = img_audio = img_note = img_paint = None

        self.settings_frame = ctk.CTkScrollableFrame(self, width=320, corner_radius=0,
                                           fg_color=("#ffffff", "#1c1c1e"), border_width=0)
        self.settings_frame.grid(row=0, column=2, sticky="nsew")

        # Header
        header_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(25, 20))
        
        ctk.CTkLabel(header_frame, text=" Cài đặt TTS", image=img_setting, compound="left",
                     font=("Arial", 16, "bold")).pack(anchor="w")

        # --- Section 1: Event Switches ---
        section_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=16)
        section_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(section_frame, text="Sự kiện", font=("Arial", 12, "bold"), 
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", padx=15, pady=(12, 8))

        self.sw_comment = self.create_switch(" Đọc Comment", self.read_comment_var, section_frame)
        self.sw_gift    = self.create_switch(" Đọc Quà tặng", self.read_gift_var, section_frame)
        self.sw_join    = self.create_switch(" Đọc Người vào phòng", self.read_join_var, section_frame)
        self.sw_like    = self.create_switch(" Đọc Lượt thích", self.read_like_var, section_frame)

        # --- Section 2: Read Mode ---
        mode_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=16)
        mode_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(mode_frame, text="Chế độ đọc", font=("Arial", 12, "bold"),
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", padx=15, pady=(12, 8))

        self.read_mode = ctk.CTkOptionMenu(
            mode_frame,
            values=["Chỉ đọc nội dung CMT", "Đọc cả Tên + Nội dung"],
            variable=self.read_mode_var,
            width=280, fg_color="#fe2c55", button_color="#ff5577",
            command=lambda _: self.save_settings()
        )
        self.read_mode.set(self.read_mode_var.get())
        self.read_mode.pack(padx=15, pady=(0, 12), fill="x")

        # --- Section 3: Speed & Volume ---
        audio_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=16)
        audio_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(audio_frame, text="Âm thanh", font=("Arial", 12, "bold"),
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", padx=15, pady=(12, 8))

        # Speed
        speed_header = ctk.CTkFrame(audio_frame, fg_color="transparent")
        speed_header.pack(fill="x", padx=15, pady=(0, 3))
        
        ctk.CTkLabel(speed_header, text="🎙️ Tốc độ", font=("Arial", 11),
                     text_color=("#333", "#ccc")).pack(side="left")
        
        self.speed_label = ctk.CTkLabel(speed_header, text=f"{self.speed_var.get():.1f}x",
                     font=("Arial", 11, "bold"), text_color="#fe2c55")
        self.speed_label.pack(side="right")

        self.speed_slider = ctk.CTkSlider(
            audio_frame,
            from_=0.5, to=2.0,
            number_of_steps=15,
            variable=self.speed_var,
            progress_color="#fe2c55",
            command=self._on_speed_change
        )
        self.speed_slider.pack(fill="x", padx=15, pady=(0, 12))

        # Volume
        volume_header = ctk.CTkFrame(audio_frame, fg_color="transparent")
        volume_header.pack(fill="x", padx=15, pady=(0, 3))
        
        ctk.CTkLabel(volume_header, text="🔊 Âm lượng", font=("Arial", 11),
                     text_color=("#333", "#ccc")).pack(side="left")
        
        self.volume_label = ctk.CTkLabel(volume_header, text=f"{int(self.volume_var.get()*100)}%",
                     font=("Arial", 11, "bold"), text_color="#fe2c55")
        self.volume_label.pack(side="right")

        self.volume_slider = ctk.CTkSlider(
            audio_frame,
            from_=0.0, to=1.0,
            number_of_steps=20,
            variable=self.volume_var,
            progress_color="#fe2c55",
            command=self._on_volume_change
        )
        self.volume_slider.pack(fill="x", padx=15, pady=(0, 12))

        # --- Section 4: Theme ---
        theme_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#f2f2f7", "#2c2c2e"), corner_radius=16)
        theme_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(theme_frame, text="Giao diện", font=("Arial", 12, "bold"),
                     text_color=("#fe2c55", "#ff5577")).pack(anchor="w", padx=15, pady=(12, 8))

        self.theme_menu = ctk.CTkSegmentedButton(
            theme_frame, values=["Light", "Dark"],
            command=self.change_theme, selected_color="#fe2c55"
        )
        self.theme_menu.set(self.theme_var.get())
        self.theme_menu.pack(padx=15, pady=(0, 12), fill="x")
        
        # Footer spacer
        ctk.CTkLabel(self.settings_frame, text="").pack(pady=20)

    def _on_speed_change(self, value):
        speed = round(float(value), 1)
        self.speed_label.configure(text=f"{speed}x")
        if hasattr(self, 'tiktok_manager'):
            self.tiktok_manager.set_speed(speed)
        self.save_settings()

    def _on_volume_change(self, value):
        volume = max(0.0, min(1.0, float(value)))
        self.volume_label.configure(text=f"{int(volume * 100)}%")
        if hasattr(self, 'tiktok_manager'):
            self.tiktok_manager.set_volume(volume)
        self.save_settings()

    def create_switch(self, text, variable, parent=None):
        if parent is None:
            parent = self.settings_frame
        sw = ctk.CTkSwitch(parent, text=text, text_color=("#333", "#ccc"),
                           progress_color="#fe2c55", variable=variable,
                           command=self.save_settings)
        sw.pack(anchor="w", padx=15, pady=5)
        return sw

    def change_theme(self, theme):
        if theme == "Dark":
            ctk.set_appearance_mode("dark")
            self.settings_frame.configure(fg_color="#1c1c1e", border_color="#1c1c1e")
        else:
            ctk.set_appearance_mode("light")
            self.settings_frame.configure(fg_color="#ffffff", border_color="#ffffff")
        self.theme_var.set(theme)
        self.save_settings()

    def validate_username(self, username):
        username = username.strip().lstrip("@")
        if not username:
            return None
        if not re.match(r"^[A-Za-z0-9._]+$", username):
            return None
        return username

    def check_tiktok_account_exists(self, username):
        url = f"https://www.tiktok.com/@{username}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=10) as response:
                page = response.read(2048).decode("utf-8", errors="ignore")
                if "Page Not Found" in page or "Không tìm thấy trang" in page or response.status == 404:
                    return False
                return True
        except HTTPError as e:
            if e.code == 404:
                return False
            return None
        except URLError:
            return None
        except Exception:
            return None

    # ==============================
    # KẾT NỐI / NGẮT KẾT NỐI
    # ==============================
    def toggle_connection(self):
        if not self.is_connected:
            self.open_connect_popup()
        else:
            self.tiktok_manager.disconnect()
            self.is_connected = False
            self.update_ui_state()

    def open_connect_popup(self):
        if hasattr(self, "conn_popup") and self.conn_popup.winfo_exists():
            self.conn_popup.lift()
            return

        self.conn_popup = ctk.CTkToplevel(self)
        self.conn_popup.title("Kết nối TikTok Live")
        self.conn_popup.geometry("400x300")
        self.conn_popup.attributes("-topmost", True)
        self.conn_popup.resizable(False, False)

        icon_path = os.path.join("data", "icon", "connect.ico")
        try:
            self.conn_popup.after(200, lambda: self.conn_popup.iconbitmap(icon_path))
        except Exception:
            pass

        ctk.CTkLabel(self.conn_popup, text="Nhập ID TikTok Live",
                     font=("Arial", 16, "bold")).pack(pady=(30, 10))

        id_entry = ctk.CTkEntry(self.conn_popup, placeholder_text="@username...", width=260, height=38)
        id_entry.pack(pady=10)
        id_entry.focus_set()

        status_lbl = ctk.CTkLabel(self.conn_popup, text="", text_color="#999", font=("Arial", 11))
        status_lbl.pack(pady=5)

        def start_connect():
            username = id_entry.get().strip()
            username = self.validate_username(username)
            if not username:
                status_lbl.configure(text="⚠️ Username không hợp lệ!", text_color="#f59e0b")
                return

            status_lbl.configure(text=f"🔴 Kiểm tra @{username}...", text_color="#3b82f6")
            self.conn_popup.update()

            valid = self.check_tiktok_account_exists(username)
            if valid is False:
                status_lbl.configure(text="❌ Tài khoản không tồn tại hoặc bị chặn.", text_color="#dc2626")
                return
            elif valid is None:
                self.add_log("⚠️ Không thể kiểm tra trạng thái tài khoản, tiếp tục kết nối...")

            success = self.tiktok_manager.connect(username, self)
            if success:
                self.is_connected = True
                self.update_ui_state()
                self.conn_popup.destroy()
            else:
                status_lbl.configure(text="❌ Kết nối thất bại. Xem log để biết chi tiết.", text_color="#dc2626")

        btn_start = ctk.CTkButton(
            self.conn_popup, text="▶ Bắt đầu kết nối",
            fg_color="#fe2c55", hover_color="#e11d48",
            height=40, font=("Arial", 13, "bold"),
            command=start_connect
        )
        btn_start.pack(pady=20)

        id_entry.bind("<Return>", lambda e: start_connect())

    def update_ui_state(self):
        new_text  = "⏹ Ngắt kết nối" if self.is_connected else "▶ Kết nối Live"
        new_color = "#333333"          if self.is_connected else "#fe2c55"
        s_text    = "● Trực tuyến"    if self.is_connected else "● Offline"
        s_color   = "#2ecc71"         if self.is_connected else "#999"

        for btn in self.connect_buttons:
            btn.configure(text=new_text, fg_color=new_color)

        if hasattr(self, "status_label"):
            self.status_label.configure(text=s_text, text_color=s_color)

    def toggle_pause(self):
        if hasattr(self, "tiktok_manager"):
            paused = self.tiktok_manager.toggle_pause()
            self.add_log("⏸ TTS đang tạm dừng..." if paused else "▶ TTS tiếp tục hoạt động.")

    # ==============================
    # MODAL QUẢN LÝ DỮ LIỆU
    # ==============================
    def open_modal(self, title):
        if self.opened_modal is not None and self.opened_modal.winfo_exists():
            self.opened_modal.lift()
            self.opened_modal.focus_set()
            return

        modal = ctk.CTkToplevel(self)
        self.opened_modal = modal
        modal.title(f"Quản lý {title}")
        modal.geometry("520x620")
        modal.attributes("-topmost", True)

        icon_path  = os.path.join("data", "icon")
        modal_icon = None
        file_path  = ""

        try:
            if title == "Quà tặng":
                img_file  = "gift.ico"
                file_path = dm.GIFT_FILE
            elif title == "Từ khóa":
                img_file  = "keyword.ico"
                file_path = dm.ABBR_FILE
            else:
                img_file  = "emoji.ico"
                file_path = dm.EMOJI_FILE

            full_icon_path = os.path.join(icon_path, img_file)
            modal.after(200, lambda: modal.iconbitmap(full_icon_path))
            modal_icon = ctk.CTkImage(Image.open(full_icon_path), size=(26, 26))
        except Exception as e:
            print(f"Lỗi nạp icon modal: {e}")

        modal.after(10, lambda: modal.focus_force())

        def on_close():
            self.opened_modal = None
            modal.destroy()

        modal.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(modal, text=f"  Danh sách {title}", image=modal_icon, compound="left",
                     font=("Arial", 22, "bold")).pack(pady=(25, 20))

        current_data = dm.load_json(file_path)

        entry_frame = ctk.CTkFrame(modal, fg_color="transparent")
        entry_frame.pack(fill="x", padx=25)

        placeholder_key = "Tên quà (VD: Rose)" if title == "Quà tặng" else "Từ gốc"
        key_entry = ctk.CTkEntry(entry_frame, placeholder_text=placeholder_key, width=165, height=35)
        key_entry.pack(side="left", padx=5)

        val_entry = ctk.CTkEntry(entry_frame, placeholder_text="Lời đọc TTS", width=165, height=35)
        val_entry.pack(side="left", padx=5)

        list_frame = ctk.CTkScrollableFrame(modal, width=460, height=350, fg_color="#dadada")
        list_frame.pack(pady=20, padx=20, fill="both", expand=True)

        def render_list():
            for widget in list_frame.winfo_children():
                widget.destroy()
            for k, v in current_data.items():
                row = ctk.CTkFrame(list_frame, fg_color="#ffffff", corner_radius=6)
                row.pack(fill="x", pady=3, padx=5)
                ctk.CTkLabel(row, text=f"• {k}", font=("Arial", 12, "bold"),
                             width=130, anchor="w", text_color="#000").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=v, font=("Arial", 12), text_color="#333",
                             wraplength=180, justify="left").pack(side="left", padx=5)
                ctk.CTkButton(row, text="Xóa", width=50, height=26,
                              fg_color="#ef4444", hover_color="#dc2626",
                              command=lambda x=k: delete_item(x)).pack(side="right", padx=10)

        def add_item():
            k = key_entry.get().strip()
            v = val_entry.get().strip()
            if k and v:
                current_data[k] = v
                dm.save_json(file_path, current_data)
                key_entry.delete(0, "end")
                val_entry.delete(0, "end")
                render_list()

        def delete_item(key):
            if key in current_data:
                del current_data[key]
                dm.save_json(file_path, current_data)
                render_list()

        ctk.CTkButton(entry_frame, text="Thêm", width=75, height=35,
                      fg_color="#10b981", hover_color="#059669",
                      font=("Arial", 13, "bold"), command=add_item).pack(side="left", padx=5)

        render_list()

        ctk.CTkButton(modal, text="Lưu và Đóng",
                      fg_color="#fe2c55", hover_color="#e11d48",
                      height=42, font=("Arial", 14, "bold"),
                      command=on_close).pack(side="bottom", pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()