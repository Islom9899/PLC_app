import customtkinter as ctk
import serial
import threading
import time
import datetime
import os

# --- UI SOZLAMALARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PLCTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LS XGT PLC - Universal Diagnostika (Cnet)")
        self.geometry("750x550")
        self.serial_port = None
        
        # Log fayl yaratish (zavod uchun)
        self.log_filename = f"PLC_Test_Log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.write_log_to_file("=== PLC DIAGNOSTIKA BOSHLANDI ===")

        self.setup_ui()

    def setup_ui(self):
        # --- 1-BLOK: ULANISH ---
        self.frame_conn = ctk.CTkFrame(self)
        self.frame_conn.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.frame_conn, text="COM Port:", font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=10)
        self.entry_port = ctk.CTkEntry(self.frame_conn, width=100, placeholder_text="COM3")
        self.entry_port.insert(0, "COM3")
        self.entry_port.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_conn, text="Baudrate:").pack(side="left", padx=10)
        self.entry_baud = ctk.CTkEntry(self.frame_conn, width=100)
        self.entry_baud.insert(0, "115200")
        self.entry_baud.pack(side="left", padx=5)

        self.btn_connect = ctk.CTkButton(self.frame_conn, text="ULANISH", fg_color="green", command=self.toggle_connection)
        self.btn_connect.pack(side="right", padx=10)

        # --- 2-BLOK: O'QISH VA YOZISH (READ / WRITE) ---
        self.frame_rw = ctk.CTkFrame(self)
        self.frame_rw.pack(pady=10, padx=10, fill="x")

        # O'qish qismi
        self.frame_read = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_read.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.frame_read, text="O'QISH (READ)", font=("Arial", 14, "bold")).pack()
        self.entry_read_addr = ctk.CTkEntry(self.frame_read, placeholder_text="Manzil (Masalan: %MW100)")
        self.entry_read_addr.pack(pady=5)
        self.btn_read = ctk.CTkButton(self.frame_read, text="O'QISH (ASK)", command=self.read_data)
        self.btn_read.pack(pady=5)

        # Yozish qismi
        self.frame_write = ctk.CTkFrame(self.frame_rw, fg_color="transparent")
        self.frame_write.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.frame_write, text="YOZISH (WRITE)", font=("Arial", 14, "bold")).pack()
        self.entry_write_addr = ctk.CTkEntry(self.frame_write, placeholder_text="Manzil (Masalan: %MX00)")
        self.entry_write_addr.pack(pady=5)
        self.entry_write_val = ctk.CTkEntry(self.frame_write, placeholder_text="Qiymat (Hex, Masalan: 0001)")
        self.entry_write_val.pack(pady=5)
        self.btn_write = ctk.CTkButton(self.frame_write, text="YOZISH (ASK)", fg_color="#C8504B", command=self.write_data)
        self.btn_write.pack(pady=5)

        # --- 3-BLOK: JONLI LOG TERMINAL (ASK/RES) ---
        self.frame_log = ctk.CTkFrame(self)
        self.frame_log.pack(pady=10, padx=10, fill="both", expand=True)
        ctk.CTkLabel(self.frame_log, text="JONLI TERMINAL (ASK holati & Xatoliklar)").pack(anchor="w", padx=10)
        
        self.textbox_log = ctk.CTkTextbox(self.frame_log, font=("Consolas", 12), text_color="#00FF00", fg_color="black")
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=10)

    # --- PROTOKOL MANTIQ (BCC HISOBLASH VA QOLIP) ---
    def calculate_bcc(self, payload_string):
        """ EOT gacha bo'lgan barcha belgilarni qo'shib, BCC parolini hisoblaydi """
        bcc_val = sum(ord(c) for c in payload_string) & 0xFF
        return f"{bcc_val:02X}"

    def build_ls_frame(self, cmd_type, address, data_hex=""):
        """ LS XGT Cnet (Maxsus) protokoli qolipini yasash """
        addr_len = f"{len(address):02d}"
        
        # 00 = Stansiya, rSS/wSS = O'qish/Yozish buyrug'i, 01 = Blok soni
        payload = f"00{cmd_type}01{addr_len}{address}"
        
        if cmd_type == "wSS" and data_hex:
            data_bytes_len = f"{len(data_hex)//2:02d}"
            payload += f"{data_bytes_len}{data_hex}"
            
        payload += "\x04" # EOT qo'shish
        bcc = self.calculate_bcc(payload)
        
        full_frame = "\x05" + payload + bcc # \x05 = ENQ
        return full_frame

    # --- ULANISH VA XAVFSIZLIK ---
    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.btn_connect.configure(text="ULANISH", fg_color="green")
            self.log_message("TIZIM: Aloqa uzildi.", "yellow")
        else:
            try:
                port = self.entry_port.get()
                baud = int(self.entry_baud.get())
                self.serial_port = serial.Serial(port, baudrate=baud, timeout=1)
                self.btn_connect.configure(text="UZISH", fg_color="red")
                self.log_message(f"TIZIM: Muvaffaqiyatli ulandi -> {port} ({baud} bps)", "green")
            except Exception as e:
                self.log_message(f"XATOLIK: Kabelni tekshiring! -> {e}", "red")

    # --- ASOSIY ISH JARAYONI ---
    def send_to_plc(self, frame):
        if not self.serial_port or not self.serial_port.is_open:
            self.log_message("XATOLIK: Avval ulanish tugmasini bosing!", "red")
            return

        try:
            # So'rov (ASK) yuborish
            # Terminalda ko'rinishi oson bo'lishi uchun maxsus belgilarni almashtiramiz
            display_ask = frame.replace('\x05', '[ENQ]').replace('\x04', '[EOT]')
            self.log_message(f"[ASK]  > {display_ask}", "cyan")
            
            self.serial_port.write(frame.encode('ascii'))
            time.sleep(0.1) # PLC javob berishiga vaqt

            # Javobni o'qish (ETX \x03 gacha)
            response = self.serial_port.read_until(b'\x03') 
            
            if not response:
                self.log_message("[RES]  < XATOLIK: PLC dan javob kelmadi (Timeout)", "red")
                return

            # Javobni dekod qilib, ACK(0x06) va NAK(0x15) ni aniqlash
            resp_str = response.decode('ascii', errors='ignore')
            
            if '\x06' in resp_str:
                clean_res = resp_str.replace('\x06', '[ACK]')
                self.log_message(f"[RES]  < {clean_res} -> SUCCESS! ✅", "green")
            elif '\x15' in resp_str:
                clean_res = resp_str.replace('\x15', '[NAK]')
                self.log_message(f"[RES]  < {clean_res} -> ERROR HANDLING! ❌", "red")
            else:
                self.log_message(f"[RES]  < {resp_str}", "white")

        except serial.SerialException:
            self.log_message("KABEL UZILDI: Port bilan aloqa yo'qoldi! Dastur qulashdan saqlandi.", "red")
            self.toggle_connection() # Xavfsiz uzish

    def read_data(self):
        addr = self.entry_read_addr.get()
        if addr:
            frame = self.build_ls_frame("rSS", addr)
            threading.Thread(target=self.send_to_plc, args=(frame,)).start()

    def write_data(self):
        addr = self.entry_write_addr.get()
        val = self.entry_write_val.get()
        if addr and val:
            frame = self.build_ls_frame("wSS", addr, val)
            threading.Thread(target=self.send_to_plc, args=(frame,)).start()

    # --- LOGLARNI YAZISH ---
    def write_log_to_file(self, text):
        """ Zavodda xatoni topish uchun loglarni doimiy faylga yozib borish """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")

    def log_message(self, message, color="white"):
        """ UI dagi qora ekranga chiqarish va faylga saqlash """
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.write_log_to_file(message)

if __name__ == "__main__":
    app = PLCTesterApp()
    app.mainloop()