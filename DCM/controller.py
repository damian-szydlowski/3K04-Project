import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List

# Data models
from models.user_model import UserModel, MAX_USERS
from models.pacing_model import PacingModel
from models.serial_comms import SerialManager

# Views
from views.login_views import Welcome, Register
from views.main_view import MainFrame, DataEntry, DebugLED

# Appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DCMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DCM - Device Controller-Monitor")

        # Window size and position
        window_width = int(self.winfo_screenwidth() * 0.5)
        window_height = int(self.winfo_screenheight() * 0.5)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(True, True)
        self.minsize(800, 500)

        # Models and session
        self.user_model = UserModel()
        self.pacing_model = PacingModel()
        self.serial_manager = SerialManager() 
        self.current_user: str | None = None

        # --- ACCESSIBILITY STATE ---
        self.current_font_size = 14  # Default size
        self.MIN_FONT_SIZE = 10
        self.MAX_FONT_SIZE = 24

        # Comms state
        self.connected: bool = False
        self.current_device_id: str | None = None
        self.last_interrogated_device_id: str | None = None

        # Container + screens
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[str, ctk.CTkFrame] = {}
        for F in (Welcome, Register, MainFrame, DataEntry, DebugLED):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Welcome")

    # ---------------- Accessibility ----------------
    def increase_font_size(self):
        if self.current_font_size < self.MAX_FONT_SIZE:
            self.current_font_size += 2
            self._update_views_font()

    def decrease_font_size(self):
        if self.current_font_size > self.MIN_FONT_SIZE:
            self.current_font_size -= 2
            self._update_views_font()

    def _update_views_font(self):
        """Notifies all views to update their widgets to the new size"""
        for frame in self.frames.values():
            if hasattr(frame, "update_font_size"):
                frame.update_font_size(self.current_font_size)

    # ---------------- Navigation ----------------
    def show_frame(self, frame_name: str):
        frame = self.frames[frame_name]
        if frame_name == "Welcome":
            frame.refresh_user_count()
        if frame_name == "MainFrame":
            self._push_comm_status_to_ui()
        frame.tkraise()

    # ---------------- Authentication ----------------
    def handle_register(self, username: str, password: str):
        ok, msg = self.user_model.register_user(username, password)
        if ok:
            messagebox.showinfo("Success", msg)
            self.show_frame("Welcome")
        else:
            messagebox.showerror("Error", msg)

    def handle_login(self, username: str, password: str):
        ok, msg = self.user_model.authenticate(username, password)
        if ok:
            self.current_user = username
            self.frames["MainFrame"].set_user(username)
            self.frames["DataEntry"].set_user(username)
            self._push_comm_status_to_ui()
            self.show_frame("MainFrame")
        else:
            messagebox.showerror("Error", msg)

    def handle_logout(self):
        self.current_user = None
        self.frames["MainFrame"].set_user("")
        self.frames["DataEntry"].set_user("")
        self.disconnect_serial()
        self.show_frame("Welcome")

    # ---------------- Parameter entry ----------------
    def show_data_entry_page(self, mode: str):
        if not self.current_user:
            messagebox.showerror("Error", "Not logged in.")
            return
        settings = self.pacing_model.load_settings(self.current_user, mode)
        self.frames["DataEntry"].set_pacing_mode(mode, settings)
        self.show_frame("DataEntry")

    def handle_save_settings(self, mode: str, data: Dict[str, str]):
        if not self.current_user:
            messagebox.showerror("Error", "Not logged in.")
            return
        
        # 1. Save locally
        self.pacing_model.save_settings(self.current_user, mode, data)
        messagebox.showinfo("Success", f"{mode} settings have been saved.")

        # 2. Send to Hardware
        if self.connected:
            self._send_settings_to_board(mode, data)
        else:
            messagebox.showwarning("Comm Warning", "Settings saved locally, but board is NOT connected.")
        
        self.show_frame("MainFrame")

    def _send_settings_to_board(self, mode_str: str, data: Dict[str, str]):
        mode_map = {"AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4} 
        mode_int = mode_map.get(mode_str, 0)

        try:
            lrl = int(data.get("Lower Rate Limit", 60))
            url = int(data.get("Upper Rate Limit", 120))
            ampl = float(data.get("Atrial Amplitude", 0) or data.get("Ventricular Amplitude", 0))
            width = float(data.get("Atrial Pulse Width", 0) or data.get("Ventricular Pulse Width", 0))

            success = self.serial_manager.send_params(mode_int, lrl, url, ampl, width)
            if not success:
                messagebox.showerror("Comm Error", "Failed to send parameters to board.")
        except ValueError:
            messagebox.showerror("Data Error", "Invalid number format in settings.")

    def send_debug_color(self, color_code: int):
        """Sends command to light up LED if connected and verified."""
        # --- NEW CHECK: Must be connected AND verified as FRDM-K64F ---
        if not self.connected or self.current_device_id != "FRDM-K64F":
            messagebox.showwarning("Access Denied", "Debug mode requires a verified FRDM-K64F connection.")
            return
        
        success = self.serial_manager.send_color_command(color_code)
        if not success:
            messagebox.showerror("Comm Error", "Failed to send LED command.")

    # ---------------- Comms helpers ----------------
    def _push_comm_status_to_ui(self):
        if "MainFrame" in self.frames:
            self.frames["MainFrame"].update_comm_status(self.connected, self.current_device_id)

    def _set_comm_state(self, connected: bool, device_id: str | None):
        self.connected = connected
        self.current_device_id = device_id if connected else None
        self._push_comm_status_to_ui()

        if connected:
            if self.last_interrogated_device_id is not None and device_id != self.last_interrogated_device_id:
                messagebox.showwarning(
                    "Device Change Detected",
                    f"A different pacemaker is now in range.\n"
                    f"Previous: {self.last_interrogated_device_id}\nCurrent: {device_id}"
                )
            self.last_interrogated_device_id = device_id

    # ---------------- SERIAL ACTIONS ----------------
    
    def get_serial_ports(self) -> List[str]:
        return self.serial_manager.get_ports()

    def connect_serial(self, port_name_display: str):
        if not self.current_user:
            messagebox.showerror("Error", "Please log in first.")
            return

        # --- SAFETY CHECK ---
        safe_keywords = ["mbed", "OpenSDA", "NXP", "DAPLink", "JLink", "Segger"]
        
        is_likely_safe = any(keyword.lower() in port_name_display.lower() for keyword in safe_keywords)

        if not is_likely_safe:
            # Warn the user about system ports
            response = messagebox.askyesno(
                "Potential Wrong Device", 
                f"The device '{port_name_display}' does not look like a pacemaker board.\n\n"
                "Do you want to connect anyway?"
            )
            if not response:
                return # User cancelled

        # Proceed to connect
        success = self.serial_manager.connect(port_name_display)
        
        if success:
            if is_likely_safe:
                device_id = "FRDM-K64F"
            else:
                device_id = "Unverified Device" 
            
            self._set_comm_state(True, device_id)
            messagebox.showinfo("Connected", f"Successfully connected to {port_name_display}")
        else:
            self._set_comm_state(False, None)
            messagebox.showerror("Connection Failed", f"Could not open {port_name_display}")

    def disconnect_serial(self):
        self._set_comm_state(False, None)
        self.serial_manager.disconnect()

    # ---------------- Utilities ----------------
    def get_user_count(self) -> int:
        return self.user_model.get_user_count()

    def get_max_users(self) -> int:
        return MAX_USERS