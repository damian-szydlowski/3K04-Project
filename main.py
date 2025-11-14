import serial
import time
import sys
import struct # Import the struct library for packing bytes

# --- Configuration (Based on Tutorial3.pdf) ---
PORT = '/dev/ttyACM0'  # The port you found
BAUDRATE = 115200       # Set to 115200 as per PDF (Page 11)
TIMEOUT = 1.0           # Read timeout in seconds

# --- Packet Constants (Based on Table 2, Page 15) ---
SYNC_BYTE = 0x16
FN_CODE_SET_PARAMS = 0x55
FN_CODE_ECHO_PARAMS = 0x22

def initialize_port(port, baudrate, timeout):
    """
    Initializes and opens the serial port.
    Returns the serial port object or None if an error occurs.
    """
    try:
        # Open the serial port
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        # Wait a moment for the device to settle
        # Some devices (like Arduinos/FRDM-K64F) reset when the port is opened
        time.sleep(2) 
        
        if ser.is_open:
            print(f"Successfully opened port: {ser.name} at {ser.baudrate} baud")
            return ser
        else:
            print(f"Failed to open port: {port}")
            return None

    except serial.SerialException as e:
        print(f"Error opening port {port}: {e}")
        if "Permission denied" in str(e):
            print("\n--- PERMISSION DENIED ---")
            print(f"Try running: sudo usermod -a -G dialout $USER")
            print("Then log out and log back in for the change to take effect.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def create_packet(fn_code, red, green, blue, off_time, switch_time):
    """
    Packs data into an 11-byte packet according to the tutorial's
    specification (Table 2, Page 15).
    
    Format:
    < (Little-Endian)
    B (uint8) - SYNC (0x16)
    B (uint8) - FN_CODE (0x55 or 0x22)
    B (uint8) - RED_ENABLE
    B (uint8) - GREEN_ENABLE
    B (uint8) - BLUE_ENABLE
    f (single, 4-bytes) - OFF_TIME
    H (uint16, 2-bytes) - SWITCH_TIME
    """
    try:
        # The format string for the 11-byte packet
        # < = Little-Endian
        # B = uint8 (1 byte)
        # f = float (4 bytes)
        # H = unsigned short (2 bytes)
        # 5x 'B's, 1x 'f', 1x 'H'
        packet_format = "<BBBBBfH"
        
        packet_bytes = struct.pack(packet_format,
            SYNC_BYTE,
            fn_code,
            red,
            green,
            blue,
            off_time,
            switch_time
        )
        
        # Verify packet length
        if len(packet_bytes) != 11:
            print(f"Error: Packed packet is {len(packet_bytes)} bytes, expected 11.")
            return None
            
        return packet_bytes
        
    except struct.error as e:
        print(f"Error packing data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during packet creation: {e}")
        return None

def write_packet_to_port(ser, packet_bytes):
    """
    Writes a pre-packed byte packet to the serial port.
    """
    if ser and ser.is_open and packet_bytes:
        try:
            ser.write(packet_bytes)
            # Print the sent bytes as a hex string for debugging
            hex_string = ' '.join(f'{b:02x}' for b in packet_bytes)
            print(f"Sent {len(packet_bytes)} bytes: {hex_string}")
        except serial.SerialException as e:
            print(f"Error writing to port: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during write: {e}")

def send_echo_request(ser):
    """
    Creates and sends an "ECHO_PARAM" (0x22) packet.
    This asks the device to send its current parameters back.
    The dummy values (0) are just placeholders to fill the 11-byte packet.
    """
    print("\n--- Creating 'ECHO_PARAM' (start) packet ---")
    echo_packet = create_packet(
        FN_CODE_ECHO_PARAMS,
        0, # dummy red
        0, # dummy green
        0, # dummy blue
        0.0, # dummy off_time
        0  # dummy switch_time
    )
    
    if echo_packet:
        write_packet_to_port(ser, echo_packet)
    else:
        print("Failed to create echo packet.")

def read_from_port(ser):
    """
    Reads raw bytes from the serial port.
    This is better than readline() for non-text protocols.
    """
    if not ser or not ser.is_open:
        return

    try:
        # Check if there is data in the input buffer
        if ser.in_waiting > 0:
            # Read all available bytes
            byte_data = ser.read(ser.in_waiting)
            
            if byte_data:
                # Print the received bytes as a hex string for debugging
                hex_string = ' '.join(f'{b:02x}' for b in byte_data)
                print(f"Received {len(byte_data)} bytes: {hex_string}")
                
    except serial.SerialException as e:
        print(f"Error reading from port: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during read: {e}")

def main():
    """
    Main function to run the UART communication.
    Sends a packet defined by the tutorial.
    """
    ser = None # Initialize ser to None
    try:
        ser = initialize_port(PORT, BAUDRATE, TIMEOUT)
        
        if ser is None:
            print("Exiting program.")
            sys.exit(1) # Exit if port initialization failed

        # --- Send an "ECHO_PARAM" request to start communication ---
        # This asks the device to send its current parameters
        send_echo_request(ser)
        
        # Wait a moment for the device to respond
        print("Waiting 1 second for echo response...")
        time.sleep(1)
        read_from_port(ser) # Check for the response

        # --- Example: Send a "SET_PARAM" packet ---
        # These are the values from the "INITIAL" state (Page 17)
        # but you can change them.
        red_val = 1       # uint8 (0 or 1)
        green_val = 1     # uint8 (0 or 1)
        blue_val = 0      # uint8 (0 or 1)
        off_time_val = 0.5  # single (float)
        switch_time_val = 200 # uint16
        
        print(f"\n--- Creating 'SET_PARAM' packet ---")
        print(f"  Values: RED={red_val}, GREEN={green_val}, BLUE={blue_val}, OFF_TIME={off_time_val}, SWITCH_TIME={switch_time_val}")
        
        packet_to_send = create_packet(
            FN_CODE_SET_PARAMS,
            red_val,
            green_val,
            blue_val,
            off_time_val,
            switch_time_val
        )

        if packet_to_send:
            write_packet_to_port(ser, packet_to_send)
        else:
            print("Failed to create packet. Not sending.")

        # Listen for responses in a loop
        print("\nListening for incoming data... (Press Ctrl+C to stop)")
        while True:
            read_from_port(ser)
            # Add a small delay to prevent high CPU usage
            time.sleep(0.01) 

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        
    finally:
        # This block ALWAYS runs, ensuring the port is closed
        if ser and ser.is_open:
            ser.close()
            print(f"Closed port: {ser.name}")

if __name__ == "__main__":
    main()