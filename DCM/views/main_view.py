import customtkinter as ctk
from tkinter import messagebox
from typing import Dict

# 1. Update the Parameter Map with Rate Adaptive Modes
PARAMETER_MAP = {
    "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
    # New Rate Adaptive Modes
    "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
    "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
    "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
    "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing", "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
}

# 2. Update Validation Rules based on Deliverable 2 & System Spec
PARAMETER_VALIDATION_RULES = {
    "Lower Rate Limit": (30, 175, int),
    "Upper Rate Limit": (50, 175, int),
    "Maximum Sensor Rate": (50, 175, int),
    "Atrial Amplitude": (0.1, 5.0, float),
    "Ventricular Amplitude": (0.1, 5.0, float),
    "Atrial Pulse Width": (1, 30, int),
    "Ventricular Pulse Width": (1, 30, int),
    "Atrial Sensitivity": (0, 5.0, float),
    "Ventricular Sensitivity": (0, 5.0, float),
    "VRP": (150, 500, int),
    "ARP": (150, 500, int),
    "PVARP": (150, 500, int),
    "Hysteresis": (0, 1, int),
    "Rate Smoothing": (0, 25, int),
    "Activity Threshold": (1, 7, int),
    "Reaction Time": (10, 50, int),
    "Response Factor": (1, 16, int),
    "Recovery Time": (2, 16, int),
}

# --- Shared Accessibility Helper ---
def create_access_buttons(parent_frame, controller):
    """Adds Font Size buttons to a frame"""
    btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    btn_frame.pack(side="right", padx=10)
    
    ctk.CTkButton(btn_frame, text="A-", width=30, command=controller.decrease_font_size).pack(side="left", padx=2)
    ctk.CTkButton(btn_frame, text="A+", width=30, command=controller.increase_font_size).pack(side="left", padx=2)


