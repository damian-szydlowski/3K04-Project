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

    def get_echo(self):
        """LED Echo - Returns Dict"""
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
        """
        Sends 18 bytes. Expects 16 bytes back.
        Mapping matches 'image_da8144.png' (Output Mux).
        """
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
            
            # Map based on Echo Output Order (Top -> Bottom)
            return {
                "raw": raw_hex,
                "mode": u[0],              # 1
                "resp_fact": u[1],         # 2
                "recov": u[2],             # 3
                "react": u[3],             # 4
                "msr": u[4],               # 5
                "lrl": u[5],               # 6
                "act_thresh": u[6],        # 7
                "v_sens": u[7] / 10.0,     # 8
                "v_ref": u[8] * 10,        # 9
                "v_pw": u[9],              # 10
                "v_amp": u[10] / 10.0,     # 11
                "a_sens": u[11] / 10.0,    # 12
                "a_ref": u[12] * 10,       # 13
                "a_pw": u[13],             # 14
                "a_amp": u[14] / 10.0,     # 15
                "hyst": u[15]              # 16
            }
        except Exception as e:
            return {"error": f"Comm Error:\n{str(e)}"}

    def send_params(self, params: dict):
        """
        Sends 18 bytes. 
        Mapping matches 'image_db0126.png' (Stateflow Parsing).
        """
        if not self.ser or not self.ser.is_open: return False
        try:
            # Order: Mode, A_PW, V_PW, LRL, A_Amp, V_Amp, A_Ref, V_Ref, ...
            data = struct.pack(self.FMT_18_BYTES, 
                               0x16, 0x55, 
                               int(params.get("mode", 0)),          # rxdata(3)
                               int(params.get("a_pw", 0) * 100),          # rxdata(4)
                               int(params.get("v_pw", 0) * 100),          # rxdata(5)
                               int(params.get("lrl", 60)),          # rxdata(6)
                               int(params.get("a_amp", 0) * 10),    # rxdata(7)
                               int(params.get("v_amp", 0) * 10),    # rxdata(8)
                               int(params.get("a_ref", 0) / 10),    # rxdata(9)
                               int(params.get("v_ref", 0) / 10),    # rxdata(10)
                               int(params.get("a_sens", 0) * 10),   # rxdata(11)
                               int(params.get("v_sens", 0) * 10),   # rxdata(12)
                               int(params.get("recov", 0)),         # rxdata(13)
                               int(params.get("resp_fact", 0)),     # rxdata(14)
                               int(params.get("msr", 0)),           # rxdata(15)
                               int(params.get("act_thresh", 0)),    # rxdata(16)
                               int(params.get("react_time", 0)),    # rxdata(17)
                               int(params.get("hyst", 0)))          # rxdata(18)
            self.ser.write(data)
            return True
        except Exception: return False