import serial
import serial.tools.list_ports
import struct
import time

class SerialManager:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.baudrate = baudrate
        self.HEADER = b'\x16'
        
        self.CMD_SET_PARAM = b'\x55'  # Updates variables
        self.CMD_ECHO_PARAM = b'\x22' # Triggers send_params()

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

    def send_params(self, mode: int, lrl: int, url: int, ampl: float, width: float):
        if not self.ser or not self.ser.is_open:
            return False

        try:
            # Map Mode to Color Flags for the Lab
            # Note: Due to your chart logic, Red MUST be 1 to reach Green/Blue
            red = 1 if mode == 1 else 0
            green = 1 if mode == 2 else 0
            blue = 1 if mode == 3 else 0
            
            off_time = float(lrl) / 100.0 
            switch_time = int(width)      
            
            return self._send_packet(self.CMD_SET_PARAM, red, green, blue, off_time, switch_time)
                
        except Exception as e:
            print(f"Packing/Sending Error: {e}")
            return False

    def send_color_command(self, color_code: int):
        if not self.ser or not self.ser.is_open:
            return False
        try:
            red = 1 if color_code == 1 else 0
            green = 1 if color_code == 2 else 0
            blue = 1 if color_code == 3 else 0
            
            off_time = 1.0       
            switch_time = 500    
            
            return self._send_packet(self.CMD_SET_PARAM, red, green, blue, off_time, switch_time)
            
        except Exception as e:
            print(f"LED Error: {e}")
            return False

    def _send_packet(self, cmd, red, green, blue, off_time, switch_time):
        """
        Helper to send the exact 11-byte packet.
        [Header(1)] [Cmd(1)] [Red(1)] [Green(1)] [Blue(1)] [OffTime(4)] [SwitchTime(2)]
        """
        data = struct.pack('<BBBBBfH', 
                           0x16, 
                           ord(cmd), 
                           int(red), 
                           int(green), 
                           int(blue), 
                           float(off_time), 
                           int(switch_time))
        
        self.ser.write(data)
        print(f"Sent Packet ({len(data)} bytes): {data.hex().upper()}")
        
        # Request Echo if we just set params
        if cmd == self.CMD_SET_PARAM:
            # Increased delay to 0.2s to let Stateflow process the transition
            time.sleep(0.2)
            self._request_echo()
            
        return True

    def _request_echo(self):
        # Send Echo Request (0x22)
        print("Sending Echo Request...")
        # Using dummy values for the data part
        self._send_packet(self.CMD_ECHO_PARAM, 0, 0, 0, 0.0, 0)
        
        response = self.read_echo()
        if response:
            print(f"Verified! Board echoed: {response}")
        else:
            print("Warning: No echo received.")

    def read_echo(self):
        if not self.ser or not self.ser.is_open:
            return None

        try:
            # Increased read wait time
            time.sleep(0.2) 
            
            waiting = self.ser.in_waiting
            print(f"Bytes in buffer: {waiting}") # DEBUG PRINT
            
            if waiting >= 11: 
                raw_data = self.ser.read(11)
                unpacked = struct.unpack('<BBBff', raw_data)
                return unpacked
            elif waiting > 0:
                # Read whatever is there to clear buffer and show user
                partial = self.ser.read(waiting)
                print(f"Partial data received: {partial.hex().upper()}")
                return None
            
            return None
        except Exception as e:
            print(f"Read Echo Error: {e}")
            return None