import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import time
import datetime
import re
import json
import os
import queue

# --- DASTUR MA'LUMOTLARI ---
APP_VERSION = "2.0.0"
APP_NAME = "LS XGT PLC - Universal Diagnostic Tool"

# --- KONFIGURATSIYA FAYLI ---
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".plc_diagnostic_config.json")

# --- LOG PAPKASI ---
LOG_DIR = os.path.join(os.path.expanduser("~"), "PLC_Diagnostic_Logs")

# --- UI SOZLAMALARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- QUVVATLANGAN BAUDRATE LAR ---
SUPPORTED_BAUDRATES = ["9600", "19200", "38400", "57600", "115200"]

# --- MA'LUMOT TURLARI ---
DATA_TYPES = {
    "HEX": {"label": "HEX", "description": "Raw hexadecimal"},
    "UINT": {"label": "UINT16", "description": "Unsigned Integer (0-65535)"},
    "INT": {"label": "INT16", "description": "Signed Integer (-32768 to 32767)"},
    "BOOL": {"label": "BOOL", "description": "Boolean (0 or 1)"},
    "DWORD": {"label": "DWORD", "description": "Double Word (32-bit)"},
}

# --- LUG'AT (DICTIONARY) ---
LANG = {
    "EN": {
        "title": f"{APP_NAME} (Cnet) v{APP_VERSION}",
        "com_port": "COM Port:",
        "baudrate": "Baudrate:",
        "station": "Station:",
        "connect": "CONNECT",
        "disconnect": "DISCONNECT",
        "read_sec": "READ (RSS)",
        "write_sec": "WRITE (WSS)",
        "addr_ph": "Address (e.g., %MW100)",
        "val_ph": "Value",
        "btn_read": "READ DATA",
        "btn_write": "WRITE DATA",
        "terminal": "LIVE TERMINAL (Request/Response & Errors)",
        "sys_conn": "SYSTEM: Successfully connected ->",
        "sys_disconn": "SYSTEM: Disconnected.",
        "err_cable": "ERROR: Check the cable! ->",
        "err_timeout": "ERROR: No response from PLC (Timeout)",
        "err_lost": "CONNECTION LOST: Port disconnected! Program saved from crash.",
        "err_invalid_baud": "ERROR: Invalid baudrate value.",
        "err_invalid_addr": "ERROR: Invalid address format. Use %MW, %DW, %MB, etc.",
        "err_invalid_hex": "ERROR: Invalid hex value.",
        "err_not_connected": "ERROR: Not connected to PLC.",
        "err_empty_addr": "ERROR: Address field is empty.",
        "err_empty_val": "ERROR: Value field is empty.",
        "status_connected": "Connected",
        "status_disconnected": "Disconnected",
        "data_type": "Data Type:",
        "monitoring": "Monitor",
        "mon_start": "START MONITOR",
        "mon_stop": "STOP MONITOR",
        "mon_interval": "Interval (ms):",
        "clear_log": "CLEAR LOG",
        "scan_ports": "Scan Ports",
        "about": "About",
        "about_text": f"{APP_NAME}\nVersion: {APP_VERSION}\nProtocol: LS XGT Cnet\nDeveloper: PLC Diagnostics Team",
        "err_nak": "ERROR: NAK response from PLC. Error code: ",
        "write_confirm": "Write confirmed",
        "read_result": "Read result",
    },
    "UZ": {
        "title": f"{APP_NAME} (Cnet) v{APP_VERSION}",
        "com_port": "COM Port:",
        "baudrate": "Tezlik:",
        "station": "Stansiya:",
        "connect": "ULASH",
        "disconnect": "UZISH",
        "read_sec": "O'QISH (RSS)",
        "write_sec": "YOZISH (WSS)",
        "addr_ph": "Manzil (masalan, %MW100)",
        "val_ph": "Qiymat",
        "btn_read": "MA'LUMOT O'QISH",
        "btn_write": "MA'LUMOT YOZISH",
        "terminal": "TERMINAL (So'rov/Javob va Xatoliklar)",
        "sys_conn": "TIZIM: Muvaffaqiyatli ulandi ->",
        "sys_disconn": "TIZIM: Uzildi.",
        "err_cable": "XATO: Kabelni tekshiring! ->",
        "err_timeout": "XATO: PLCdan javob yo'q (Timeout)",
        "err_lost": "ALOQA UZILDI: Port uzildi! Dastur himoyalandi.",
        "err_invalid_baud": "XATO: Noto'g'ri baudrate qiymati.",
        "err_invalid_addr": "XATO: Noto'g'ri manzil formati. %MW, %DW, %MB va h.k. ishlating.",
        "err_invalid_hex": "XATO: Noto'g'ri hex qiymat.",
        "err_not_connected": "XATO: PLCga ulanmagan.",
        "err_empty_addr": "XATO: Manzil maydoni bo'sh.",
        "err_empty_val": "XATO: Qiymat maydoni bo'sh.",
        "status_connected": "Ulangan",
        "status_disconnected": "Ulanmagan",
        "data_type": "Ma'lumot turi:",
        "monitoring": "Monitoring",
        "mon_start": "MONITORNI BOSHLASH",
        "mon_stop": "MONITORNI TO'XTATISH",
        "mon_interval": "Interval (ms):",
        "clear_log": "LOGNI TOZALASH",
        "scan_ports": "Portlarni topish",
        "about": "Haqida",
        "about_text": f"{APP_NAME}\nVersiya: {APP_VERSION}\nProtokol: LS XGT Cnet\nIshlab chiquvchi: PLC Diagnostics Team",
        "err_nak": "XATO: PLCdan NAK javob. Xato kodi: ",
        "write_confirm": "Yozish tasdiqlandi",
        "read_result": "O'qish natijasi",
    },
    "KR": {
        "title": f"LS XGT PLC - 범용 진단 프로그램 (Cnet) v{APP_VERSION}",
        "com_port": "통신 포트:",
        "baudrate": "통신 속도:",
        "station": "국번:",
        "connect": "연결",
        "disconnect": "연결 해제",
        "read_sec": "읽기 (RSS)",
        "write_sec": "쓰기 (WSS)",
        "addr_ph": "주소 (예: %MW100)",
        "val_ph": "값",
        "btn_read": "데이터 읽기",
        "btn_write": "데이터 쓰기",
        "terminal": "라이브 터미널 (요청/응답 및 오류)",
        "sys_conn": "시스템: 연결 성공 ->",
        "sys_disconn": "시스템: 연결이 해제되었습니다.",
        "err_cable": "오류: 케이블을 확인하세요! ->",
        "err_timeout": "오류: PLC 응답 없음 (시간 초과)",
        "err_lost": "연결 끊김: 포트 통신 단절! 프로그램 충돌이 방지되었습니다.",
        "err_invalid_baud": "오류: 잘못된 통신 속도 값.",
        "err_invalid_addr": "오류: 잘못된 주소 형식. %MW, %DW, %MB 등을 사용하세요.",
        "err_invalid_hex": "오류: 잘못된 16진수 값.",
        "err_not_connected": "오류: PLC에 연결되지 않았습니다.",
        "err_empty_addr": "오류: 주소 필드가 비어 있습니다.",
        "err_empty_val": "오류: 값 필드가 비어 있습니다.",
        "status_connected": "연결됨",
        "status_disconnected": "연결 안 됨",
        "data_type": "데이터 유형:",
        "monitoring": "모니터링",
        "mon_start": "모니터링 시작",
        "mon_stop": "모니터링 중지",
        "mon_interval": "간격 (ms):",
        "clear_log": "로그 지우기",
        "scan_ports": "포트 스캔",
        "about": "정보",
        "about_text": f"{APP_NAME}\n버전: {APP_VERSION}\n프로토콜: LS XGT Cnet\n개발자: PLC Diagnostics Team",
        "err_nak": "오류: PLC에서 NAK 응답. 오류 코드: ",
        "write_confirm": "쓰기 확인됨",
        "read_result": "읽기 결과",
    }
}


