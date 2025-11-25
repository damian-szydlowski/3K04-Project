import customtkinter as ctk
from tkinter import messagebox
from typing import Dict

PARAMETER_MAP = {
    "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"],
}

PARAMETER_VALIDATION_RULES = {
    "Lower Rate Limit": (30, 175, int),
    "Upper Rate Limit": (50, 175, int),
    "Atrial Amplitude": (0.5, 7.0, float),
    "Atrial Pulse Width": (0.05, 1.9, float),
    "Ventricular Amplitude": (0.5, 7.0, float),
    "Ventricular Pulse Width": (0.05, 1.9, float),
    "VRP": (150, 500, int),
    "ARP": (150, 500, int),
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

        # Accessibility
        create_access_buttons(top_bar, controller)

        # Main Content
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=20, pady=20)

        self.instr_label = ctk.CTkLabel(main_content, text="Click a color to test the FRDM-K64F RGB LED", font=ctk.CTkFont(size=16))
        self.instr_label.pack(pady=(20, 40))

        # Color Buttons
        self.red_btn = ctk.CTkButton(main_content, text="RED", fg_color="#ef4444", hover_color="#dc2626", height=50, width=200,
                                     command=lambda: controller.send_debug_color(1))
        self.red_btn.pack(pady=10)

        self.green_btn = ctk.CTkButton(main_content, text="GREEN", fg_color="#22c55e", hover_color="#16a34a", height=50, width=200,
                                       command=lambda: controller.send_debug_color(2))
        self.green_btn.pack(pady=10)

        self.blue_btn = ctk.CTkButton(main_content, text="BLUE", fg_color="#3b82f6", hover_color="#2563eb", height=50, width=200,
                                      command=lambda: controller.send_debug_color(3))
        self.blue_btn.pack(pady=10)

        self.off_btn = ctk.CTkButton(main_content, text="OFF", fg_color="gray", height=50, width=200,
                                     command=lambda: controller.send_debug_color(0))
        self.off_btn.pack(pady=10)

        # Back Button
        self.back_btn = ctk.CTkButton(main_content, text="Back to Main Menu", width=200, command=lambda: controller.show_frame("MainFrame"))
        self.back_btn.pack(side="bottom", pady=40)

    def update_font_size(self, size):
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        title_font = ctk.CTkFont(family="Helvetica", size=size+2, weight="bold")
        
        self.title_label.configure(font=title_font)
        self.instr_label.configure(font=normal_font)
        
        for btn in [self.red_btn, self.green_btn, self.blue_btn, self.off_btn, self.back_btn]:
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

        # Accessibility Buttons
        create_access_buttons(top_bar, controller)

        # Main Content
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        self.title_label = ctk.CTkLabel(main_content, textvariable=self.mode_var, font=title_font)
        self.title_label.pack(pady=10)
        
        # Controls Frame
        controls_frame = ctk.CTkFrame(main_content)
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10, ipady=10, ipadx=10)

        param_list = [
            "Lower Rate Limit", "Upper Rate Limit",
            "Atrial Amplitude", "Atrial Pulse Width",
            "Ventricular Amplitude", "Ventricular Pulse Width",
            "VRP", "ARP"
        ]

        for i, param_name in enumerate(param_list):
            rule = PARAMETER_VALIDATION_RULES.get(param_name)
            label_text = f"{param_name}:"
            if rule:
                min_val, max_val, _ = rule
                label_text = f"{param_name}: ({min_val} - {max_val})"
            
            label = ctk.CTkLabel(controls_frame, text=label_text)
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            entry = ctk.CTkEntry(controls_frame, width=200)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            
            self.param_widgets[param_name] = (label, entry)

        # Bottom Buttons
        bottom_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        self.back_btn = ctk.CTkButton(bottom_frame, text="Back to Mode Selection", width=180, command=lambda: controller.show_frame("MainFrame"))
        self.back_btn.pack(side="left", padx=10)
        
        self.logout_btn = ctk.CTkButton(bottom_frame, text="Logout", width=100, command=self._do_logout)
        self.logout_btn.pack(side="right", padx=10)
        
        self.save_btn = ctk.CTkButton(bottom_frame, text="Save Parameters", width=180, command=self._do_save)
        self.save_btn.pack(side="right", padx=10) 

    def update_font_size(self, size):
        """Updates fonts dynamically"""
        # 1. Update Labels
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        title_font = ctk.CTkFont(family="Helvetica", size=size+4, weight="bold")
        
        self.user_label.configure(font=normal_font)
        self.title_label.configure(font=title_font)
        
        # 2. Update Entry Rows
        for (label, entry) in self.param_widgets.values():
            label.configure(font=normal_font)
            entry.configure(font=normal_font)
            
        # 3. Update Buttons
        for btn in [self.back_btn, self.logout_btn, self.save_btn]:
            btn.configure(font=normal_font)

    def set_pacing_mode(self, mode: str, settings: Dict[str, str]):
        self.current_mode = mode 
        self.mode_var.set(f"Editing Parameters for: {mode}")
        
        active_params = PARAMETER_MAP.get(mode, [])

        for param_name, (label, entry) in self.param_widgets.items():
            entry.delete(0, 'end') 
            
            if param_name in active_params:
                label.configure(state="normal")
                entry.configure(state="normal")
                saved_value = settings.get(param_name, "") 
                entry.insert(0, saved_value)
            else:
                label.configure(state="disabled")
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

        min_val, max_val, data_type = rule
        try:
            value = data_type(value_str)
        except ValueError:
            messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be a number.")
            return False

        if not (min_val <= value <= max_val):
            messagebox.showerror("Invalid Input", f"Error in '{name}': Value must be between {min_val} and {max_val}.")
            return False
        
        if name == "Upper Rate Limit":
            try:
                lrl_entry = self.param_widgets["Lower Rate Limit"][1]
                lrl_val = int(lrl_entry.get())
                if value < lrl_val:
                    messagebox.showerror("Invalid Input", "Error: 'Upper Rate Limit' cannot be less than 'Lower Rate Limit'.")
                    return False
            except Exception:
                pass 
        return True

    def set_user(self, username: str):
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
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

        # Accessibility Buttons
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
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(main_content, text="Select Pacing Mode", font=ctk.CTkFont(family="Helvetica", size=18, weight="bold"))
        self.title_label.pack(pady=20)
        
        # Mode Buttons
        controls_frame = ctk.CTkFrame(main_content)
        controls_frame.pack(fill="y", expand=True, padx=10, pady=10)

        self.mode_buttons = []
        for mode in ["AOO", "VOO", "AAI", "VVI"]:
            btn = ctk.CTkButton(controls_frame, text=mode, width=200, command=lambda m=mode: controller.show_data_entry_page(m))
            btn.pack(pady=10, padx=20, ipady=5)
            self.mode_buttons.append(btn)
        
        # Debug Button - Initially Disabled
        self.debug_btn = ctk.CTkButton(controls_frame, text="Hardware Debug: LED Test", 
                                       fg_color="gray", width=200, state="disabled",
                                       command=lambda: controller.show_frame("DebugLED"))
        self.debug_btn.pack(pady=20, padx=20, ipady=5)

        # Bottom Connection Bar
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
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
        
        # 1. Labels
        self.user_label.configure(font=normal_font)
        self.comm_text.configure(font=normal_font)
        self.device_text.configure(font=normal_font)
        self.title_label.configure(font=title_font)
        
        # 2. Mode Buttons
        for btn in self.mode_buttons:
            btn.configure(font=normal_font)
        self.debug_btn.configure(font=normal_font)
            
        # 3. Connection Controls
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
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        self.controller.handle_logout()

    def update_comm_status(self, connected: bool, device_id: str | None):
        if connected:
            self.comm_dot.configure(text_color="#22c55e")
            self.comm_text.configure(text="Connected")
            self.device_text.configure(text=f"Device: {device_id or 'Unknown'}")
            
            # --- CONNECTION LOCKED ---
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.port_dropdown.configure(state="disabled")

            # --- DEBUG BUTTON LOGIC ---
            # ONLY Enable if device is actually the FRDM-K64F
            if device_id == "FRDM-K64F":
                self.debug_btn.configure(state="normal", fg_color="#52525b")
            else:
                # If connected to "Unverified Device" (COM1), keep debug disabled
                self.debug_btn.configure(state="disabled", fg_color="gray")
            
        else:
            self.comm_dot.configure(text_color="#9ca3af")
            self.comm_text.configure(text="Disconnected")
            self.device_text.configure(text="")
            
            # --- CONNECTION OPEN ---
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.port_dropdown.configure(state="normal")

            # --- DISABLE DEBUG ---
            self.debug_btn.configure(state="disabled", fg_color="gray")