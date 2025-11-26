import serial
import serial.tools.list_ports
import struct
import time

class SerialManager:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.baudrate = baudrate
        self.HEADER = b'\x16'
        
        # Commands matching your Stateflow Chart
        self.CMD_SET_PARAM = b'\x55'  # Matches rxdata(2) == 0x55
        self.CMD_ECHO_PARAM = b'\x22' # Matches rxdata(2) == 0x22

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        result = []
        for port in ports:
            if port.description:
                result.append(f"{port.device}: {port.description}")
            else:
                result.append(port.device)
        return result

    def connect(self, port_name_str):
        if ":" in port_name_str:
            actual_port = port_name_str.split(":")[0] 
        else:
            actual_port = port_name_str

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(actual_port, self.baudrate, timeout=1)
            self.ser.reset_input_buffer()
            return True
        except serial.SerialException as e:
            print(f"Serial Connection Error: {e}")
            return False

    def disconnect(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception as e:
            print(f"Error closing port: {e}")
        finally:
            self.ser = None

    def send_params(self, mode: int, lrl: int, url: int, ampl: float, width: float, a_sens: float = 0.0, v_sens: float = 0.0):
        """
        Sends the new 46-byte packet matching the 'setting_parameters' chart.
        """
        if not self.ser or not self.ser.is_open:
            return False

        try:
            # --- PREPARE DATA ---
            # Since the GUI sends generic 'ampl' and 'width', we map them 
            # to Atrial or Ventricular fields based on the mode.
            
            # Modes:
            # 1 AOO, 3 AAI, 5 AOOR, 7 AAIR use atrial amplitude and pulse width
            # 2 VOO, 4 VVI, 6 VOOR, 8 VVIR use ventricular amplitude and pulse width
            atrial_modes = {1, 3, 5, 7}
            ventricular_modes = {2, 4, 6, 8}

            a_pw = int(width) if mode in atrial_modes else 0
            v_pw = int(width) if mode in ventricular_modes else 0
            a_amp = float(ampl) if mode in atrial_modes else 0.0
            v_amp = float(ampl) if mode in ventricular_modes else 0.0

            # Defaults for new parameters (not yet in GUI)
            # You can update these as you add fields to your View.
            a_ref = 250
            v_ref = 320
            delay = 0

            recov = 0
            resp_fact = 0
            max_sens = 0
            act_thresh = 0.0
            react_time = 0

            # --- PACKET STRUCTURE (46 Bytes) ---
            # Based on Chart:
            # 1: Header (B)
            # 2: Cmd (B)
            # 3-4: Mode (H - uint16)
            # 5-6: A_Pulse_Width (H)
            # 7-8: V_Pulse_Width (H)
            # 9-10: LRL (H)
            # 11-14: A_Amp (f - single)
            # 15-18: V_Amp (f)
            # 19-20: A_Refractory (H)
            # 21-22: V_Refractory (H)
            # 23-24: Delay (H)
            # 25-28: A_Sensitivity (f)
            # 29-32: V_Sensitivity (f)
            # 33-34: Recover_time (H)
            # 35-36: Response_factor (H)
            # 37-38: Maxsensorrate (H)
            # 39-42: Activity_threshold (f)
            # 43-44: Reaction_time (H)
            # 45-46: URL (H) -> Note: URL is at the very end now!

            # Format String: < BB HHHH ff HHH ff HHH f H H
            fmt = '<BBHHHHffHHHffHHfHH'
            
            data = struct.pack(fmt, 
                               0x16,                # Header
                               0x55,                # Cmd (SET)
                               int(mode),           # Mode
                               a_pw,                # A_PW
                               v_pw,                # V_PW
                               int(lrl),            # LRL
                               float(a_amp),        # A_Amp
                               float(v_amp),        # V_Amp
                               int(a_ref),          # A_Ref
                               int(v_ref),          # V_Ref
                               int(delay),          # Delay
                               float(a_sens),       # A_Sens
                               float(v_sens),       # V_Sens
                               int(recov),          # Recov
                               int(resp_fact),      # RespFact
                               int(max_sens),       # MaxSens
                               float(act_thresh),   # ActThresh
                               int(react_time),     # ReactTime
                               int(url))            # URL (Last!)

            # Send packet
            self.ser.write(data)
            print(f"Sent Packet ({len(data)} bytes): {data.hex().upper()}")

            # Unpack what we just sent so we have a typed reference
            expected = struct.unpack(fmt, data)

            # Request echo from device
            time.sleep(0.1)
            echo = self._request_echo()

            if not echo:
                print("Warning: No echo received from device.")
                return False

            # Compare all fields except header and command byte
            if echo[2:] == expected[2:]:
                print("Echo verification passed. Device stored parameters correctly.")
                return True
            else:
                print("Echo verification FAILED.")
                print("Expected:", expected)
                print("Received:", echo)
                return False

                
        except Exception as e:
            print(f"Packing/Sending Error: {e}")
            return False

    def send_color_command(self, color_code: int):
        """
        Updated to send full 46-byte packet to keep stateflow happy,
        mapping Color to Mode for visual debug if desired.
        """
        if not self.ser or not self.ser.is_open:
            return False
        try:
            # Sending a generic packet with just Mode set to color code
            # This relies on your board having logic to handle this, 
            # or just to verify connectivity.
            
            # Using defaults for everything else
            zeros_H = 0
            zeros_f = 0.0
            
            fmt = '<BBHHHHffHHHffHHfHH'
            data = struct.pack(fmt, 0x16, 0x55, int(color_code), 0,0,0, 0.0,0.0, 0,0,0, 0.0,0.0, 0,0,0, 0.0,0, 0)
            
            self.ser.write(data)
            print(f"Sent LED Packet: {data.hex().upper()}")
            return True
        except Exception as e:
            print(f"LED Error: {e}")
            return False

    def _request_echo(self):
        """
        Send an echo request packet and return the unpacked 46 byte response,
        or None if no valid response is received.
        """
        if not self.ser or not self.ser.is_open:
            return None

        fmt = '<BBHHHHffHHHffHHfHH'
        data = struct.pack(fmt, 0x16, 0x22, 0,0,0,0, 0.0,0.0, 0,0,0, 0.0,0.0, 0,0,0, 0.0,0, 0)
        try:
            self.ser.write(data)
        except Exception as e:
            print(f"Echo request write error: {e}")
            return None

        return self.read_echo()

    def read_echo(self):
        if not self.ser or not self.ser.is_open:
            return None

        try:
            time.sleep(0.2) 
            if self.ser.in_waiting >= 46: 
                raw_data = self.ser.read(46)
                # Unpack same structure
                fmt = '<BBHHHHffHHHffHHfHH'
                unpacked = struct.unpack(fmt, raw_data)
                return unpacked
            return None
        except Exception as e:
            print(f"Read Echo Error: {e}")
            return None
        
    def read_egram_samples(self, max_samples: int = 100):
        """
        Read up to max_samples Egram samples from the serial port.

        Expected line format from the pacemaker:
            t,atr,vent,marker\\n

        t       float or int, time or sample index
        atr     int or float, atrial raw value
        vent    int or float, ventricular raw value
        marker  string, for example "--", "VS", "VP", "()"
        """
        if not self.ser or not self.ser.is_open:
            return []

        samples = []
        try:
            while self.ser.in_waiting and len(samples) < max_samples:
                line = self.ser.readline()
                if not line:
                    break

                try:
                    decoded = line.decode("ascii", errors="ignore").strip()
                    if not decoded:
                        continue

                    parts = decoded.split(",")
                    if len(parts) != 4:
                        continue

                    t_val = float(parts[0])
                    atr_val = float(parts[1])
                    vent_val = float(parts[2])
                    marker = parts[3]

                    samples.append(
                        {
                            "t": t_val,
                            "atr": atr_val,
                            "vent": vent_val,
                            "marker": marker,
                        }
                    )
                except Exception:
                    # Ignore malformed lines and keep reading
                    continue
        except Exception as e:
            print(f"Egram read error: {e}")

        return samples