def load_config():
    """Konfiguratsiyani fayldan yuklash."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_config(config):
    """Konfiguratsiyani faylga saqlash."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError:
        pass


def scan_serial_ports():
    """Mavjud serial portlarni topish."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in sorted(ports)]


def validate_address(address):
    """PLC manzil formatini tekshirish."""
    pattern = r'^%[A-Z]{1,2}[BW]?\d+$'
    return bool(re.match(pattern, address.upper()))


def validate_hex(value):
    """Hex qiymatni tekshirish."""
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def convert_value_to_hex(value_str, data_type):
    """Qiymatni belgilangan turdan hex ga o'girish."""
    try:
        if data_type == "HEX":
            if not validate_hex(value_str):
                return None
            val = value_str.upper()
            if len(val) % 2 != 0:
                val = '0' + val
            return val.zfill(4)
        elif data_type == "UINT":
            val = int(value_str)
            if val < 0 or val > 65535:
                return None
            return f"{val:04X}"
        elif data_type == "INT":
            val = int(value_str)
            if val < -32768 or val > 32767:
                return None
            if val < 0:
                val = val + 65536
            return f"{val:04X}"
        elif data_type == "BOOL":
            val = int(value_str)
            if val not in (0, 1):
                return None
            return f"{val:04X}"
        elif data_type == "DWORD":
            val = int(value_str)
            if val < 0 or val > 4294967295:
                return None
            return f"{val:08X}"
    except (ValueError, TypeError):
        return None
    return None


