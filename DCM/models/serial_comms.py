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
        # Header(1) + Cmd(1) + R(1) + G(1) + B(1) + OffTime(4) + SwitchTime(2)
        self.FMT_11_BYTES = '<BBBBBfH'
        
        # 46 Bytes for Cardiac Params (Future use)
        self.FMT_46_BYTES = '<BBHHHHffHHHffHHfHHH' 

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
        """Sends the SET_PARAM packet (Cmd 0x55)."""
        if not self.ser or not self.ser.is_open:
            return False
        try:
            red = 1 if color_code == 1 else 0
            green = 1 if color_code == 2 else 0
            blue = 1 if color_code == 3 else 0
            # Default values for testing
            off_time = 0.5 
            switch_time = 200

            # Cmd 0x55 triggers SET_PARAM state in your diagram
            data = struct.pack(self.FMT_11_BYTES, 
                               0x16, 0x55, red, green, blue, off_time, switch_time)
            
            self.ser.write(data)
            return True
        except Exception as e:
            print(f"LED Error: {e}")
            return False

    def get_echo(self):
        """
        Sends ECHO_PARAM command (0x22) and reads back 9 bytes.
        Returns: Dict of values or None if failed.
        """
        if not self.ser or not self.ser.is_open:
            return None

        try:
            # 1. Send Request: Cmd 0x22 triggers ECHO_PARAM state.
            # We still send 11 bytes because the board's receive logic likely expects a full packet.
            req_data = struct.pack(self.FMT_11_BYTES, 
                                   0x16, 0x22, 0, 0, 0, 0.0, 0)
            self.ser.reset_input_buffer() 
            self.ser.write(req_data)

            # 2. Read Response: Expecting 9 bytes back (No Header, No Cmd)
            # Structure from Mux in Simulink: Red(1), Green(1), Blue(1), SwitchTime(2), OffTime(4)
            response = self.ser.read(9)
            
            if len(response) != 9:
                print(f"Echo Error: Received {len(response)} bytes, expected 9.")
                return None

            # 3. Unpack
            # < = Little Endian
            # B = uchar (1 byte) x3
            # H = ushort (2 bytes) -> Switch Time
            # f = float (4 bytes) -> Off Time
            unpacked = struct.unpack('<BBBHf', response)
            
            return {
                "red": unpacked[0],
                "green": unpacked[1],
                "blue": unpacked[2],
                "switch_time": unpacked[3],
                "off_time": unpacked[4]
            }

        except Exception as e:
            print(f"Echo Comm Error: {e}")
            return None

    def send_params(self, mode: int, lrl: int, url: int, ampl: float, width: float):
        """
        FUTURE FEATURE: Sends 46 bytes.
        WARNING: Do not use this if the board expects 11 bytes. It will desync the UART.
        """
        if not self.ser or not self.ser.is_open:
            return False

        try:
            # Logic to map GUI inputs to struct fields
            a_pw = int(width) if mode in [1, 3] else 0
            v_pw = int(width) if mode in [2, 4] else 0
            a_amp = float(ampl) if mode in [1, 3] else 0.0
            v_amp = float(ampl) if mode in [2, 4] else 0.0

            # Defaults
            a_ref, v_ref, delay = 250, 320, 0
            a_sens, v_sens = 0.0, 0.0
            recov, resp_fact, max_sens = 0, 0, 0
            act_thresh, react_time = 0.0, 0

            # Pack 46 bytes - Now using the corrected 19-item format string
            data = struct.pack(self.FMT_46_BYTES, 
                               0x16, 0x55, 
                               int(mode), a_pw, v_pw, int(lrl),
                               float(a_amp), float(v_amp),
                               int(a_ref), int(v_ref), int(delay),
                               float(a_sens), float(v_sens),
                               int(recov), int(resp_fact), int(max_sens),
                               float(act_thresh), int(react_time),
                               int(url)) # <--- This was the 19th item missing in your format string

            self.ser.write(data)
            print(f"Sent Param Packet (46 bytes): {data.hex().upper()}")
            return True

        except struct.error as e:
            print(f"Struct Error (Check format string vs arguments): {e}")
            return False
        except Exception as e:
            print(f"Param Send Error: {e}")
            return False