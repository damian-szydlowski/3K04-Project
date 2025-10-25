import tkinter as tk
from tkinter import ttk
from typing import Dict # Import Dict

# This map defines which parameters are active for each mode.
# These strings MUST match the keys in the self.param_widgets dictionary below.
PARAMETER_MAP = {
    "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"],
}
class DataEntry(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="Editing Mode: N/A")
        self.current_mode = None 
        
        self.param_widgets = {}

        # Top Bar
        top_bar = tk.Frame(self, bg="#f0f0f0", height=40, relief="groove", borderwidth=1)
        top_bar.pack(side="top", fill="x")
        
        user_label = tk.Label(top_bar, textvariable=self.user_var, font=("Helvetica", 12), bg="#f0f0f0")
        user_label.pack(side="left", padx=10)

        logout_btn = tk.Button(top_bar, text="Logout", width=10, command=self._do_logout)
        logout_btn.pack(side="right", padx=10)

        # Main Content Area 
        main_content = tk.Frame(self)
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_content, textvariable=self.mode_var, font=("Helvetica", 16, "bold")).pack(pady=10)
        
        controls_frame = tk.LabelFrame(main_content, text="Parameters")
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10, ipady=10, ipadx=10)

        param_list = [
            "Lower Rate Limit", "Upper Rate Limit",
            "Atrial Amplitude", "Atrial Pulse Width",
            "Ventricular Amplitude", "Ventricular Pulse Width",
            "VRP", "ARP"
        ]

        for i, param_name in enumerate(param_list):
            label = tk.Label(controls_frame, text=f"{param_name}:")
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            entry = tk.Entry(controls_frame, width=20)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            
            self.param_widgets[param_name] = (label, entry)

        # Bottom Bar 
        bottom_frame = tk.Frame(main_content)
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        Back_Button = tk.Button(bottom_frame, text="Back to Mode Selection", width=20, command=lambda: controller.show_frame("MainFrame"))
        Back_Button.pack(side="left", padx=10)
        
        Save_Button = tk.Button(bottom_frame, text="Save Parameters", width=20, command=self._do_save)
        Save_Button.pack(side="right", padx=10)

    def set_pacing_mode(self, mode: str, settings: Dict[str, str]):
            
        self.current_mode = mode # Store for saving
        self.mode_var.set(f"Editing Parameters for: {mode}")
            
        active_params = PARAMETER_MAP.get(mode, [])

        for param_name, (label, entry) in self.param_widgets.items():
            entry.delete(0, 'end')  
            if param_name in active_params:
                label.config(state="normal")
                entry.config(state="normal")
                saved_value = settings.get(param_name, "") 
                entry.insert(0, saved_value)
            else:
                label.config(state="disabled")
                entry.config(state="disabled")

    def _do_save(self):
        """Collects data from entry boxes and tells controller to save."""
        if not self.current_mode:
            return # Should not happen

        data_to_save = {}
        for param_name, (label, entry) in self.param_widgets.items():
            if entry.cget("state") != "disabled":
                data_to_save[param_name] = entry.get()
        
        # Pass the mode and the collected data to the controller
        self.controller.handle_save_settings(self.current_mode, data_to_save)

    def set_user(self, username: str):
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        self.controller.handle_logout()


class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_var = tk.StringVar(value="")

        # Top Bar 
        top_bar = tk.Frame(self, bg="#f0f0f0", height=40, relief="groove", borderwidth=1)
        top_bar.pack(side="top", fill="x")
        
        user_label = tk.Label(top_bar, textvariable=self.user_var, font=("Helvetica", 12), bg="#f0f0f0")
        user_label.pack(side="left", padx=10)

        logout_btn = tk.Button(top_bar, text="Logout", width=10, command=self._do_logout)
        logout_btn.pack(side="right", padx=10)

        # Main Content Area 
        main_content = tk.Frame(self)
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_content, text="Select Pacing Mode", font=("Helvetica", 16, "bold")).pack(pady=20)
        
        # Pacing Mode Controls 
        controls_frame = tk.LabelFrame(main_content, text="Modes")
        controls_frame.pack(fill="y", expand=True, padx=10, pady=10)

        # Buttons for each mode
        AOO_Button = tk.Button(controls_frame, text="AOO", width=20, command=lambda: controller.show_data_entry_page("AOO"))
        AOO_Button.pack(pady=10, padx=20, ipady=5)
        
        VOO_Button = tk.Button(controls_frame, text="VOO", width=20, command=lambda: controller.show_data_entry_page("VOO"))
        VOO_Button.pack(pady=10, padx=20, ipady=5)
        
        AAI_Button = tk.Button(controls_frame, text="AAI", width=20, command=lambda: controller.show_data_entry_page("AAI"))
        AAI_Button.pack(pady=10, padx=20, ipady=5)
        
        VVI_Button = tk.Button(controls_frame, text="VVI", width=20, command=lambda: controller.show_data_entry_page("VVI"))
        VVI_Button.pack(pady=11, padx=20, ipady=5)

    def set_user(self, username: str):
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        self.controller.handle_logout()