def convert_hex_to_value(hex_str, data_type):
    """Hex qiymatni belgilangan turga o'girish."""
    try:
        if data_type == "HEX":
            return hex_str.upper()
        elif data_type == "UINT":
            return str(int(hex_str, 16))
        elif data_type == "INT":
            val = int(hex_str, 16)
            if val > 32767:
                val = val - 65536
            return str(val)
        elif data_type == "BOOL":
            return "1" if int(hex_str, 16) != 0 else "0"
        elif data_type == "DWORD":
            return str(int(hex_str, 16))
    except (ValueError, TypeError):
        return hex_str
    return hex_str


class PLCTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Thread-safe UI yangilash uchun queue ---
        self._ui_queue = queue.Queue()

        # --- Monitoring holati ---
        self._monitoring = False
        self._monitor_thread = None

        # --- Log fayl uchun lock ---
        self._log_lock = threading.Lock()

        # --- Ulanish holati uchun lock ---
        self._connection_lock = threading.Lock()

        self.current_lang = "EN"
        self.serial_port = None

        # --- Log papkasini yaratish ---
        os.makedirs(LOG_DIR, exist_ok=True)
        self.log_filename = os.path.join(
            LOG_DIR,
            f"PLC_Log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        self.write_log_to_file("=== PLC DIAGNOSTICS STARTED ===")

        # --- Konfiguratsiyani yuklash ---
        self.config = load_config()

        # --- Oyna sozlamalari ---
        self.title(LANG[self.current_lang]["title"])
        self.geometry(self.config.get("geometry", "950x720"))
        self.minsize(850, 650)

        # --- Oyna yopilganda ---
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.setup_ui()
        self._apply_saved_config()
        self.update_texts()

        # --- UI queueni tekshirish ---
        self._process_ui_queue()

        # --- Eski loglarni tozalash (30 kundan eski) ---
        self._cleanup_old_logs(max_age_days=30)

    def _apply_saved_config(self):
        """Saqlangan konfiguratsiyani UI ga qo'llash."""
        if "com_port" in self.config:
            self.port_combo.set(self.config["com_port"])
        if "baudrate" in self.config:
            self.baud_combo.set(self.config["baudrate"])
        if "station" in self.config:
            self.entry_station.delete(0, "end")
            self.entry_station.insert(0, self.config["station"])
        if "language" in self.config:
            self.current_lang = self.config["language"]
            self.lang_switch.set(self.current_lang)
        if "data_type" in self.config:
            self.data_type_combo.set(self.config["data_type"])

    def _save_current_config(self):
        """Joriy sozlamalarni saqlash."""
        self.config["com_port"] = self.port_combo.get()
        self.config["baudrate"] = self.baud_combo.get()
        self.config["station"] = self.entry_station.get()
        self.config["language"] = self.current_lang
        self.config["data_type"] = self.data_type_combo.get()
        self.config["geometry"] = self.geometry()
        save_config(self.config)

    def _on_closing(self):
        """Oyna yopilganda chaqiriladi - portni yopish va configni saqlash."""
        self._monitoring = False
        self._save_current_config()
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.write_log_to_file("=== PLC DIAGNOSTICS CLOSED ===")
        self.destroy()

    def _process_ui_queue(self):
        """Thread-safe: queue dan UI buyruqlarni bajarish (main threadda)."""
        try:
            while True:
                func, args, kwargs = self._ui_queue.get_nowait()
                func(*args, **kwargs)
        except queue.Empty:
            pass
        self.after(50, self._process_ui_queue)

    def _run_on_ui(self, func, *args, **kwargs):
        """Thread-safe: funksiyani main threadga yuborish."""
        self._ui_queue.put((func, args, kwargs))

    def _cleanup_old_logs(self, max_age_days=30):
        """Eski log fayllarni o'chirish."""
        try:
            now = time.time()
            for filename in os.listdir(LOG_DIR):
                filepath = os.path.join(LOG_DIR, filename)
                if os.path.isfile(filepath) and filename.startswith("PLC_Log_"):
                    age_days = (now - os.path.getmtime(filepath)) / 86400
                    if age_days > max_age_days:
                        os.remove(filepath)
        except OSError:
            pass

    def setup_ui(self):
        # === TOP BAR: TIL VA HAQIDA ===
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.pack(fill="x", padx=10, pady=(5, 0))

        self.btn_about = ctk.CTkButton(
            self.frame_top, text="About", width=60,
            fg_color="gray30", hover_color="gray40",
            command=self.show_about
        )
        self.btn_about.pack(side="left")

        self.lang_switch = ctk.CTkSegmentedButton(
            self.frame_top, values=["EN", "UZ", "KR"],
            command=self.change_language
        )
        self.lang_switch.set("EN")
        self.lang_switch.pack(side="right")

        # === STATUS BAR (yuqorida) ===
        self.frame_status = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_status.pack(fill="x", padx=10, pady=(2, 0))

        self.status_indicator = ctk.CTkLabel(
            self.frame_status, text="  ",
            width=14, height=14, corner_radius=7,
            fg_color="red"
        )
        self.status_indicator.pack(side="left", padx=(5, 5))

        self.status_label = ctk.CTkLabel(
            self.frame_status, text="Disconnected",
            font=("Arial", 12), text_color="gray"
        )
        self.status_label.pack(side="left")

        # === 1-BLOK: ULANISH SOZLAMALARI ===
        self.frame_conn = ctk.CTkFrame(self)
        self.frame_conn.pack(pady=5, padx=10, fill="x")

        # COM Port
        self.lbl_port = ctk.CTkLabel(self.frame_conn, font=("Arial", 13, "bold"))
        self.lbl_port.pack(side="left", padx=(10, 5), pady=10)

        ports = scan_serial_ports()
        self.port_combo = ctk.CTkComboBox(
            self.frame_conn, width=120,
            values=ports if ports else ["COM1"]
        )
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("COM1")
        self.port_combo.pack(side="left", padx=5)

        self.btn_scan = ctk.CTkButton(
            self.frame_conn, text="Scan", width=50,
            fg_color="gray30", hover_color="gray40",
            command=self.refresh_ports
        )
        self.btn_scan.pack(side="left", padx=(2, 10))

        # Baudrate
        self.lbl_baud = ctk.CTkLabel(self.frame_conn, font=("Arial", 13))
        self.lbl_baud.pack(side="left", padx=(10, 5))

        self.baud_combo = ctk.CTkComboBox(
            self.frame_conn, width=100,
            values=SUPPORTED_BAUDRATES
        )
        self.baud_combo.set("115200")
        self.baud_combo.pack(side="left", padx=5)

        # Stansiya raqami
        self.lbl_station = ctk.CTkLabel(self.frame_conn, font=("Arial", 13))
        self.lbl_station.pack(side="left", padx=(10, 5))

        self.entry_station = ctk.CTkEntry(self.frame_conn, width=50)
        self.entry_station.insert(0, "0")
        self.entry_station.pack(side="left", padx=5)

        # Connect tugmasi
        self.btn_connect = ctk.CTkButton(
            self.frame_conn, fg_color="green",
            hover_color="#228B22", width=130,
            command=self.toggle_connection
        )
        self.btn_connect.pack(side="right", padx=10)

        # === 2-BLOK: O'QISH VA YOZISH ===
        self.frame_rw = ctk.CTkFrame(self)
        self.frame_rw.pack(pady=5, padx=10, fill="x")

        # Data type tanlash
        self.frame_dtype = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_dtype.pack(fill="x", padx=10, pady=(10, 0))

        self.lbl_dtype = ctk.CTkLabel(self.frame_dtype, font=("Arial", 13))
        self.lbl_dtype.pack(side="left", padx=5)

        self.data_type_combo = ctk.CTkComboBox(
            self.frame_dtype, width=120,
            values=list(DATA_TYPES.keys())
        )
        self.data_type_combo.set("HEX")
        self.data_type_combo.pack(side="left", padx=5)

        # Read va Write panellari
        self.frame_panels = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_panels.pack(fill="x", padx=5)

        # Read panel
        self.frame_read = ctk.CTkFrame(self.frame_panels, fg_color="transparent")
        self.frame_read.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.lbl_read_sec = ctk.CTkLabel(self.frame_read, font=("Arial", 14, "bold"))
        self.lbl_read_sec.pack()

        self.entry_read_addr = ctk.CTkEntry(self.frame_read, width=200)
        self.entry_read_addr.pack(pady=5)

        self.btn_read = ctk.CTkButton(self.frame_read, command=self.read_data)
        self.btn_read.pack(pady=5)

        # Write panel
        self.frame_write = ctk.CTkFrame(self.frame_panels, fg_color="transparent")
        self.frame_write.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        self.lbl_write_sec = ctk.CTkLabel(self.frame_write, font=("Arial", 14, "bold"))
        self.lbl_write_sec.pack()

        self.entry_write_addr = ctk.CTkEntry(self.frame_write, width=200)
        self.entry_write_addr.pack(pady=5)

        self.entry_write_val = ctk.CTkEntry(self.frame_write, width=200)
        self.entry_write_val.pack(pady=5)

        self.btn_write = ctk.CTkButton(
            self.frame_write, fg_color="#C8504B",
            hover_color="#A03030", command=self.write_data
        )
        self.btn_write.pack(pady=5)

        # === 3-BLOK: MONITORING ===
        self.frame_monitor = ctk.CTkFrame(self)
        self.frame_monitor.pack(pady=5, padx=10, fill="x")

        self.lbl_monitor = ctk.CTkLabel(
            self.frame_monitor, font=("Arial", 13, "bold")
        )
        self.lbl_monitor.pack(side="left", padx=10, pady=8)

        self.lbl_interval = ctk.CTkLabel(self.frame_monitor, font=("Arial", 12))
        self.lbl_interval.pack(side="left", padx=(10, 5))

        self.entry_interval = ctk.CTkEntry(self.frame_monitor, width=70)
        self.entry_interval.insert(0, "1000")
        self.entry_interval.pack(side="left", padx=5)

        self.btn_monitor = ctk.CTkButton(
            self.frame_monitor, fg_color="#5B8C5A",
            hover_color="#4A7A49", width=160,
            command=self.toggle_monitoring
        )
        self.btn_monitor.pack(side="left", padx=10)

        # === 4-BLOK: TERMINAL ===
        self.frame_log = ctk.CTkFrame(self)
        self.frame_log.pack(pady=5, padx=10, fill="both", expand=True)

        self.frame_log_header = ctk.CTkFrame(self.frame_log, fg_color="transparent")
        self.frame_log_header.pack(fill="x", padx=10, pady=(5, 0))

        self.lbl_terminal = ctk.CTkLabel(
            self.frame_log_header, font=("Arial", 13, "bold")
        )
        self.lbl_terminal.pack(side="left")

        self.btn_clear = ctk.CTkButton(
            self.frame_log_header, text="Clear",
            width=80, fg_color="gray30", hover_color="gray40",
            command=self.clear_log
        )
        self.btn_clear.pack(side="right")

        self.textbox_log = ctk.CTkTextbox(
            self.frame_log, font=("Consolas", 12),
            fg_color="black"
        )
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Tag ranglarni sozlash
        self.textbox_log._textbox.tag_config("green", foreground="#00FF00")
        self.textbox_log._textbox.tag_config("red", foreground="#FF4444")
        self.textbox_log._textbox.tag_config("yellow", foreground="#FFDD00")
        self.textbox_log._textbox.tag_config("cyan", foreground="#00DDFF")
        self.textbox_log._textbox.tag_config("white", foreground="#CCCCCC")
        self.textbox_log._textbox.tag_config("orange", foreground="#FFA500")

    def show_about(self):
        """Dastur haqida dialog."""
        lang = LANG[self.current_lang]
        dialog = ctk.CTkToplevel(self)
        dialog.title(lang["about"])
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        lbl = ctk.CTkLabel(
            dialog, text=lang["about_text"],
            font=("Arial", 14), justify="center"
        )
        lbl.pack(expand=True, padx=20, pady=20)

        btn = ctk.CTkButton(dialog, text="OK", width=80, command=dialog.destroy)
        btn.pack(pady=(0, 20))

    def refresh_ports(self):
        """Serial portlarni qayta skanerlash."""
        ports = scan_serial_ports()
        if ports:
            self.port_combo.configure(values=ports)
            self.port_combo.set(ports[0])
        else:
            self.port_combo.configure(values=["No ports found"])
            self.port_combo.set("No ports found")

    def clear_log(self):
        """Terminal logini tozalash."""
        self.textbox_log.configure(state="normal")
        self.textbox_log._textbox.delete("1.0", "end")

    def change_language(self, choice):
        self.current_lang = choice
        self.update_texts()

    def update_texts(self):
        lang = LANG[self.current_lang]
        self.title(lang["title"])
        self.lbl_port.configure(text=lang["com_port"])
        self.lbl_baud.configure(text=lang["baudrate"])
        self.lbl_station.configure(text=lang["station"])
        self.lbl_read_sec.configure(text=lang["read_sec"])
        self.lbl_write_sec.configure(text=lang["write_sec"])
        self.entry_read_addr.configure(placeholder_text=lang["addr_ph"])
        self.entry_write_addr.configure(placeholder_text=lang["addr_ph"])
        self.entry_write_val.configure(placeholder_text=lang["val_ph"])
        self.btn_read.configure(text=lang["btn_read"])
        self.btn_write.configure(text=lang["btn_write"])
        self.lbl_terminal.configure(text=lang["terminal"])
        self.lbl_dtype.configure(text=lang["data_type"])
        self.lbl_monitor.configure(text=lang["monitoring"])
        self.lbl_interval.configure(text=lang["mon_interval"])
        self.btn_clear.configure(text=lang["clear_log"])
        self.btn_scan.configure(text=lang["scan_ports"])
        self.btn_about.configure(text=lang["about"])

        if self.serial_port and self.serial_port.is_open:
            self.btn_connect.configure(text=lang["disconnect"])
            self.status_label.configure(
                text=lang["status_connected"], text_color="#00FF00"
            )
        else:
            self.btn_connect.configure(text=lang["connect"])
            self.status_label.configure(
                text=lang["status_disconnected"], text_color="gray"
            )

        if self._monitoring:
            self.btn_monitor.configure(text=lang["mon_stop"])
        else:
            self.btn_monitor.configure(text=lang["mon_start"])

    # --- PROTOKOL ---
    def calculate_bcc(self, frame_bytes):
        """BCC = barcha baytlar yig'indisi & 0xFF, 2 belgili HEX."""
        total = sum(frame_bytes) & 0xFF
        return f"{total:02X}"

    def build_xgt_frame(self, cmd, address, data_hex=""):
        """
        XGT Cnet protokol ramkasi.
        cmd: "RSS" yoki "WSS"
        address: masalan "%MW100"
        data_hex: yozishda hex qiymat
        """
        try:
            station = int(self.entry_station.get())
            if station < 0 or station > 31:
                station = 0
        except (ValueError, TypeError):
            station = 0
        station_str = f"{station:02d}"

        block_count = "01"
        var_name = address.encode('ascii')
        var_len = f"{len(address):02d}"

        ENQ = b'\x05'
        EOT = b'\x04'

        frame_parts = [
            ENQ,
            station_str.encode('ascii'),
            cmd.encode('ascii'),
            block_count.encode('ascii'),
            var_len.encode('ascii'),
            var_name
        ]

        if cmd.upper() == "WSS" and data_hex:
            # Ma'lumot uzunligi (baytlar soni)
            data_byte_count = len(data_hex) // 2
            frame_parts.append(f"{data_byte_count:02d}".encode('ascii'))
            frame_parts.append(data_hex.encode('ascii'))

        frame_parts.append(EOT)
        frame = b''.join(frame_parts)

        # BCC qo'shish
        if cmd[0].islower():
            bcc_value = self.calculate_bcc(frame)
            frame = frame + bcc_value.encode('ascii')

        return frame

    def toggle_connection(self):
        """Ulash/uzish."""
        with self._connection_lock:
            lang = LANG[self.current_lang]

            if self.serial_port and self.serial_port.is_open:
                # Monitoringni to'xtatish
                self._monitoring = False
                try:
                    self.serial_port.close()
                except Exception:
                    pass
                self.serial_port = None
                self.btn_connect.configure(text=lang["connect"], fg_color="green")
                self.status_indicator.configure(fg_color="red")
                self.status_label.configure(
                    text=lang["status_disconnected"], text_color="gray"
                )
                self.log_message(lang["sys_disconn"], "yellow")
            else:
                port = self.port_combo.get()
                baud_str = self.baud_combo.get()

                # Baudrate validatsiyasi
                try:
                    baud = int(baud_str)
                except ValueError:
                    self.log_message(lang["err_invalid_baud"], "red")
                    return

                try:
                    self.serial_port = serial.Serial(
                        port, baudrate=baud, timeout=1.5
                    )
                    self.btn_connect.configure(
                        text=lang["disconnect"], fg_color="red"
                    )
                    self.status_indicator.configure(fg_color="#00FF00")
                    self.status_label.configure(
                        text=f"{lang['status_connected']} - {port}",
                        text_color="#00FF00"
                    )
                    self.log_message(
                        f"{lang['sys_conn']} {port} ({baud} bps)", "green"
                    )
                    self._save_current_config()
                except serial.SerialException as e:
                    self.serial_port = None
                    self.log_message(f"{lang['err_cable']} {e}", "red")

    def send_to_plc(self, frame, cmd, address, value=""):
        """PLCga ramka yuborish va javob olish (background threadda ishlaydi)."""
        lang = LANG[self.current_lang]
        data_type = self.data_type_combo.get()

        if not self.serial_port or not self.serial_port.is_open:
            self._run_on_ui(self.log_message, lang["err_not_connected"], "red")
            return

        try:
            # So'rovni ekranga chiqarish
            display_ask = frame.replace(
                b'\x05', b'[ENQ]'
            ).replace(
                b'\x04', b'[EOT]'
            ).decode('ascii', errors='ignore')
            self._run_on_ui(
                self.log_message, f"[ASK]  > {display_ask}", "cyan"
            )

            self.serial_port.write(frame)
            time.sleep(0.05)

            # Javobni o'qish
            response = self.serial_port.read_until(b'\x03')
            if response and b'\x03' in response:
                bcc_bytes = self.serial_port.read(2)
                response += bcc_bytes
            elif not response:
                self._run_on_ui(
                    self.log_message,
                    f"[RES]  < {address} -> {lang['err_timeout']}", "red"
                )
                return

            resp_str = response.decode('ascii', errors='ignore')
            clean_res = (resp_str
                         .replace('\x06', '[ACK]')
                         .replace('\x15', '[NAK]')
                         .replace('\x05', '[ENQ]')
                         .replace('\x04', '[EOT]')
                         .replace('\x03', '[ETX]'))

            if '\x06' in resp_str:
                # ACK - muvaffaqiyatli
                if cmd.upper() == "RSS":
                    # Javobdan ma'lumotni ajratish
                    data_part = resp_str.split('\x03')[0] if '\x03' in resp_str else resp_str
                    hex_match = re.findall(r'[0-9A-Fa-f]{2,}', data_part)
                    if hex_match:
                        raw_hex = hex_match[-1]
                        # 4 yoki 8 belgili hex
                        if len(raw_hex) >= 4:
                            display_val = convert_hex_to_value(raw_hex[-4:], data_type)
                            raw_display = raw_hex[-4:].upper()
                        else:
                            display_val = raw_hex.upper()
                            raw_display = raw_hex.upper()
                        self._run_on_ui(
                            self.log_message,
                            f"[RES]  < {address} = {display_val} (0x{raw_display}) -> {lang['read_result']} ✅",
                            "green"
                        )
                    else:
                        self._run_on_ui(
                            self.log_message,
                            f"[RES]  < {address} = ??? -> {clean_res}", "orange"
                        )
                elif cmd.upper() == "WSS":
                    self._run_on_ui(
                        self.log_message,
                        f"[RES]  < {address} <- {value} -> {lang['write_confirm']} ✅",
                        "green"
                    )
                else:
                    self._run_on_ui(
                        self.log_message,
                        f"[RES]  < {clean_res} -> SUCCESS ✅", "green"
                    )
            elif '\x15' in resp_str:
                # NAK - xatolik kodi bilan
                error_part = resp_str.split('\x15')[-1].split('\x03')[0] if '\x03' in resp_str else ""
                self._run_on_ui(
                    self.log_message,
                    f"[RES]  < {address} -> {lang['err_nak']}{error_part} ❌",
                    "red"
                )
            else:
                self._run_on_ui(
                    self.log_message,
                    f"[RES]  < {clean_res}", "white"
                )

        except serial.SerialException:
            self._run_on_ui(self.log_message, lang["err_lost"], "red")
            self._run_on_ui(self._handle_connection_lost)

    def _handle_connection_lost(self):
        """Ulanish uzilganda (main threadda chaqiriladi)."""
        lang = LANG[self.current_lang]
        self._monitoring = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None
        self.btn_connect.configure(text=lang["connect"], fg_color="green")
        self.status_indicator.configure(fg_color="red")
        self.status_label.configure(
            text=lang["status_disconnected"], text_color="gray"
        )

    def read_data(self):
        """Ma'lumot o'qish - validatsiya bilan."""
        lang = LANG[self.current_lang]
        addr = self.entry_read_addr.get().strip()

        if not addr:
            self.log_message(lang["err_empty_addr"], "red")
            return

        if not validate_address(addr):
            self.log_message(lang["err_invalid_addr"], "red")
            return

        if not self.serial_port or not self.serial_port.is_open:
            self.log_message(lang["err_not_connected"], "red")
            return

        frame = self.build_xgt_frame("RSS", addr)
        threading.Thread(
            target=self.send_to_plc, args=(frame, "RSS", addr),
            daemon=True
        ).start()

    def write_data(self):
        """Ma'lumot yozish - validatsiya bilan."""
        lang = LANG[self.current_lang]
        addr = self.entry_write_addr.get().strip()
        val = self.entry_write_val.get().strip()
        data_type = self.data_type_combo.get()

        if not addr:
            self.log_message(lang["err_empty_addr"], "red")
            return

        if not val:
            self.log_message(lang["err_empty_val"], "red")
            return

        if not validate_address(addr):
            self.log_message(lang["err_invalid_addr"], "red")
            return

        if not self.serial_port or not self.serial_port.is_open:
            self.log_message(lang["err_not_connected"], "red")
            return

        # Qiymatni hex ga o'girish
        hex_val = convert_value_to_hex(val, data_type)
        if hex_val is None:
            self.log_message(lang["err_invalid_hex"], "red")
            return

        frame = self.build_xgt_frame("WSS", addr, hex_val)
        threading.Thread(
            target=self.send_to_plc, args=(frame, "WSS", addr, val),
            daemon=True
        ).start()

    def toggle_monitoring(self):
        """Monitoringni boshlash/to'xtatish."""
        lang = LANG[self.current_lang]

        if self._monitoring:
            self._monitoring = False
            self.btn_monitor.configure(
                text=lang["mon_start"], fg_color="#5B8C5A"
            )
            self.log_message("[MONITOR] Stopped", "yellow")
        else:
            addr = self.entry_read_addr.get().strip()
            if not addr:
                self.log_message(lang["err_empty_addr"], "red")
                return
            if not validate_address(addr):
                self.log_message(lang["err_invalid_addr"], "red")
                return
            if not self.serial_port or not self.serial_port.is_open:
                self.log_message(lang["err_not_connected"], "red")
                return

            try:
                interval = int(self.entry_interval.get())
                if interval < 100:
                    interval = 100
            except (ValueError, TypeError):
                interval = 1000

            self._monitoring = True
            self.btn_monitor.configure(
                text=lang["mon_stop"], fg_color="#C8504B"
            )
            self.log_message(
                f"[MONITOR] Started: {addr} every {interval}ms", "cyan"
            )
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, args=(addr, interval),
                daemon=True
            )
            self._monitor_thread.start()

    def _monitor_loop(self, address, interval_ms):
        """Monitoring sikli (background threadda)."""
        while self._monitoring:
            if not self.serial_port or not self.serial_port.is_open:
                self._monitoring = False
                break

            frame = self.build_xgt_frame("RSS", address)
            self.send_to_plc(frame, "RSS", address)
            time.sleep(interval_ms / 1000.0)

    def write_log_to_file(self, text):
        """Thread-safe log yozish."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self._log_lock:
            try:
                with open(self.log_filename, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {text}\n")
            except IOError:
                pass

    def log_message(self, message, color="white"):
        """Terminalga rangli xabar yozish (faqat main threaddan chaqirish!)."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        self.textbox_log._textbox.insert("end", full_msg, color)
        self.textbox_log.see("end")
        self.write_log_to_file(message)


if __name__ == "__main__":
    app = PLCTesterApp()
    app.mainloop()