class DebugLED(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Top Bar
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(side="top", fill="x")
        
        self.title_label = ctk.CTkLabel(top_bar, text="Hardware Debug: LED Test", font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        create_access_buttons(top_bar, controller)

        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=20, pady=20)

        self.instr_label = ctk.CTkLabel(main_content, text="Click a color to test the FRDM-K64F RGB LED", font=ctk.CTkFont(size=16))
        self.instr_label.pack(pady=(20, 40))

        self.buttons = []
        for text, col, code in [("RED", "#ef4444", 1), ("GREEN", "#22c55e", 2), ("BLUE", "#3b82f6", 3), ("OFF", "gray", 0)]:
            btn = ctk.CTkButton(main_content, text=text, fg_color=col, height=50, width=200,
                                     command=lambda c=code: controller.send_debug_color(c))
            btn.pack(pady=10)
            self.buttons.append(btn)

        self.back_btn = ctk.CTkButton(main_content, text="Back to Main Menu", width=200, command=lambda: controller.show_frame("MainFrame"))
        self.back_btn.pack(side="bottom", pady=40)

    def update_font_size(self, size):
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        title_font = ctk.CTkFont(family="Helvetica", size=size+2, weight="bold")
        
        self.title_label.configure(font=title_font)
        self.instr_label.configure(font=normal_font)
        
        for btn in self.buttons + [self.back_btn]:
            btn.configure(font=normal_font)


class DataEntry(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.user_var = ctk.StringVar(value="")
        self.mode_var = ctk.StringVar(value="Editing Mode: N/A")
        self.current_mode = None 
        self.param_widgets = {}

        # Top Bar
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(side="top", fill="x")
        
        self.user_label = ctk.CTkLabel(top_bar, textvariable=self.user_var, font=ctk.CTkFont(family="Helvetica", size=12), fg_color="transparent")
        self.user_label.pack(side="left", padx=10)

        create_access_buttons(top_bar, controller)

        # Main Content
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        self.title_label = ctk.CTkLabel(main_content, textvariable=self.mode_var, font=title_font)
        self.title_label.pack(pady=10)
        
        # Scrollable Frame for many parameters
        controls_frame = ctk.CTkScrollableFrame(main_content)
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Full superset of parameters
        param_list = [
            "Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate",
            "Atrial Amplitude", "Atrial Pulse Width", "Atrial Sensitivity",
            "Ventricular Amplitude", "Ventricular Pulse Width", "Ventricular Sensitivity",
            "VRP", "ARP", "PVARP", "Hysteresis", "Rate Smoothing",
            "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"
        ]

        for i, param_name in enumerate(param_list):
            rule = PARAMETER_VALIDATION_RULES.get(param_name)
            label_text = f"{param_name}:"
            if rule:
                min_val, max_val, _ = rule
                label_text = f"{param_name} ({min_val}-{max_val}):"
            
            label = ctk.CTkLabel(controls_frame, text=label_text)
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            entry = ctk.CTkEntry(controls_frame, width=200)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            
            self.param_widgets[param_name] = (label, entry)

        # Bottom Buttons
        bottom_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        self.back_btn = ctk.CTkButton(bottom_frame, text="Back", width=100, command=lambda: controller.show_frame("MainFrame"))
        self.back_btn.pack(side="left", padx=10)
        
        self.logout_btn = ctk.CTkButton(bottom_frame, text="Logout", width=100, command=self._do_logout)
        self.logout_btn.pack(side="right", padx=10)
        
        self.save_btn = ctk.CTkButton(bottom_frame, text="Save Parameters", width=180, command=self._do_save)
        self.save_btn.pack(side="right", padx=10) 

    def update_font_size(self, size):
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        title_font = ctk.CTkFont(family="Helvetica", size=size+4, weight="bold")
        
        self.user_label.configure(font=normal_font)
        self.title_label.configure(font=title_font)
        
        for (label, entry) in self.param_widgets.values():
            label.configure(font=normal_font)
            entry.configure(font=normal_font)
            
        for btn in [self.back_btn, self.logout_btn, self.save_btn]:
            btn.configure(font=normal_font)

    def set_pacing_mode(self, mode: str, settings: Dict[str, str]):
        self.current_mode = mode 
        self.mode_var.set(f"Editing: {mode}")
        
        active_params = PARAMETER_MAP.get(mode, [])

        for param_name, (label, entry) in self.param_widgets.items():
            if param_name in active_params:
                # Show widget
                label.grid()
                entry.grid()
                entry.configure(state="normal")
                entry.delete(0, 'end')
                saved_value = settings.get(param_name, "") 
                entry.insert(0, saved_value)
            else:
                # Hide widget
                label.grid_remove()
                entry.grid_remove()
                entry.configure(state="disabled")

    def _do_save(self):
        if not self.current_mode:
            return 
        data_to_save = {}
        for param_name, (label, entry) in self.param_widgets.items():
            if entry.cget("state") != "disabled":
                value_str = entry.get()
                if not self._validate_entry(param_name, value_str):
                    return
                data_to_save[param_name] = value_str
        
        self.controller.handle_save_settings(self.current_mode, data_to_save)

    def _validate_entry(self, name: str, value_str: str) -> bool:
        rule = PARAMETER_VALIDATION_RULES.get(name)
        if not rule:
            return True

        if name in ["Atrial Amplitude", "Ventricular Amplitude"]:
            if value_str.strip().lower() == "off":
                return True  # accept "Off" as a valid entry and treat as 0 V later

        min_val, max_val, data_type = rule
        try:
            value = data_type(value_str)
        except ValueError:
            messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be a number.")
            return False

        if not (min_val <= value <= max_val):
            messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be between {min_val} and {max_val}.")
            return False
        
                
        if name in ["Atrial Amplitude", "Ventricular Amplitude"]:
            # step 0.1 V
            step = 0.1
            if abs(round(value / step) * step - value) > 1e-6:
                messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be in steps of {step} V.")
                return False

        if name in ["Atrial Sensitivity", "Ventricular Sensitivity"]:
            # step 0.1 V
            step = 0.1
            if abs(round(value / step) * step - value) > 1e-6:
                messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be in steps of {step} V.")
                return False

        if name in ["Atrial Pulse Width", "Ventricular Pulse Width"]:
            # they are ints already, so they are implicitly step 1 ms
            pass


        if name == "Upper Rate Limit":
            try:
                # Try to get LRL if it's active
                if self.param_widgets["Lower Rate Limit"][1].cget("state") != "disabled":
                    lrl_val = int(self.param_widgets["Lower Rate Limit"][1].get())
                    if value < lrl_val:
                        messagebox.showerror("Invalid Input", "Error: URL cannot be less than LRL.")
                        return False
            except Exception:
                pass 
        return True

    def set_user(self, username: str):
        self.user_var.set(f"Logged in as: {username}" if username else "")
            
    def _do_logout(self):
        self.controller.handle_logout()


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_var = ctk.StringVar(value="")

        # Top Bar
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(side="top", fill="x")
        
        self.user_label = ctk.CTkLabel(top_bar, textvariable=self.user_var, font=ctk.CTkFont(family="Helvetica", size=12), fg_color="transparent")
        self.user_label.pack(side="left", padx=10)

        create_access_buttons(top_bar, controller)

        # Status Row
        status_row = ctk.CTkFrame(self, height=32, corner_radius=0)
        status_row.pack(side="top", fill="x", padx=10, pady=(6, 0))

        self.comm_dot = ctk.CTkLabel(status_row, text="●", font=ctk.CTkFont(size=18))
        self.comm_dot.pack(side="left", padx=(4, 6))

        self.comm_text = ctk.CTkLabel(status_row, text="Disconnected")
        self.comm_text.pack(side="left")

        self.device_text = ctk.CTkLabel(status_row, text="")
        self.device_text.pack(side="left", padx=12)

        # Main Content
        # FIX: Added corner_radius=0 to prevent Linux crash
        main_content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(main_content, text="Select Pacing Mode", font=ctk.CTkFont(family="Helvetica", size=18, weight="bold"))
        self.title_label.pack(pady=10)
        
        # --- Center Container for Buttons ---
        # FIX: Added corner_radius=0
        center_container = ctk.CTkFrame(main_content, fg_color="transparent", corner_radius=0)
        center_container.pack(expand=True, fill="both")

        # Two-Column Shared Grid
        self.controls_frame = ctk.CTkFrame(center_container)
        self.controls_frame.pack(expand=True) 

        # Configure columns
        self.controls_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        self.controls_frame.grid_columnconfigure(1, weight=1, uniform="cols")

        # Headers
        self.atrial_title = ctk.CTkLabel(self.controls_frame, text="Atrial Pacing", font=ctk.CTkFont(size=16, weight="bold"))
        self.atrial_title.grid(row=0, column=0, pady=(0, 10))

        self.vent_title = ctk.CTkLabel(self.controls_frame, text="Ventricular Pacing", font=ctk.CTkFont(size=16, weight="bold"))
        self.vent_title.grid(row=0, column=1, pady=(0, 10))

        self.mode_buttons = []

        # Helper to create uniformly sized buttons
        def create_mode_btn(mode, desc, r, c):
            text_val = f"{mode}\n{desc}"
            btn = ctk.CTkButton(self.controls_frame, text=text_val, width=240, height=80,
                                font=ctk.CTkFont(size=14),
                                command=lambda m=mode: controller.show_data_entry_page(m))
            btn.grid(row=r, column=c, padx=15, pady=10, sticky="nsew")
            self.controls_frame.grid_rowconfigure(r, weight=1, uniform="rows")
            self.mode_buttons.append(btn)

        # Atrial Column (0)
        create_mode_btn("AOO", "Asynchronous", 1, 0)
        create_mode_btn("AAI", "Inhibited", 2, 0)
        create_mode_btn("AOOR", "Rate Adaptive Async", 3, 0)
        create_mode_btn("AAIR", "Rate Adaptive Inhibited", 4, 0)

        # Ventricular Column (1)
        create_mode_btn("VOO", "Asynchronous", 1, 1)
        create_mode_btn("VVI", "Inhibited", 2, 1)
        create_mode_btn("VOOR", "Rate Adaptive Async", 3, 1)
        create_mode_btn("VVIR", "Rate Adaptive Inhibited", 4, 1)

        # Debug Button
        self.debug_btn = ctk.CTkButton(self.controls_frame, text="Hardware Debug: LED Test", 
                                       fg_color="gray", width=460, height=40, state="disabled",
                                       command=lambda: controller.show_frame("DebugLED"))
        self.debug_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Egram Button
        self.egram_btn = ctk.CTkButton(self.controls_frame, text="View Real-Time Egrams", 
                                       fg_color="#8b5cf6", hover_color="#7c3aed",
                                       width=460, height=40,
                                       command=lambda: controller.show_frame("EgramView"))
        self.egram_btn.grid(row=6, column=0, columnspan=2, pady=10)


        # Bottom Connection Bar
        # FIX: Added corner_radius=0
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        self.port_var = ctk.StringVar(value="Select Port...")
        self.port_dropdown = ctk.CTkComboBox(bottom_frame, variable=self.port_var, width=120)
        self.port_dropdown.pack(side="left", padx=5)

        self.refresh_btn = ctk.CTkButton(bottom_frame, text="⟳", width=30, command=self.refresh_ports)
        self.refresh_btn.pack(side="left", padx=2)

        self.connect_btn = ctk.CTkButton(bottom_frame, text="Connect", fg_color="green", width=100, command=self._handle_connect)
        self.connect_btn.pack(side="left", padx=10)

        self.disconnect_btn = ctk.CTkButton(bottom_frame, text="Disconnect", fg_color="red", width=100, state="disabled", command=self._handle_disconnect)
        self.disconnect_btn.pack(side="left", padx=5)

        self.logout_btn = ctk.CTkButton(bottom_frame, text="Logout", width=100, command=self._do_logout)
        self.logout_btn.pack(side="right", padx=10)
        
        self.refresh_ports()

    def update_font_size(self, size):
        """Updates fonts dynamically"""
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        title_font = ctk.CTkFont(family="Helvetica", size=size+4, weight="bold")
        btn_font = ctk.CTkFont(family="Helvetica", size=size, weight="bold")
        
        # Labels
        self.user_label.configure(font=normal_font)
        self.comm_text.configure(font=normal_font)
        self.device_text.configure(font=normal_font)
        self.title_label.configure(font=title_font)
        
        # Category Titles
        self.atrial_title.configure(font=title_font)
        self.vent_title.configure(font=title_font)

        # Mode Buttons
        for btn in self.mode_buttons:
            btn.configure(font=btn_font)
        
        self.debug_btn.configure(font=normal_font)
        self.egram_btn.configure(font=normal_font)
            
        # Connection Controls
        controls = [self.port_dropdown, self.refresh_btn, self.connect_btn, self.disconnect_btn, self.logout_btn]
        for ctrl in controls:
            ctrl.configure(font=normal_font)

    # ... existing methods (refresh_ports, handlers, etc.) ...
    def refresh_ports(self):
        ports = self.controller.get_serial_ports()
        if ports:
            self.port_dropdown.configure(values=ports)
            self.port_dropdown.set(ports[0])
        else:
            self.port_dropdown.configure(values=["No Ports"])
            self.port_dropdown.set("No Ports")

    def _handle_connect(self):
        selected_port = self.port_var.get()
        if not selected_port or selected_port == "No Ports" or selected_port == "Select Port...":
            messagebox.showerror("Error", "Please select a valid COM port.")
            return
        self.controller.connect_serial(selected_port)

    def _handle_disconnect(self):
        self.controller.disconnect_serial()

    def set_user(self, username: str):
        self.user_var.set(f"Logged in as: {username}" if username else "")
            
    def _do_logout(self):
        self.controller.handle_logout()

    def update_comm_status(self, connected: bool, device_id: str | None):
        if connected:
            self.comm_dot.configure(text_color="#22c55e")
            self.comm_text.configure(text="Connected")
            self.device_text.configure(text=f"Device: {device_id or 'Unknown'}")
            
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.port_dropdown.configure(state="disabled")

            if device_id == "FRDM-K64F":
                self.debug_btn.configure(state="normal", fg_color="#52525b")
            else:
                self.debug_btn.configure(state="disabled", fg_color="gray")
            
        else:
            self.comm_dot.configure(text_color="#9ca3af")
            self.comm_text.configure(text="Disconnected")
            self.device_text.configure(text="")
            
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.port_dropdown.configure(state="normal")
            self.debug_btn.configure(state="disabled", fg_color="gray")