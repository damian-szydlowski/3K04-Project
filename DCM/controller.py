import customtkinter as ctk
from tkinter import messagebox
from typing import Dict

# Data models
from models.user_model import UserModel, MAX_USERS
from models.pacing_model import PacingModel

# Views
from views.main_view import MainFrame, DataEntry, EgramView
from views.main_view import MainFrame, DataEntry

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
        self.current_user: str | None = None

        # Comms state (for 3.2.2 #4 and #7)
        self.connected: bool = False
        self.current_device_id: str | None = None
        self.last_interrogated_device_id: str | None = None

        # Container + screens
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[str, ctk.CTkFrame] = {}
        for F in (Welcome, Register, MainFrame, DataEntry, EgramView):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start on Welcome
        self.show_frame("Welcome")

    # ---------------- Navigation ----------------
    def show_frame(self, frame_name: str):
        frame = self.frames[frame_name]
        if frame_name == "Welcome":
            frame.refresh_user_count()
        if frame_name == "MainFrame":
            self._push_comm_status_to_ui()
        if frame_name == "EgramView":
            frame.set_device(self.current_device_id)
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
            self.frames["EgramView"].set_user(username)
            self._push_comm_status_to_ui()
            self.show_frame("MainFrame")
        else:
            messagebox.showerror("Error", msg)

    def handle_logout(self):
        self.current_user = None
        self.frames["MainFrame"].set_user("")
        self.frames["DataEntry"].set_user("")
        self.frames["EgramView"].set_user("")
        self.show_frame("Welcome")

    def start_egram(self, channel: str):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to a device.")
            return

        # Backend will:
        #   - Send a command to start streaming egram data.
        #   - Read the incoming samples and update the view.
        print(f"[DEBUG] Would start egram for channel: {channel}")
        messagebox.showinfo("Egram", f"Start egram for: {channel} (front end stub).")

    def stop_egram(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to a device.")
            return

        print("[DEBUG] Would stop egram stream.")
        messagebox.showinfo("Egram", "Stop egram (front end stub).")


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
        self.pacing_model.save_settings(self.current_user, mode, data)

        self.send_parameters_to_device(mode, data)

        messagebox.showinfo("Success", f"{mode} settings have been saved and sent to device.")
        self.show_frame("MainFrame")

    def send_parameters_to_device(self, mode: str, data: Dict[str, str]):
        "Placeholder: backend will implement building and sending the packet."
        if not self.connected:
        # Optionally warn, but avoid blocking save
            messagebox.showwarning("Warning", "Parameters saved, but device is not connected.")
            return

    # Here you will call your serial code to build and send the packet.
    # For Deliverable 2 front end work, this stub is enough.
    print(f"[DEBUG] Would send parameters for mode {mode}: {data}")


    # ---------------- Comms helpers (points 4 & 7) ----------------
    def _push_comm_status_to_ui(self):
        # Update any screens that show comms (MainFrame for now)
        self.frames["MainFrame"].update_comm_status(self.connected, self.current_device_id)
        if "EgramView" in self.frames:
            self.frames["EgramView"].set_device(self.current_device_id)

    def _set_comm_state(self, connected: bool, device_id: str | None):
        """Single place to change comm state and trigger UI + change detection (Point 4 and 7)."""
        self.connected = connected
        self.current_device_id = device_id if connected else None
        self._push_comm_status_to_ui()

        # Point 7: different device approached than previously interrogated
        if connected:
            if self.last_interrogated_device_id is not None and device_id != self.last_interrogated_device_id:
                messagebox.showwarning(
                    "Device Change Detected",
                    f"A different pacemaker is now in range.\n"
                    f"Previous: {self.last_interrogated_device_id}\nCurrent: {device_id}"
                )
            # Update the record of what we have interrogated
            self.last_interrogated_device_id = device_id

    # ---------------- Mock actions ----------------
    def mock_connect(self, device_id: str = "PKM-001"):
        if not self.current_user:
            messagebox.showerror("Error", "Please log in first.")
            return
        self._set_comm_state(True, device_id)

    def mock_disconnect(self):
        self._set_comm_state(False, None)

    def mock_switch_device(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected.")
            return
        new_id = "PKM-002" if self.current_device_id != "PKM-002" else "PKM-003"
        self._set_comm_state(True, new_id)

    def handle_verify_parameters(self):
        """Front end entry point to verify parameters stored on the device."""
        if not self.current_user:
            messagebox.showerror("Error", "Please log in first.")
            return
        if not self.connected:
            messagebox.showerror("Error", "Not connected to a device.")
            return

        ok = self.verify_parameters_on_device()

        if ok:
            messagebox.showinfo("Verification", "Parameters on the pacemaker match the DCM settings.")
        else:
            messagebox.showwarning("Verification", "Parameters on the pacemaker do not match the DCM settings.")

    def verify_parameters_on_device(self) -> bool:
        """
        Placeholder for backend verification logic.
        Expected behavior:
        - Read parameters back from the device over serial.
        - Compare to self.pacing_model settings for self.current_user.
        Return True if they match, False otherwise.
        """
        print("[DEBUG] Would verify parameters on device here.")
        # For now, pretend verification passes
        return True



    # ---------------- Utilities for other views ----------------
    def get_user_count(self) -> int:
        return self.user_model.get_user_count()

    def get_max_users(self) -> int:
        return MAX_USERS

	