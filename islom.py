import customtkinter as ctk
import tkinter as tk
import serial
import threading
import time

# --- UI SOZLAMALARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# LUG'AT (Sizning original main.py dagi kabi)
LANG = {
    "EN": {
        "title": "LS XGT PLC - Universal Diagnostic Tool (Cnet)",
        "com_port": "COM Port:",
        "baudrate": "Baudrate:",
        "station": "Station:",
        "connect": "CONNECT",
        "disconnect": "DISCONNECT",
        "read_sec": "READ",
        "write_sec": "WRITE",
        "addr_ph": "Address (e.g., %MW100)",
        "val_ph": "Value (Hex, e.g., 0001)",
        "btn_read": "READ DATA",
        "btn_write": "WRITE DATA",
        "bcc_check": "Enable BCC (lowercase command)",
        "terminal": "LIVE TERMINAL (Request/Response & Errors)",
        "sys_conn": "SYSTEM: Successfully connected ->",
        "sys_disconn": "SYSTEM: Disconnected.",
        "err_cable": "ERROR: Check the cable! ->",
        "err_timeout": "[RES]  < ERROR: No response from PLC (Timeout)",
        "err_lost": "CONNECTION LOST: Port disconnected! Program saved from crash."
    },
    "KR": {
        "title": "LS XGT PLC - 범용 진단 프로그램 (Cnet)",
        "com_port": "통신 포트:",
        "baudrate": "통신 속도:",
        "station": "국번:",
        "connect": "연결",
        "disconnect": "연결 해제",
        "read_sec": "읽기",
        "write_sec": "쓰기",
        "addr_ph": "주소 (예: %MW100)",
        "val_ph": "값 (Hex, 예: 0001)",
        "btn_read": "데이터 읽기",
        "btn_write": "데이터 쓰기",
        "bcc_check": "BCC 활성화 (소문자 명령)",
        "terminal": "라이브 터미널 (요청/응답 및 오류)",
        "sys_conn": "시스템: 연결 성공 ->",
        "sys_disconn": "시스템: 연결이 해제되었습니다.",
        "err_cable": "오류: 케이블을 확인하세요! ->",
        "err_timeout": "[RES]  < 오류: PLC 응답 없음 (시간 초과)",
        "err_lost": "연결 끊김: 포트 통신 단절! 프로그램 충돌이 방지되었습니다."
    }
}

