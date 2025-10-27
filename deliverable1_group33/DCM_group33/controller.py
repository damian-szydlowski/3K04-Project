import customtkinter as ctk
from tkinter import messagebox
from typing import Dict

# Data models
from models.user_model import UserModel, MAX_USERS
from models.pacing_model import PacingModel

# Views
from views.login_views import Welcome, Register
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
        for F in (Welcome, Register, MainFrame, DataEntry):
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
        self.pacing_model.save_settings(self.current_user, mode, data)
        messagebox.showinfo("Success", f"{mode} settings have been saved.")
        self.show_frame("MainFrame")

    # ---------------- Comms helpers (points 4 & 7) ----------------
    def _push_comm_status_to_ui(self):
        # Update any screens that show comms (MainFrame for now)
        self.frames["MainFrame"].update_comm_status(self.connected, self.current_device_id)

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

    # ---------------- Utilities for other views ----------------
    def get_user_count(self) -> int:
        return self.user_model.get_user_count()

    def get_max_users(self) -> int:
        return MAX_USERS

	