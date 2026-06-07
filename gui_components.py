import customtkinter as ctk

class SettingsColumn(ctk.CTkFrame):
    def __init__(self, parent, vars_dict):
        super().__init__(parent, width=300, corner_radius=15, fg_color="#ffffff")
        self.pack_propagate(False)
        
        ctk.CTkLabel(self, text="⚙️ Cài đặt TTS", font=("Arial", 18, "bold")).pack(pady=20, padx=25, anchor="w")
        
        # Switches
        ctk.CTkSwitch(self, text="Đọc Comment", variable=vars_dict['read_comment'], progress_color="#fe2c55").pack(anchor="w", padx=30, pady=8)
        ctk.CTkSwitch(self, text="Đọc Quà tặng", variable=vars_dict['read_gift'], progress_color="#fe2c55").pack(anchor="w", padx=30, pady=8)
        ctk.CTkSwitch(self, text="Đọc Vào phòng", variable=vars_dict['read_join'], progress_color="#fe2c55").pack(anchor="w", padx=30, pady=8)
        ctk.CTkSwitch(self, text="Đọc Lượt thích", variable=vars_dict['read_like'], progress_color="#fe2c55").pack(anchor="w", padx=30, pady=8)

        # Audio Section
        ctk.CTkLabel(self, text="🔊 Âm thanh", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(20, 10))
        ctk.CTkLabel(self, text="Tốc độ & Âm lượng", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=25)
        ctk.CTkSlider(self, from_=0, to=100, progress_color="#fe2c55").pack(fill="x", padx=25, pady=10)

class LogArea(ctk.CTkFrame):
    def __init__(self, parent, toggle_pause_func, clear_func, stop_tts_func):
        super().__init__(parent, fg_color="#ffffff", corner_radius=15)
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="📜 Nhật ký Live", font=("Arial", 16, "bold")).pack(side="left")
        
        self.txt = ctk.CTkTextbox(self, fg_color="#fcfcfc", border_width=1, corner_radius=10, font=("Consolas", 13))
        self.txt.pack(fill="both", expand=True, padx=20, pady=10)
        
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=15)
        self.btn_pause = ctk.CTkButton(footer, text="⏸ Pause TTS", fg_color="#fbbf24", text_color="#000", command=toggle_pause_func)
        self.btn_pause.pack(side="left", padx=5)
        ctk.CTkButton(footer, text="⏹ Dừng TTS", fg_color="#333", command=stop_tts_func).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🗑 Xóa log", fg_color="#ef4444", command=clear_func).pack(side="left", padx=5)