# ==========================================
# 1. TO'LIQ SANOAT VIRTUAL KLAVIATURASI
# ==========================================
class VirtualKeyboard(ctk.CTkToplevel):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.title("HMI Full Keyboard")
        self.geometry("950x350")
        self.attributes("-topmost", True)
        self.target_entry = target_entry

        self.is_shifted = False
        self.is_caps = False

        self.keys_normal = [
            ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'BACKSPACE'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
            ['CapsLock', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'ENTER'],
            ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'SHIFT'],
            ['COM', 'SPACE', 'CLEAR', 'CLOSE']
        ]
        
        self.keys_shift = [
            ['~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', 'BACKSPACE'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
            ['CapsLock', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', 'ENTER'],
            ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?', 'SHIFT'],
            ['COM', 'SPACE', 'CLEAR', 'CLOSE']
        ]

        self.btn_widgets = {}
        self.build_keyboard()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 475
        y = (self.winfo_screenheight() // 2) - 175 + 100
        self.geometry(f'+{x}+{y}')

    def get_current_char(self, r, c):
        norm = self.keys_normal[r][c]
        shft = self.keys_shift[r][c]
        if len(norm) > 1:
            return norm
        if norm.isalpha():
            use_upper = self.is_caps ^ self.is_shifted
            return shft if use_upper else norm
        else:
            return shft if self.is_shifted else norm

    def build_keyboard(self):
        for r_idx in range(len(self.keys_normal)):
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=3, fill="x", padx=5)
            for c_idx in range(len(self.keys_normal[r_idx])):
                key_text = self.get_current_char(r_idx, c_idx)
                btn_width = 45
                btn_color = ["#3B8ED0", "#1F6AA5"]
                hover_color = ["#36719F", "#144870"]

                if len(key_text) > 1:
                    btn_color = "#555"
                    hover_color = "#777"
                    if key_text in ['BACKSPACE', 'ENTER', 'SHIFT']:
                        btn_width = 90
                    elif key_text == 'CapsLock':
                        btn_width = 80
                    elif key_text in ['CLEAR', 'CLOSE', 'COM']:
                        btn_width = 80
                    elif key_text == 'SPACE':
                        btn_width = 400

                btn = ctk.CTkButton(
                    frame, text=key_text, width=btn_width, height=50,
                    font=("Arial", 16, "bold"), fg_color=btn_color, hover_color=hover_color,
                    command=lambda r=r_idx, c=c_idx: self.handle_key(r, c)
                )
                if key_text == 'SPACE':
                    btn.pack(side="left", padx=2, expand=True)
                else:
                    btn.pack(side="left", padx=2, expand=True, fill="both")
                self.btn_widgets[(r_idx, c_idx)] = btn

    def refresh_labels(self):
        for (r, c), btn in self.btn_widgets.items():
            char = self.get_current_char(r, c)
            btn.configure(text=char)
            if char == 'CapsLock':
                btn.configure(fg_color="#2FA572" if self.is_caps else "#555")
            elif char == 'SHIFT':
                btn.configure(fg_color="#2FA572" if self.is_shifted else "#555")

    def handle_key(self, r, c):
        key = self.get_current_char(r, c)
        if key == 'CLOSE' or key == 'ENTER':
            self.destroy()
        elif key == 'BACKSPACE':
            current = self.target_entry.get()
            self.target_entry.delete(0, 'end')
            self.target_entry.insert(0, current[:-1])
        elif key == 'CLEAR':
            self.target_entry.delete(0, 'end')
        elif key == 'SPACE':
            self.target_entry.insert('end', ' ')
        elif key == 'CapsLock':
            self.is_caps = not self.is_caps
            self.refresh_labels()
        elif key == 'SHIFT':
            self.is_shifted = not self.is_shifted
            self.refresh_labels()
        elif key == 'COM':
            self.target_entry.insert('end', 'COM')
        else:
            self.target_entry.insert('end', key)
            if self.is_shifted:
                self.is_shifted = False
                self.refresh_labels()

# ==========================================
# 2. VIZUALIZATSIYA
# ==========================================
class CraneTrackWidget(ctk.CTkFrame):
    def __init__(self, master, width=600, height=350, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        self.width = width
        self.height = height

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both", padx=10, pady=10)

        self.current_x = 150
        self.target_x = 150
        self.draw_static_rails()
        self.build_crane_assembly()

    def draw_static_rails(self):
        self.canvas.create_line(20, 30, self.width-20, 30, fill="#666666", width=2)
        self.canvas.create_line(20, self.height-30, self.width-20, self.height-30, fill="#666666", width=2)

    def build_crane_assembly(self):
        self.canvas.delete("crane_tag")
        x = self.current_x
        self.canvas.create_rectangle(
            x - 6, 35, x + 6, self.height-35,
            outline="#D49A00", fill="#FFC000", tags="crane_tag", width=2
        )

    def set_position(self, target_x):
        self.target_x = max(30, min(self.width - 30, target_x))
        self._animate()

    def _animate(self):
        if self.current_x == self.target_x:
            return
        step = 5
        direction = 1 if self.target_x > self.current_x else -1
        if abs(self.target_x - self.current_x) <= step:
            dx = self.target_x - self.current_x
            self.current_x = self.target_x
        else:
            dx = step * direction
            self.current_x += dx
        self.canvas.move("crane_tag", dx, 0)
        self.after(15, self._animate)

class ModernLED(ctk.CTkFrame):
    def __init__(self, master, text="LED", size=70, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.text = text
        self.state = False
        self.canvas = tk.Canvas(self, width=size, height=size+20, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack()
        self.draw_off()

    def draw_off(self):
        self.canvas.delete("all")
        cx = cy = self.size // 2
        self.canvas.create_oval(cx-5, cy-5, cx+self.size//2+5, cy+self.size//2+5, fill="#1a1a1a", outline="")
        self.canvas.create_oval(cx-self.size//2+5, cy-self.size//2+5, cx+self.size//2-5, cy+self.size//2-5, fill="#3a3a3a", outline="#888", width=2)
        self.canvas.create_oval(cx-12, cy-12, cx+12, cy+12, fill="#555", outline="#666", width=1)
        self.canvas.create_text(cx, cy+30, text=self.text, fill="white", font=("Arial", 10, "bold"))

    def draw_on(self):
        self.canvas.delete("all")
        cx = cy = self.size // 2
        self.canvas.create_oval(cx-5, cy-5, cx+self.size//2+5, cy+self.size//2+5, fill="#1a1a1a", outline="")
        self.canvas.create_oval(cx-self.size//2+5, cy-self.size//2+5, cx+self.size//2-5, cy+self.size//2-5, fill="#3a3a3a", outline="#888", width=2)
        for i in range(10, 0, -1):
            alpha = int(255 * (0.3 + 0.7 * (i/10)))
            color = f"#{alpha:02x}ff{alpha:02x}"
            self.canvas.create_oval(cx-i+5, cy-i+5, cx+i-5, cy+i-5, fill=color, outline="")
        self.canvas.create_text(cx, cy+30, text=self.text, fill="white", font=("Arial", 10, "bold"))

    def set_state(self, on):
        if on != self.state:
            self.state = on
            if on: self.draw_on()
            else: self.draw_off()

class ModernAngleMeter(ctk.CTkFrame):
    def __init__(self, master, title="LEFT", txt_left="OUT", txt_right="IN", width=220, height=180, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.width = width
        self.height = height
        self.title_text = title
        self.txt_left = txt_left
        self.txt_right = txt_right
        self.angle = 0

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(expand=True, pady=10)
        self.draw_fixture()

    def draw_fixture(self):
        self.canvas.delete("all")
        cx = self.width // 2
        self.canvas.create_text(cx - 70, 30, text=self.txt_left, fill="#666666", font=("Arial", 12, "bold"))
        self.canvas.create_text(cx + 70, 30, text=self.txt_right, fill="#666666", font=("Arial", 12, "bold"))
        self.canvas.create_rectangle(cx - 35, 5, cx + 35, 25, fill="#0078D7", outline="")
        self.canvas.create_text(cx, 15, text=self.title_text, fill="white", font=("Arial", 11, "bold"))
        self.canvas.create_rectangle(cx - 35, 25, cx + 35, 45, fill="#999999", outline="")
        self.angle_text_id = self.canvas.create_text(cx, 35, text=f"{self.angle}°", fill="black", font=("Arial", 12, "bold"))
        self.canvas.create_rectangle(0, 55, self.width, 70, fill="#ECA400", outline="#B87300", width=2)
        self.canvas.create_rectangle(cx - 45, 45, cx + 45, 60, fill="#C0C0C0", outline="#888")
        self.canvas.create_rectangle(cx - 4, 70, cx + 4, 110, fill="#888888", outline="#555")
        self.canvas.create_polygon(cx - 50, 120, cx + 50, 120, cx + 40, 110, cx - 40, 110, fill="#A0A0A0", outline="#666")
        self.canvas.create_rectangle(cx - 65, 120, cx + 65, 135, fill="#222222", outline="#444")
        self.canvas.create_rectangle(cx - 55, 135, cx - 25, 140, fill="#FFFFCC", outline="")
        self.canvas.create_rectangle(cx - 15, 135, cx + 15, 140, fill="#FFFFCC", outline="")
        self.canvas.create_rectangle(cx + 25, 135, cx + 55, 140, fill="#FFFFCC", outline="")

    def set_angle(self, angle):
        self.angle = angle % 360
        self.canvas.itemconfig(self.angle_text_id, text=f"{self.angle}°")

# ==========================================
# 3. ASOSIY DASTUR
# ==========================================
class PLCTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "EN"
        self.title(LANG[self.current_lang]["title"])
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.destroy())

        self.serial_port = None
        self.kb_window = None

        # Manzillar
        self.led_addr = ctk.StringVar(value="%MW200")
        self.crane_addr = ctk.StringVar(value="%MW210")
        self.angle_addr_left = ctk.StringVar(value="%MW220")
        self.angle_addr_right = ctk.StringVar(value="%MW222")

        self.setup_ui()
        self.update_texts()

    def open_keyboard(self, event, entry_widget):
        if self.kb_window and self.kb_window.winfo_exists():
            self.kb_window.destroy()
        self.kb_window = VirtualKeyboard(self, entry_widget)

    def change_language(self, choice):
        self.current_lang = choice
        self.update_texts()

    def update_texts(self):
        """Asl main.py dagi tilni o'zgartirish tizimi tiklandi"""
        lang = LANG[self.current_lang]
        self.title(lang["title"])
        self.lbl_port.configure(text=lang["com_port"])
        self.lbl_baud.configure(text=lang["baudrate"])
        self.lbl_station.configure(text=lang["station"])
        self.lbl_read_sec.configure(text=lang["read_sec"])
        self.lbl_write_sec.configure(text=lang["write_sec"])
        self.read_addr.configure(placeholder_text=lang["addr_ph"])
        self.write_addr.configure(placeholder_text=lang["addr_ph"])
        self.write_val.configure(placeholder_text=lang["val_ph"])
        self.read_btn.configure(text=lang["btn_read"])
        self.write_btn.configure(text=lang["btn_write"])
        self.bcc_check.configure(text=lang["bcc_check"])
        self.lbl_terminal.configure(text=lang["terminal"])
        
        if self.serial_port and self.serial_port.is_open:
            self.connect_btn.configure(text=lang["disconnect"])
        else:
            self.connect_btn.configure(text=lang["connect"])

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # 4-qator (Terminal) bo'sh joyni oladi

        # --- Tepadagi Tillar paneli ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.lang_switch = ctk.CTkSegmentedButton(self.frame_top, values=["EN", "KR"], command=self.change_language)
        self.lang_switch.set("EN")
        self.lang_switch.pack(side="right")

        # ----- 1-qator: Ulanish sozlamalari -----
        conn_frame = ctk.CTkFrame(self)
        conn_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        conn_frame.grid_columnconfigure((0,1,2,3,4), weight=1)

        self.lbl_port = ctk.CTkLabel(conn_frame, font=("Arial", 12, "bold"))
        self.lbl_port.grid(row=0, column=0, padx=5, sticky="w")
        self.port_entry = ctk.CTkEntry(conn_frame, width=100)
        self.port_entry.insert(0, "COM10")
        self.port_entry.grid(row=0, column=1, padx=5)
        self.port_entry.bind("<Button-1>", lambda e: self.open_keyboard(e, self.port_entry))

        self.lbl_baud = ctk.CTkLabel(conn_frame, font=("Arial", 12, "bold"))
        self.lbl_baud.grid(row=0, column=2, padx=5, sticky="w")
        self.baud_entry = ctk.CTkEntry(conn_frame, width=100)
        self.baud_entry.insert(0, "115200")
        self.baud_entry.grid(row=0, column=3, padx=5)
        self.baud_entry.bind("<Button-1>", lambda e: self.open_keyboard(e, self.baud_entry))

        self.lbl_station = ctk.CTkLabel(conn_frame, font=("Arial", 12, "bold"))
        self.lbl_station.grid(row=1, column=0, padx=5, sticky="w")
        self.station_entry = ctk.CTkEntry(conn_frame, width=50)
        self.station_entry.insert(0, "00")
        self.station_entry.grid(row=1, column=1, padx=5, sticky="w")
        self.station_entry.bind("<Button-1>", lambda e: self.open_keyboard(e, self.station_entry))

        self.bcc_var = ctk.BooleanVar(value=True)
        self.bcc_check = ctk.CTkCheckBox(conn_frame, variable=self.bcc_var)
        self.bcc_check.grid(row=1, column=2, columnspan=2, padx=5, sticky="w")

        self.connect_btn = ctk.CTkButton(conn_frame, fg_color="green", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, rowspan=2, padx=10, pady=5, sticky="e")

        # ----- 2-qator: O‘qish/Yozish -----
        rw_frame = ctk.CTkFrame(self)
        rw_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        rw_frame.grid_columnconfigure((1, 2), weight=1) 

        self.lbl_read_sec = ctk.CTkLabel(rw_frame, font=("Arial", 14, "bold"))
        self.lbl_read_sec.grid(row=0, column=0, padx=5, sticky="w")
        self.read_addr = ctk.CTkEntry(rw_frame, width=200)
        self.read_addr.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.read_addr.bind("<Button-1>", lambda e: self.open_keyboard(e, self.read_addr))
        self.read_btn = ctk.CTkButton(rw_frame, command=self.read_data, width=120)
        self.read_btn.grid(row=0, column=2, padx=5, pady=5)

        self.lbl_write_sec = ctk.CTkLabel(rw_frame, font=("Arial", 14, "bold"))
        self.lbl_write_sec.grid(row=1, column=0, padx=5, pady=(10,0), sticky="w")
        self.write_addr = ctk.CTkEntry(rw_frame, width=120)
        self.write_addr.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.write_addr.bind("<Button-1>", lambda e: self.open_keyboard(e, self.write_addr))
        
        self.write_val = ctk.CTkEntry(rw_frame, width=120)
        self.write_val.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.write_val.bind("<Button-1>", lambda e: self.open_keyboard(e, self.write_val))
        
        self.write_btn = ctk.CTkButton(rw_frame, fg_color="#C8504B", command=self.write_data, width=120)
        self.write_btn.grid(row=1, column=3, padx=5, pady=5)

        # ----- 3-qator: Animatsiya manzillari -----
        addr_frame = ctk.CTkFrame(self)
        addr_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        addr_frame.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1)

        ctk.CTkLabel(addr_frame, text="LED word:", font=("Arial", 11)).grid(row=0, column=0, padx=2, sticky="w")
        self.entry_led = ctk.CTkEntry(addr_frame, textvariable=self.led_addr, width=80)
        self.entry_led.grid(row=0, column=1, padx=2)
        self.entry_led.bind("<Button-1>", lambda e: self.open_keyboard(e, self.entry_led))

        ctk.CTkLabel(addr_frame, text="Kran X:", font=("Arial", 11)).grid(row=0, column=2, padx=2, sticky="w")
        self.entry_crane = ctk.CTkEntry(addr_frame, textvariable=self.crane_addr, width=80)
        self.entry_crane.grid(row=0, column=3, padx=2)
        self.entry_crane.bind("<Button-1>", lambda e: self.open_keyboard(e, self.entry_crane))

        ctk.CTkLabel(addr_frame, text="L-Angle:", font=("Arial", 11)).grid(row=0, column=4, padx=2, sticky="w")
        self.entry_angle_left = ctk.CTkEntry(addr_frame, textvariable=self.angle_addr_left, width=80)
        self.entry_angle_left.grid(row=0, column=5, padx=2)
        self.entry_angle_left.bind("<Button-1>", lambda e: self.open_keyboard(e, self.entry_angle_left))
        
        ctk.CTkLabel(addr_frame, text="R-Angle:", font=("Arial", 11)).grid(row=0, column=6, padx=2, sticky="w")
        self.entry_angle_right = ctk.CTkEntry(addr_frame, textvariable=self.angle_addr_right, width=80)
        self.entry_angle_right.grid(row=0, column=7, padx=2)
        self.entry_angle_right.bind("<Button-1>", lambda e: self.open_keyboard(e, self.entry_angle_right))

        # ----- 4-qator: Terminal -----
        term_frame = ctk.CTkFrame(self)
        term_frame.grid(row=4, column=0, padx=20, pady=5, sticky="nsew")
        self.lbl_terminal = ctk.CTkLabel(term_frame, font=("Arial", 12, "bold"))
        self.lbl_terminal.pack(anchor="w", padx=5, pady=2)
        self.textbox_log = ctk.CTkTextbox(term_frame, font=("Consolas", 11), text_color="#00FF00", fg_color="black")
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=5)

        # ----- 5-qator: Animatsiyalar -----
        anim_frame = ctk.CTkFrame(self)
        anim_frame.grid(row=5, column=0, padx=20, pady=(5,10), sticky="sew")
        anim_frame.grid_columnconfigure((0,1,2), weight=1)
        anim_frame.grid_rowconfigure(0, weight=1)

        # LED panel
        led_panel = ctk.CTkFrame(anim_frame)
        led_panel.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(led_panel, text="LED INDICATORS", font=("Arial", 14, "bold")).pack(pady=5)
        led_inner = ctk.CTkFrame(led_panel, fg_color="transparent")
        led_inner.pack(expand=True)
        self.left_led = ModernLED(led_inner, text="LEFT", size=70)
        self.left_led.pack(side="left", padx=10, pady=10)
        self.right_led = ModernLED(led_inner, text="RIGHT", size=70)
        self.right_led.pack(side="right", padx=10, pady=10)

        # Kran panel
        crane_panel = ctk.CTkFrame(anim_frame)
        crane_panel.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(crane_panel, text="CRANE MOVEMENT", font=("Arial", 14, "bold")).pack(pady=5)
        self.crane = CraneTrackWidget(crane_panel, width=500, height=220)
        self.crane.pack(expand=True, pady=10)

        # Burchak panel
        angle_panel = ctk.CTkFrame(anim_frame)
        angle_panel.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(angle_panel, text="ANGLE METERS", font=("Arial", 14, "bold")).pack(pady=5)
        
        angle_inner = ctk.CTkFrame(angle_panel, fg_color="transparent")
        angle_inner.pack(expand=True)

        self.angle_meter_left = ModernAngleMeter(angle_inner, title="LEFT", txt_left="OUT", txt_right="IN", width=220)
        self.angle_meter_left.pack(side="left", padx=10, pady=10)

        self.angle_meter_right = ModernAngleMeter(angle_inner, title="RIGHT", txt_left="IN", txt_right="OUT", width=220)
        self.angle_meter_right.pack(side="left", padx=10, pady=10)

    # ---------- Original main.py arxitekturasi tiklandi ----------
    def calculate_bcc(self, frame_bytes):
        total = sum(frame_bytes) & 0xFF
        return f"{total:02X}"

    def build_xgt_frame(self, cmd_base, address, data_hex="", use_bcc=True):
        try:
            station = int(self.station_entry.get())
            if station < 0 or station > 31: station = 0
        except: station = 0
            
        station_str = f"{station:02d}" # Original main.py da 02d edi
        cmd_letter = cmd_base.lower() if use_bcc else cmd_base.upper()
        cmd_type = "SS"
        block_count = "01"
        var_len = f"{len(address):02d}"

        ENQ, EOT = b'\x05', b'\x04'

        parts = [
            ENQ, station_str.encode('ascii'), cmd_letter.encode('ascii'),
            cmd_type.encode('ascii'), block_count.encode('ascii'),
            var_len.encode('ascii'), address.encode('ascii')
        ]
        if cmd_base == 'w' and data_hex:
            parts.append(data_hex.encode('ascii'))
        parts.append(EOT)

        frame_without_bcc = b''.join(parts)
        if use_bcc:
            bcc = self.calculate_bcc(frame_without_bcc).encode('ascii')
            return frame_without_bcc + bcc
        return frame_without_bcc

    def toggle_connection(self):
        lang = LANG[self.current_lang]
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.connect_btn.configure(text=lang["connect"], fg_color="green")
            self.log_message(lang["sys_disconn"], "yellow")
        else:
            try:
                port = self.port_entry.get()
                baud = int(self.baud_entry.get())
                self.serial_port = serial.Serial(port, baudrate=baud, timeout=1.5)
                self.connect_btn.configure(text=lang["disconnect"], fg_color="red")
                self.log_message(f"{lang['sys_conn']} {port} ({baud} bps)", "green")
            except Exception as e:
                self.log_message(f"{lang['err_cable']} {e}", "red")

    def bytes_to_display(self, data):
        result = []
        for b in data:
            if b == 0x05: result.append('[ENQ]')
            elif b == 0x06: result.append('[ACK]')
            elif b == 0x15: result.append('[NAK]')
            elif b == 0x04: result.append('[EOT]')
            elif b == 0x03: result.append('[ETX]')
            elif 32 <= b <= 126: result.append(chr(b))
            else: result.append(f'[{b:02X}]')
        return ''.join(result)

    def get_error_description(self, error_code):
        errors = {
            "0003": "Block count exceeds 16", "0004": "Variable length > 12",
            "0007": "Invalid data type", "0011": "Data error / invalid variable",
            "0090": "Monitor not registered", "0190": "Monitor number out of range",
            "0290": "Monitor registration number out of range", "1132": "Invalid device memory",
            "1232": "Data size > max (60 words)", "1234": "Extra frame data",
            "1332": "Data type mismatch in blocks", "1432": "Invalid hex data",
            "7132": "Variable area exceeded"
        }
        return errors.get(error_code, "Unknown error")

    # Original send_to_plc mantiqi (animatsiyaga callback qilish bilan birga)
    def send_to_plc(self, frame, cmd, address, value="", callback=None):
        lang = LANG[self.current_lang]
        if not self.serial_port or not self.serial_port.is_open:
            return

        try:
            self.log_message(f"[ASK]  > {self.bytes_to_display(frame)}", "cyan")
            self.serial_port.write(frame)
            time.sleep(0.1)

            use_bcc = self.bcc_var.get()
            response = bytearray()
            
            while True:
                ch = self.serial_port.read(1)
                if not ch: break
                response.extend(ch)
                if ch == b'\x03': break

            if not response:
                self.log_message(f"[RES]  < {address} -> " + lang["err_timeout"], "red")
                return

            if use_bcc:
                self.serial_port.timeout = 0.2
                bcc_bytes = self.serial_port.read(2)
                self.serial_port.timeout = 1.5
                if len(bcc_bytes) == 2:
                    response.extend(bcc_bytes)
                    has_bcc = True
                else: has_bcc = False
            else: has_bcc = False

            self.log_message(f"[RES]  < {self.bytes_to_display(response)}", "white")

            if len(response) < 1: return
            first_byte = response[0]

            if first_byte == 0x06: # ACK
                if cmd == "r":
                    min_len = 13 if not has_bcc else 15
                    if len(response) < min_len:
                        self.log_message("[RES]  < Response too short for read", "red")
                        return

                    try:
                        data_cnt_ascii = response[8:10].decode('ascii')
                        data_bytes = int(data_cnt_ascii, 16)
                    except: data_bytes = 0

                    data_start = 10
                    data_end = data_start + data_bytes * 2
                    etx_pos = len(response) - 3 if has_bcc else len(response) - 1

                    if data_end > etx_pos:
                        self.log_message("[RES]  < Data length mismatch", "red")
                        return

                    data_ascii = response[data_start:data_end].decode('ascii')
                    self.log_message(f"[RES]  < {address} = {data_ascii} -> SUCCESS ✅", "green")
                    
                    # Animatsiya uchun Callback chaqiramiz
                    if callback:
                        try:
                            val_int = int(data_ascii, 16)
                            self.after(0, callback, val_int, address)
                        except: pass

                elif cmd == "w":
                    min_len = 7 if not has_bcc else 9
                    if len(response) < min_len:
                        self.log_message("[RES]  < Response too short for write", "red")
                        return

                    if response[6] == 0x03:
                        self.log_message(f"[RES]  < {address} <- {value} -> WRITE SUCCESS ✅", "green")
                    else:
                        self.log_message("[RES]  < Unexpected write response format", "red")

            elif first_byte == 0x15: # NAK
                error_start = 1 + 2 + 1 + 2
                etx_pos = response.find(b'\x03', error_start)

                if etx_pos > error_start:
                    error_ascii = response[error_start:etx_pos].decode('ascii')
                    desc = self.get_error_description(error_ascii)
                    self.log_message(f"[RES]  < {address} -> ERROR (NAK) code: {error_ascii} ({desc}) ❌", "red")
                else:
                    self.log_message(f"[RES]  < {address} -> ERROR (NAK) ❌", "red")
            else:
                self.log_message("[RES]  < Unknown response (no ACK/NAK)", "red")

        except serial.SerialException:
            self.log_message(lang["err_lost"], "red")
            self.toggle_connection()

    def read_data(self):
        addr = self.read_addr.get().strip()
        if addr:
            use_bcc = self.bcc_var.get()
            frame = self.build_xgt_frame("r", addr, use_bcc=use_bcc)
            threading.Thread(target=self.send_to_plc, args=(frame, "r", addr, "", self.update_by_address)).start()

    def write_data(self):
        addr = self.write_addr.get().strip()
        val = self.write_val.get().strip()
        if addr and val:
            if len(val) % 2 != 0:
                val = '0' + val
            use_bcc = self.bcc_var.get()
            frame = self.build_xgt_frame("w", addr, val, use_bcc=use_bcc)
            threading.Thread(target=self.send_to_plc, args=(frame, "w", addr, val)).start()

    def update_by_address(self, value, addr):
        if addr == self.led_addr.get(): self.update_leds(value)
        elif addr == self.crane_addr.get(): self.update_crane(value)
        elif addr == self.angle_addr_left.get(): self.update_angle_left(value)
        elif addr == self.angle_addr_right.get(): self.update_angle_right(value)

    def update_leds(self, value):
        self.left_led.set_state(bool(value & 1))
        self.right_led.set_state(bool(value & 2))

    def update_crane(self, value):
        min_x = 30
        max_x = 500 - 30
        target_x = min_x + (value / 1000) * (max_x - min_x)
        self.crane.set_position(int(target_x))

    def update_angle_left(self, value):
        self.angle_meter_left.set_angle(value)
        
    def update_angle_right(self, value):
        self.angle_meter_right.set_angle(value)

    def log_message(self, message, color="white"):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

if __name__ == "__main__":
    app = PLCTesterApp()
    app.mainloop()