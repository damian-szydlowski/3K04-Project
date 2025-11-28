import serial
import serial.tools.list_ports
import struct
import time

class SerialManager:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.baudrate = baudrate
        self.HEADER = b'\x16'
        self.FMT_11_BYTES = '<BBBBBfH'
        self.FMT_18_BYTES = '<BBBBBBBBBBBBBBBBBB' 

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [f"{p.device}: {p.description}" if p.description else p.device for p in ports]

    def connect(self, port_name_str):
        actual_port = port_name_str.split(":")[0] if ":" in port_name_str else port_name_str
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(actual_port, self.baudrate, timeout=1)
            self.ser.reset_input_buffer()
            return True
        except serial.SerialException as e:
            print(f"Connection Error: {e}")
            return False

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None

    def send_color_command(self, color_code: int):
        if not self.ser or not self.ser.is_open: return False
        try:
            data = struct.pack(self.FMT_11_BYTES, 0x16, 0x55, 
                               1 if color_code==1 else 0, 
                               1 if color_code==2 else 0, 
                               1 if color_code==3 else 0, 0.5, 200)
            self.ser.write(data)
            return True
        except Exception: return False

    def send_params(self, params: dict):
        if not self.ser or not self.ser.is_open: return False
        try:
            data = struct.pack(self.FMT_18_BYTES, 
                               0x16, 0x55, 
                               int(params.get("mode", 0)),
                               int(params.get("a_pw", 0) * 100),
                               int(params.get("v_pw", 0) * 100),
                               int(params.get("lrl", 60)),
                               int(params.get("a_amp", 0) * 10),
                               int(params.get("v_amp", 0) * 10),
                               int(params.get("a_ref", 0) / 10),
                               int(params.get("v_ref", 0) / 10),
                               int(params.get("a_sens", 0) * 10),
                               int(params.get("v_sens", 0) * 10),
                               int(params.get("recov", 0)),
                               int(params.get("resp_fact", 0)),
                               int(params.get("msr", 0)),
                               int(params.get("act_thresh", 0)),
                               int(params.get("react_time", 0)),
                               int(params.get("hyst", 0)))
            self.ser.write(data)
            return True
        except Exception: return False

    def get_echo(self):
        if not self.ser or not self.ser.is_open: return None
        try:
            self.ser.reset_input_buffer()
            self.ser.write(struct.pack(self.FMT_11_BYTES, 0x16, 0x22, 0,0,0,0.0,0))
            resp = self.ser.read(9)
            if len(resp) != 9: return None
            u = struct.unpack('<BBBHf', resp)
            return {"red": u[0], "green": u[1], "blue": u[2], "switch_time": u[3], "off_time": u[4]}
        except Exception: return None

    def get_cardiac_echo(self):
        if not self.ser or not self.ser.is_open:
            return {"error": "Not Connected"}
        try:
            self.ser.reset_input_buffer()
            self.ser.write(struct.pack(self.FMT_18_BYTES, 0x16, 0x22, *([0]*16)))
            response = self.ser.read(16)
            raw_hex = response.hex().upper()
            if len(response) != 16:
                return {"error": f"Timeout.\nRx: {len(response)} B\nRaw: {raw_hex}"}
            u = struct.unpack('<BBBBBBBBBBBBBBBB', response)
            return {
                "raw": raw_hex, "mode": u[0], "resp_fact": u[1], "recov": u[2], "react": u[3], "msr": u[4], "lrl": u[5], "act_thresh": u[6], "v_sens": u[7] / 10.0, "v_ref": u[8] * 10, "v_pw": u[9], "v_amp": u[10] / 10.0, "a_sens": u[11] / 10.0, "a_ref": u[12] * 10, "a_pw": u[13], "a_amp": u[14] / 10.0, "hyst": u[15]
            }
        except Exception as e:
            return {"error": f"Comm Error:\n{str(e)}"}

    def start_egram_stream(self):
        """Sends 16 bytes: 16 (Head), 51 (Code), + 14 Zeros."""
        if not self.ser or not self.ser.is_open: return False
        try:
            self.ser.reset_input_buffer()
            # 2 bytes command + 14 bytes pad = 16 Bytes Total
            self.ser.write(struct.pack('<BB14x', 0x16, 0x33)) 
            print("[Serial] Sent Start Egram (16 bytes)")
            return True
        except Exception as e: 
            print(f"[Serial] Error starting stream: {e}")
            return False

    def stop_egram_stream(self):
        """Sends 16 bytes: 16 (Head), 52 (Code), + 14 Zeros."""
        if not self.ser or not self.ser.is_open: return False
        try:
            self.ser.write(struct.pack('<BB14x', 0x16, 0x34))
            print("[Serial] Sent Stop Egram (16 bytes)")
            return True
        except Exception as e:
            print(f"[Serial] Error stopping stream: {e}")
            return False

    def read_egram_sample(self):
        """
        SYNC READ (16 Bytes Total):
        1. Reads until Header (0x01) is found.
        2. Reads next 15 bytes.
        Structure: [01] [7 Pad] [4 Atr] [4 Vent]
        """
        if not self.ser or not self.ser.is_open: return None
        
        # Need at least 16 bytes
        if self.ser.in_waiting < 16: return None

        try:
            # --- SYNC LOOP ---
            while True:
                if self.ser.in_waiting < 16: return None
                
                header = self.ser.read(1)
                
                if header == b'\x01':
                    # Found header, read rest of packet (15 bytes)
                    payload = self.ser.read(15)
                    break
            
            # --- DEBUG: Print Raw Hex ---
            total_packet = header + payload
            print(f"[Raw] {total_packet.hex().upper()}")

            # Unpack Payload (15 bytes):
            # 7x = Skip 7 bytes (Padding)
            # f  = Float (Atrial)
            # f  = Float (Ventricular)
            val_atr, val_vent = struct.unpack('<7xff', payload)
            
            return (val_atr, val_vent)

        except Exception as e:
            print(f"[Serial] Egram read error: {e}")
            return None