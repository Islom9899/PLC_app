import customtkinter as ctk
import serial
import threading
import time

# --- UI SOZLAMALARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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

class PLCTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "EN"
        self.title(LANG[self.current_lang]["title"])
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.destroy())
        self.serial_port = None
        self.setup_ui()
        self.update_texts()

    def setup_ui(self):
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.pack(fill="x", padx=10, pady=5)
        self.lang_switch = ctk.CTkSegmentedButton(self.frame_top, values=["EN", "KR"], command=self.change_language)
        self.lang_switch.set("EN")
        self.lang_switch.pack(side="right")

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

        self.lbl_station = ctk.CTkLabel(self.frame_conn)
        self.lbl_station.pack(side="left", padx=10)
        self.entry_station = ctk.CTkEntry(self.frame_conn, width=50)
        self.entry_station.insert(0, "00")
        self.entry_station.pack(side="left", padx=5)

        self.btn_connect = ctk.CTkButton(self.frame_conn, fg_color="green", command=self.toggle_connection)
        self.btn_connect.pack(side="right", padx=10)

        self.bcc_var = ctk.BooleanVar(value=True)
        self.chk_bcc = ctk.CTkCheckBox(self.frame_conn, text="", variable=self.bcc_var, onvalue=True, offvalue=False)
        self.chk_bcc.pack(side="right", padx=5)

        self.frame_rw = ctk.CTkFrame(self)
        self.frame_rw.pack(pady=10, padx=10, fill="x")

        self.frame_read = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_read.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.lbl_read_sec = ctk.CTkLabel(self.frame_read, font=("Arial", 14, "bold"))
        self.lbl_read_sec.pack()
        self.entry_read_addr = ctk.CTkEntry(self.frame_read, width=200)
        self.entry_read_addr.pack(pady=5)
        self.btn_read = ctk.CTkButton(self.frame_read, command=self.read_data)
        self.btn_read.pack(pady=5)

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
        self.chk_bcc.configure(text=lang["bcc_check"])
        self.lbl_terminal.configure(text=lang["terminal"])
        
        if self.serial_port and self.serial_port.is_open:
            self.btn_connect.configure(text=lang["disconnect"])
        else:
            self.btn_connect.configure(text=lang["connect"])

    # ------------------------------------------------------------
    # XGT frame yaratish (7.2.1, 7.2.3, 7.2.4 bo'limlar asosida)
    # ------------------------------------------------------------
    def calculate_bcc(self, frame_bytes):
        """ENQ dan EOT gacha bo'lgan baytlarning yig'indisining pastki 8 biti (7.2.3)"""
        total = sum(frame_bytes) & 0xFF
        return f"{total:02X}"  # 2 belgili hex string

    def build_xgt_frame(self, cmd_base, address, data_hex="", use_bcc=True):
        """
        cmd_base: 'r' yoki 'w'
        address: masalan '%MW100'
        data_hex: write uchun hex qiymat (masalan '0001')
        use_bcc: True bo'lsa, kichik harfli komanda va BCC qo'shiladi
        """
        try:
            station = int(self.entry_station.get())
            if station < 0 or station > 31:
                station = 0
        except:
            station = 0
        station_str = f"{station:02d}"                # 2 raqamli string

        cmd_letter = cmd_base.lower() if use_bcc else cmd_base.upper()
        cmd_type = "SS"
        block_count = "01"
        var_len = f"{len(address):02d}"

        ENQ = b'\x05'
        EOT = b'\x04'

        # ENQ dan EOT gacha bo'lgan qism (BCCsiz)
        parts = [
            ENQ,
            station_str.encode('ascii'),
            cmd_letter.encode('ascii'),
            cmd_type.encode('ascii'),
            block_count.encode('ascii'),
            var_len.encode('ascii'),
            address.encode('ascii')
        ]
        if cmd_base == 'w' and data_hex:
            parts.append(data_hex.encode('ascii'))
        parts.append(EOT)                     # EOT shu yerda

        frame_without_bcc = b''.join(parts)

        if use_bcc:
            bcc = self.calculate_bcc(frame_without_bcc).encode('ascii')
            full_frame = frame_without_bcc + bcc   # EOT dan keyin BCC
        else:
            full_frame = frame_without_bcc

        return full_frame

    # ------------------------------------------------------------
    # Serial ulanishni boshqarish
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Xabarlarni chiroyli ko'rsatish
    # ------------------------------------------------------------
    def bytes_to_display(self, data):
        result = []
        for b in data:
            if b == 0x05:
                result.append('[ENQ]')
            elif b == 0x06:
                result.append('[ACK]')
            elif b == 0x15:
                result.append('[NAK]')
            elif b == 0x04:
                result.append('[EOT]')
            elif b == 0x03:
                result.append('[ETX]')
            elif 32 <= b <= 126:
                result.append(chr(b))
            else:
                result.append(f'[{b:02X}]')
        return ''.join(result)

    # ------------------------------------------------------------
    # Xatolik kodlarini izohlash (7.2.8 bo'lim)
    # ------------------------------------------------------------
    def get_error_description(self, error_code):
        errors = {
            "0003": "Block count exceeds 16",
            "0004": "Variable length > 12",
            "0007": "Invalid data type (not X,B,W,D,L)",
            "0011": "Data error / invalid variable",
            "0090": "Monitor not registered",
            "0190": "Monitor number out of range",
            "0290": "Monitor registration number out of range",
            "1132": "Invalid device memory",
            "1232": "Data size > max (60 words)",
            "1234": "Extra frame data",
            "1332": "Data type mismatch in blocks",
            "1432": "Invalid hex data",
            "7132": "Variable area exceeded"
        }
        return errors.get(error_code, "Unknown error")

    # ------------------------------------------------------------
    # PLC ga so'rov yuborish va javobni tahlil qilish
    # ------------------------------------------------------------
    def send_to_plc(self, frame, cmd, address, value=""):
        lang = LANG[self.current_lang]
        if not self.serial_port or not self.serial_port.is_open:
            return

        try:
            self.log_message(f"[ASK]  > {self.bytes_to_display(frame)}", "cyan")
            self.serial_port.write(frame)
            time.sleep(0.1)

            use_bcc = self.bcc_var.get()   # BCC yoqilganmi?

            # Javobni o'qish: ETX gacha + keyin BCC (agar kerak bo'lsa)
            response = bytearray()
            # ETX gacha o'qish
            while True:
                ch = self.serial_port.read(1)
                if not ch:
                    break
                response.extend(ch)
                if ch == b'\x03':          # ETX
                    break

            if not response:
                self.log_message(f"[RES]  < {address} -> " + lang["err_timeout"], "red")
                return

            # BCC mavjudligini tekshirish: ETX dan keyin 2 bayt kelishi kerak
            if use_bcc:
                self.serial_port.timeout = 0.2
                bcc_bytes = self.serial_port.read(2)
                self.serial_port.timeout = 1.5
                if len(bcc_bytes) == 2:
                    response.extend(bcc_bytes)
                    has_bcc = True
                else:
                    has_bcc = False
            else:
                has_bcc = False

            self.log_message(f"[RES]  < {self.bytes_to_display(response)}", "white")

            if len(response) < 1:
                return

            first_byte = response[0]

            # ----------------------------------------------------
            # ACK javobi (0x06)
            # ----------------------------------------------------
            if first_byte == 0x06:
                if cmd == "r":          # Read javobi
                    # Minimal uzunlik: ACK + station(2) + cmd(1) + cmd_type(2) + block(2) + data_count(2) + data(2*?) + ETX
                    # Eng kamida data_count=01 bo'lganda data=2 bayt, jami: 1+2+1+2+2+2+2+1 = 13 bayt (BCCsiz)
                    min_len = 13
                    if has_bcc:
                        min_len += 2
                    if len(response) < min_len:
                        self.log_message("[RES]  < Response too short for read", "red")
                        return

                    # Data count (indeks 8) - 2 bayt ASCII
                    try:
                        data_cnt_ascii = response[8:10].decode('ascii')
                        data_bytes = int(data_cnt_ascii, 16)   # necha byte data (word*2)
                    except:
                        data_bytes = 0

                    data_start = 10
                    data_end = data_start + data_bytes * 2     # har bir byte 2 ASCII belgi

                    # ETX joylashuvi
                    if has_bcc:
                        etx_pos = len(response) - 3            # ETX + BCC(2)
                    else:
                        etx_pos = len(response) - 1            # faqat ETX

                    if data_end > etx_pos:
                        self.log_message("[RES]  < Data length mismatch", "red")
                        return

                    data_ascii = response[data_start:data_end].decode('ascii')
                    self.log_message(f"[RES]  < {address} = {data_ascii} -> SUCCESS ✅", "green")

                elif cmd == "w":        # Write javobi
                    # Minimal uzunlik: ACK + station(2) + cmd(1) + cmd_type(2) + ETX = 1+2+1+2+1 = 7
                    min_len = 7
                    if has_bcc:
                        min_len += 2
                    if len(response) < min_len:
                        self.log_message("[RES]  < Response too short for write", "red")
                        return

                    # Write uchun ACK da ETX 6-indeksda bo'lishi kerak
                    if response[6] == 0x03:
                        self.log_message(f"[RES]  < {address} <- {value} -> WRITE SUCCESS ✅", "green")
                    else:
                        self.log_message("[RES]  < Unexpected write response format", "red")

            # ----------------------------------------------------
            # NAK javobi (0x15) – xatolik
            # ----------------------------------------------------
            elif first_byte == 0x15:
                # NAK + station(2) + cmd(1) + cmd_type(2) dan keyin error code (4 byte ASCII) keladi
                error_start = 1 + 2 + 1 + 2   # NAK, station, cmd, cmd_type
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

    # ------------------------------------------------------------
    # O'qish va yozish tugmalari
    # ------------------------------------------------------------
    def read_data(self):
        addr = self.entry_read_addr.get().strip()
        if addr:
            use_bcc = self.bcc_var.get()
            frame = self.build_xgt_frame("r", addr, use_bcc=use_bcc)
            threading.Thread(target=self.send_to_plc, args=(frame, "r", addr)).start()

    def write_data(self):
        addr = self.entry_write_addr.get().strip()
        val = self.entry_write_val.get().strip()
        if addr and val:
            if len(val) % 2 != 0:
                val = '0' + val
            use_bcc = self.bcc_var.get()
            frame = self.build_xgt_frame("w", addr, val, use_bcc=use_bcc)
            threading.Thread(target=self.send_to_plc, args=(frame, "w", addr, val)).start()

    def log_message(self, message, color="white"):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

if __name__ == "__main__":
    app = PLCTesterApp()
    app.mainloop()