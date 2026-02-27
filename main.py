import customtkinter as ctk
import serial
import threading
import time
import datetime

# --- UI SOZLAMALARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- LUG'AT (DICTIONARY) ---
LANG = {
    "EN": {
        "title": "LS XGT PLC - Universal Diagnostic Tool (Cnet)",
        "com_port": "COM Port:",
        "baudrate": "Baudrate:",
        "station": "Station:",
        "connect": "CONNECT",
        "disconnect": "DISCONNECT",
        "read_sec": "READ (RSS)",
        "write_sec": "WRITE (WSS)",
        "addr_ph": "Address (e.g., %MW100)",
        "val_ph": "Value (Hex, e.g., 0001)",
        "btn_read": "READ DATA",
        "btn_write": "WRITE DATA",
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
        "read_sec": "읽기 (RSS)",
        "write_sec": "쓰기 (WSS)",
        "addr_ph": "주소 (예: %MW100)",
        "val_ph": "값 (Hex, 예: 0001)",
        "btn_read": "데이터 읽기",
        "btn_write": "데이터 쓰기",
        "terminal": "라이브 터미널 (요청/응답 및 오류)",
        "sys_conn": "시스템: 연결 성공 ->",
        "sys_disconn": "시스템: 연결이 해제되었습니다.",
        "err_cable": "오류: 케이블을 확인하세요! ->",
        "err_timeout": "[RES]  < 오류: PLC 응답 없음 (시간 초과)",
        "err_lost": "연결 끊김: 포트 통신 단절! 프로그램 충돌이 방지되었습니다."
    }
}

class PLCTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.current_lang = "EN"
        self.title(LANG[self.current_lang]["title"])
        self.geometry("850x650")
        self.serial_port = None
        
        self.log_filename = f"PLC_Test_Log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.write_log_to_file("=== PLC DIAGNOSTICS STARTED ===")

        self.setup_ui()
        self.update_texts()

    def setup_ui(self):
        # --- TOP BAR: LANGUAGE SWITCHER ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.pack(fill="x", padx=10, pady=5)
        
        self.lang_switch = ctk.CTkSegmentedButton(self.frame_top, values=["EN", "KR"], command=self.change_language)
        self.lang_switch.set("EN")
        self.lang_switch.pack(side="right")

        # --- 1-BLOK: ULANISH (with Station) ---
        self.frame_conn = ctk.CTkFrame(self)
        self.frame_conn.pack(pady=5, padx=10, fill="x")

        self.lbl_port = ctk.CTkLabel(self.frame_conn, font=("Arial", 14, "bold"))
        self.lbl_port.pack(side="left", padx=10, pady=10)
        
        self.entry_port = ctk.CTkEntry(self.frame_conn, width=100)
        self.entry_port.insert(0, "COM10")
        self.entry_port.pack(side="left", padx=5)

        self.lbl_baud = ctk.CTkLabel(self.frame_conn)
        self.lbl_baud.pack(side="left", padx=10)
        
        self.entry_baud = ctk.CTkEntry(self.frame_conn, width=100)
        self.entry_baud.insert(0, "115200")
        self.entry_baud.pack(side="left", padx=5)

        # Yangi: stansiya raqami
        self.lbl_station = ctk.CTkLabel(self.frame_conn)
        self.lbl_station.pack(side="left", padx=10)
        self.entry_station = ctk.CTkEntry(self.frame_conn, width=50)
        self.entry_station.insert(0, "0")
        self.entry_station.pack(side="left", padx=5)

        self.btn_connect = ctk.CTkButton(self.frame_conn, fg_color="green", command=self.toggle_connection)
        self.btn_connect.pack(side="right", padx=10)

        # --- 2-BLOK: O'QISH VA YOZISH ---
        self.frame_rw = ctk.CTkFrame(self)
        self.frame_rw.pack(pady=10, padx=10, fill="x")

        # Read
        self.frame_read = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_read.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.lbl_read_sec = ctk.CTkLabel(self.frame_read, font=("Arial", 14, "bold"))
        self.lbl_read_sec.pack()
        self.entry_read_addr = ctk.CTkEntry(self.frame_read, width=200)
        self.entry_read_addr.pack(pady=5)
        self.btn_read = ctk.CTkButton(self.frame_read, command=self.read_data)
        self.btn_read.pack(pady=5)

        # Write
        self.frame_write = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_write.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        self.lbl_write_sec = ctk.CTkLabel(self.frame_write, font=("Arial", 14, "bold"))
        self.lbl_write_sec.pack()
        self.entry_write_addr = ctk.CTkEntry(self.frame_write, width=200)
        self.entry_write_addr.pack(pady=5)
        self.entry_write_val = ctk.CTkEntry(self.frame_write, width=200)
        self.entry_write_val.pack(pady=5)
        self.btn_write = ctk.CTkButton(self.frame_write, fg_color="#C8504B", command=self.write_data)
        self.btn_write.pack(pady=5)

        # --- 3-BLOK: TERMINAL ---
        self.frame_log = ctk.CTkFrame(self)
        self.frame_log.pack(pady=10, padx=10, fill="both", expand=True)
        self.lbl_terminal = ctk.CTkLabel(self.frame_log)
        self.lbl_terminal.pack(anchor="w", padx=10)
        
        self.textbox_log = ctk.CTkTextbox(self.frame_log, font=("Consolas", 12), text_color="#00FF00", fg_color="black")
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=10)

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
        
        if self.serial_port and self.serial_port.is_open:
            self.btn_connect.configure(text=lang["disconnect"])
        else:
            self.btn_connect.configure(text=lang["connect"])

    # --- PROTOKOL MANTIQ (TO'G'IRLANGAN) ---
    def calculate_bcc(self, frame_without_bcc):
        """
        frame_without_bcc: baytlar ro'yxati (ENQ dan EOT gacha, ikkalasi ham ichida)
        BCC = (sum of all bytes) & 0xFF, so'ng 2 belgili HEX
        """
        total = sum(frame_without_bcc) & 0xFF
        return f"{total:02X}"

    def build_xgt_frame(self, cmd, address, data_hex=""):
        """
        cmd: "rss" yoki "wss"
        address: masalan "%MW100"
        data_hex: (faqat yozishda) juft sonli hex raqamlar, masalan "00FF"
        """
        # Stansiya raqamini 2 belgili ASCII ga aylantirish
        try:
            station = int(self.entry_station.get())
            if station < 0 or station > 31:
                station = 0
        except:
            station = 0
        station_str = f"{station:02d}"  # "00" dan "31" gacha

        # Blok soni har doim 1 ("01")
        block_count = "01"

        # O'zgaruvchi nomi uzunligi (masalan "%MW100" -> 6)
        var_len = f"{len(address):02d}"

        # ENQ va EOT belgilari
        ENQ = b'\x05'
        EOT = b'\x04'

        # Ramkaning asosiy qismi (ENQ dan tashqari, lekin BCC hisoblash uchun ENQ ni qo'shamiz)
        # Avval baytlar ro'yxatini tuzamiz
        # ENQ + station_str + cmd + block_count + var_len + address + (agar yozish bo'lsa data_hex) + EOT
        frame_parts = [
            ENQ,
            station_str.encode('ascii'),
            cmd.encode('ascii'),      # kichik harf "rss" yoki "wss"
            block_count.encode('ascii'),
            var_len.encode('ascii'),
            address.encode('ascii')
        ]
        if cmd == "WSS" and data_hex:
            # Ma'lumotni ASCII hex sifatida qo'shamiz
            frame_parts.append(data_hex.encode('ascii'))
        frame_parts.append(EOT)

        # Barcha qismlarni birlashtiramiz
        frame = b''.join(frame_parts)

        # BCC hisoblash (ENQ dan EOT gacha bo'lgan barcha baytlar)
        bcc_value = self.calculate_bcc(frame)   # frame ichida ENQ va EOT bor
        bcc_bytes = bcc_value.encode('ascii')   # 2 bayt

        # To'liq ramka = asosiy qism + BCC
        full_frame = frame + bcc_bytes
        return full_frame

    def toggle_connection(self):
        lang = LANG[self.current_lang]
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.btn_connect.configure(text=lang["connect"], fg_color="green")
            self.log_message(lang["sys_disconn"], "yellow")
        else:
            try:
                port = self.entry_port.get()
                baud = int(self.entry_baud.get())
                self.serial_port = serial.Serial(port, baudrate=baud, timeout=1.5)
                self.btn_connect.configure(text=lang["disconnect"], fg_color="red")
                self.log_message(f"{lang['sys_conn']} {port} ({baud} bps)", "green")
            except Exception as e:
                self.log_message(f"{lang['err_cable']} {e}", "red")

    def send_to_plc(self, frame):
        lang = LANG[self.current_lang]
        if not self.serial_port or not self.serial_port.is_open:
            return

        try:
            # So'rovni ekranga chiqarish
            display_ask = frame.replace(b'\x05', b'[ENQ]').replace(b'\x04', b'[EOT]').decode('ascii', errors='ignore')
            self.log_message(f"[ASK]  > {display_ask}", "cyan")
            
            self.serial_port.write(frame)
            time.sleep(0.1)

            # Javobni o'qish: ETX (0x03) gacha
            response = self.serial_port.read_until(b'\x03')
            if response and b'\x03' in response:
                # ETX dan keyin 2 bayt BCC ni o'qish
                bcc_bytes = self.serial_port.read(2)
                response += bcc_bytes
            elif not response:
                self.log_message(lang["err_timeout"], "red")
                return

            # Javobni matnga aylantirish
            resp_str = response.decode('ascii', errors='ignore')
            clean_res = resp_str.replace('\x06', '[ACK]').replace('\x15', '[NAK]').replace('\x05', '[ENQ]').replace('\x04', '[EOT]').replace('\x03', '[ETX]')
            
            if '\x06' in resp_str:
                self.log_message(f"[RES]  < {clean_res} -> SUCCESS ✅", "green")
            elif '\x15' in resp_str:
                self.log_message(f"[RES]  < {clean_res} -> ERROR (NAK) ❌", "red")
            else:
                self.log_message(f"[RES]  < {clean_res}", "white")

        except serial.SerialException:
            self.log_message(lang["err_lost"], "red")
            self.toggle_connection()

    def read_data(self):
        addr = self.entry_read_addr.get().strip()
        if addr:
            frame = self.build_xgt_frame("RSS", addr)
            threading.Thread(target=self.send_to_plc, args=(frame,)).start()

    def write_data(self):
        addr = self.entry_write_addr.get().strip()
        val = self.entry_write_val.get().strip()
        if addr and val:
            # Ma'lumot uzunligi juft bo'lishi kerak
            if len(val) % 2 != 0:
                val = '0' + val  # oldiga nol qo'shish
            frame = self.build_xgt_frame("WSS", addr, val)
            threading.Thread(target=self.send_to_plc, args=(frame,)).start()

    def write_log_to_file(self, text):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")

    def log_message(self, message, color="white"):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.write_log_to_file(message)

if __name__ == "__main__":
    app = PLCTesterApp()
    app.mainloop()