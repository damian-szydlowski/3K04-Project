import serial
import serial.tools.list_ports
import struct


class SerialManager:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.baudrate = baudrate
        self.HEADER = b'\x16'
        self.FMT_11_BYTES = '<BBBBBfH'
        self.FMT_18_BYTES = '<BBBBBBBBBBBBBBBBBB'

        # Each streaming egram frame is 4 bytes:
        # 2 bytes m_vraw, 2 bytes f_marker
        self.EGRAM_FRAME_SIZE = 4

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

    def read_egram_sample(self):
        """
        Try to read one egram sample from the UART.

        New packet format (4 bytes total, little endian):
          [0:2]  low  16 bits  -> marker (uint16)
          [2:4]  high 16 bits  -> raw mV value (0..5000) as uint16

        Returns (raw_mV, marker_str) or None if no full frame is available.
        """
        if not self.ser or not self.ser.is_open:
            print("[Serial] read_egram_sample called but serial is not open")
            return None

        if self.ser.in_waiting < self.EGRAM_FRAME_SIZE:
            return None

        try:
            frame = self.ser.read(self.EGRAM_FRAME_SIZE)
            print(f"[Serial] Raw frame bytes: {frame.hex(' ')}")

            if len(frame) != self.EGRAM_FRAME_SIZE:
                print(f"[Serial] Short frame, len={len(frame)}")
                return None

            # Split according to new spec
            marker_u16 = int.from_bytes(frame[0:2], byteorder="little", signed=False)
            raw_u16    = int.from_bytes(frame[2:4], byteorder="little", signed=False)

            # Raw is already 0..5000 mV according to your spec
            raw_mv = raw_u16

            # Try to interpret marker as two ASCII chars first
            b0, b1 = frame[0], frame[1]
            if 32 <= b0 <= 126 and 32 <= b1 <= 126:
                try:
                    marker = bytes([b0, b1]).decode("ascii")
                except UnicodeDecodeError:
                    marker = "--"
            else:
                # Fallback numeric code in low byte of marker_u16
                code = marker_u16 & 0xFF
                if code == 0:
                    marker = "--"
                elif code == 1:
                    marker = "VS"
                elif code == 2:
                    marker = "VP"
                elif code == 3:
                    marker = "()"
                else:
                    print(f"[Serial] Unknown marker code {marker_u16}, forcing '--'")
                    marker = "--"

            print(f"[Serial] Parsed sample raw_mv={raw_mv}, marker={marker}")
            return raw_mv, marker

        except Exception as e:
            print(f"[Serial] Egram read error: {e}")
            return None

    def start_egram_stream(self) -> bool:
        """
        Send an egram START command so the pacemaker begins streaming
        4 byte frames with m_vraw plus marker.
        Here I use command byte 0x33. Change it if your Simulink model
        uses a different command code.
        """
        if not self.ser or not self.ser.is_open:
            print("[Serial] Cannot start egram, port is not open")
            return False

        try:
            frame = struct.pack(self.FMT_18_BYTES, 0x16, 0x33, *([0] * 16))
            print(f"[Serial] Sending egram START: {frame.hex().upper()}")
            self.ser.write(frame)
            return True
        except Exception as e:
            print(f"[Serial] Egram start send error: {e}")
            return False

    def stop_egram_stream(self) -> bool:
        """
        Send an egram STOP command so the pacemaker stops streaming.
        Here I use command byte 0x34. Change it if your Simulink model
        uses a different command code.
        """
        if not self.ser or not self.ser.is_open:
            print("[Serial] Cannot stop egram, port is not open")
            return False

        try:
            frame = struct.pack(self.FMT_18_BYTES, 0x16, 0x34, *([0] * 16))
            print(f"[Serial] Sending egram STOP: {frame.hex().upper()}")
            self.ser.write(frame)
            return True
        except Exception as e:
            print(f"[Serial] Egram stop send error: {e}")
            return False
