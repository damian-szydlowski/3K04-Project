import serial
import serial.tools.list_ports
import struct
import time

class SerialManager:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.baudrate = baudrate
        self.HEADER = b'\x16'
        
        # --- DEFINITIONS ---
        # 11 Bytes for LED/Basic commands
        self.FMT_11_BYTES = '<BBBBBfH'
        
        # 18 Bytes for Parameter Setting (Header+Cmd + 16 Data Bytes)
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
        if not self.ser or not self.ser.is_open:
            return False
        try:
            # Map simple color code to RGB
            red = 1 if color_code == 1 else 0
            green = 1 if color_code == 2 else 0
            blue = 1 if color_code == 3 else 0
            data = struct.pack(self.FMT_11_BYTES, 0x16, 0x55, red, green, blue, 0.5, 200)
            self.ser.write(data)
            return True
        except Exception:
            return False

    def get_echo(self):
        """LED Echo (9 bytes) - Returns Dict"""
        if not self.ser or not self.ser.is_open:
            return None
        try:
            self.ser.reset_input_buffer()
            self.ser.write(struct.pack(self.FMT_11_BYTES, 0x16, 0x22, 0,0,0,0.0,0))
            resp = self.ser.read(9)
            if len(resp) != 9: return None
            u = struct.unpack('<BBBHf', resp)
            return {"red": u[0], "green": u[1], "blue": u[2], "switch_time": u[3], "off_time": u[4]}
        except Exception:
            return None

    def get_cardiac_echo(self):
        """
        Sends 18 bytes (Header+Cmd+Zeros) to trigger Echo.
        Expects 16 bytes back based on image_da8144.png.
        """
        if not self.ser or not self.ser.is_open:
            return {"error": "Not Connected"}

        try:
            # 1. Clear buffer
            self.ser.reset_input_buffer()

            # 2. Send Trigger: 0x16, 0x22, + 16 zeros
            req_data = struct.pack(self.FMT_18_BYTES, 0x16, 0x22, *([0]*16))
            self.ser.write(req_data)

            # 3. Read Response: Expecting 16 bytes (Data only, no header from board)
            response = self.ser.read(16)
            
            if len(response) != 16:
                return {"error": f"Timeout/Partial Data.\nRx: {len(response)} bytes\nEx: 16 bytes"}

            # 4. Unpack 16 bytes (Top to Bottom from image_da8144.png)
            # All are uint8 (B)
            u = struct.unpack('<BBBBBBBBBBBBBBBB', response)
            
            # 5. Reverse Scaling
            params = {
                "mode": u[0],              # 1
                "resp_fact": u[1],         # 2
                "recov": u[2],             # 3
                "react": u[3],             # 4
                "msr": u[4],               # 5
                "lrl": u[5],               # 6
                "act_thresh": u[6],        # 7
                "v_sens": u[7] / 10.0,     # 8  (Scale / 10)
                "v_ref": u[8] * 10,        # 9  (Scale * 10)
                "v_pw": u[9],              # 10
                "v_amp": u[10] / 10.0,     # 11 (Scale / 10)
                "a_sens": u[11] / 10.0,    # 12 (Scale / 10)
                "a_ref": u[12] * 10,       # 13 (Scale * 10)
                "a_pw": u[13],             # 14
                "a_amp": u[14] / 10.0,     # 15 (Scale / 10)
                "hyst": u[15]              # 16
            }
            return params

        except Exception as e:
            return {"error": f"Comm Error:\n{str(e)}"}

    def send_params(self, params: dict):
        """Sends 18 bytes. Order matches Simulink Input Ports 1-16."""
        if not self.ser or not self.ser.is_open:
            return False
        try:
            # Packing Order: Header(1), Cmd(1), Data(16)
            # Matching the Simulink Input Order
            data = struct.pack(self.FMT_18_BYTES, 
                               0x16, 0x55, 
                               int(params.get("mode", 0)),          # 1
                               int(params.get("resp_fact", 0)),     # 2
                               int(params.get("recov", 0)),         # 3
                               int(params.get("react_time", 0)),    # 4
                               int(params.get("msr", 0)),           # 5
                               int(params.get("lrl", 60)),          # 6
                               int(params.get("act_thresh", 0)),    # 7
                               int(params.get("v_sens", 0) * 10),   # 8  (Scaled x10)
                               int(params.get("v_ref", 0) / 10),    # 9  (Scaled /10)
                               int(params.get("v_pw", 0)),          # 10
                               int(params.get("v_amp", 0) * 10),    # 11 (Scaled x10)
                               int(params.get("a_sens", 0) * 10),   # 12 (Scaled x10)
                               int(params.get("a_ref", 0) / 10),    # 13 (Scaled /10)
                               int(params.get("a_pw", 0)),          # 14
                               int(params.get("a_amp", 0) * 10),    # 15 (Scaled x10)
                               int(params.get("hyst", 0)))          # 16

            self.ser.write(data)
            print(f"Sent Params (18 bytes): {data.hex().upper()}")
            return True
        except Exception as e:
            print(f"Param Send Error: {e}")
            return False