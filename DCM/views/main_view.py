import customtkinter as ctk
from tkinter import messagebox  
from typing import Dict 

# This map tells us which parameters are active for each pacing mode
PARAMETER_MAP = {
    "AOO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"],
}

# Validation rules
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


# This is the screen for entering and editing pacing parameters.
class DataEntry(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.user_var = ctk.StringVar(value="")
        self.mode_var = ctk.StringVar(value="Editing Mode: N/A")
        self.current_mode = None 
        
        self.param_widgets = {}

        # This is the bar at the top showing the logged in user
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(side="top", fill="x")
        
        user_label = ctk.CTkLabel(top_bar, textvariable=self.user_var, font=ctk.CTkFont(family="Helvetica", size=12), fg_color="transparent")
        user_label.pack(side="left", padx=10)

        # This is the main content area below the top bar
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # The title that shows which mode we're editing
        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        ctk.CTkLabel(main_content, textvariable=self.mode_var, font=title_font).pack(pady=10)
        
        # A frame to hold all the parameter entry boxes
        controls_frame = ctk.CTkFrame(main_content)
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10, ipady=10, ipadx=10)

        # This is the list of all possible parameters
        param_list = [
            "Lower Rate Limit", "Upper Rate Limit",
            "Atrial Amplitude", "Atrial Pulse Width",
            "Ventricular Amplitude", "Ventricular Pulse Width",
            "VRP", "ARP"
        ]

        # Let's create all the labels and entry boxes in a loop
        for i, param_name in enumerate(param_list):
            
            # --- THIS IS THE MODIFIED PART ---
            # Get the rule for this parameter
            rule = PARAMETER_VALIDATION_RULES.get(param_name)
            label_text = f"{param_name}:" # Start with the base text
            
            if rule:
                # If a rule exists, add the (min-max) range to the text
                min_val, max_val, _ = rule
                label_text = f"{param_name}: ({min_val} - {max_val})"
            
            # Create the label with the new text
            label = ctk.CTkLabel(controls_frame, text=label_text)
            # --- END OF MODIFICATION ---
            
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            entry = ctk.CTkEntry(controls_frame, width=200)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            
            # Save the widgets so we can enable/disable them later
            self.param_widgets[param_name] = (label, entry)

        # This frame holds the buttons at the bottom
        bottom_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        Back_Button = ctk.CTkButton(bottom_frame, text="Back to Mode Selection", width=180, command=lambda: controller.show_frame("MainFrame"))
        Back_Button.pack(side="left", padx=10)
        
        logout_btn = ctk.CTkButton(bottom_frame, text="Logout", width=100, command=self._do_logout)
        logout_btn.pack(side="right", padx=10)
        
        Save_Button = ctk.CTkButton(bottom_frame, text="Save Parameters", width=180, command=self._do_save)
        Save_Button.pack(side="right", padx=10) 

    def set_pacing_mode(self, mode: str, settings: Dict[str, str]):
        # This function is called by the controller to set up the page
        self.current_mode = mode 
        self.mode_var.set(f"Editing Parameters for: {mode}")
        
        # Get the list of parameters that are allowed for this mode
        active_params = PARAMETER_MAP.get(mode, [])

        # Loop through all the widgets we created
        for param_name, (label, entry) in self.param_widgets.items():
            entry.delete(0, 'end') # Clear any old value first
            
            if param_name in active_params:
                # If it's active, turn it on and fill in the saved value
                label.configure(state="normal")
                entry.configure(state="normal")
                saved_value = settings.get(param_name, "") 
                entry.insert(0, saved_value)
            else:
                # If it's not active, turn it off
                label.configure(state="disabled")
                entry.configure(state="disabled")

    def _do_save(self):
        # This runs when the 'Save' button is clicked
        if not self.current_mode:
            return 

        data_to_save = {}
        # Go through all widgets and get the text from the ones that are enabled
        for param_name, (label, entry) in self.param_widgets.items():
            if entry.cget("state") != "disabled":
                value_str = entry.get()
                
                if not self._validate_entry(param_name, value_str):
                    return # Stop the save if validation fails
                
                data_to_save[param_name] = value_str
        
        # If all validations passed, send the data to the controller
        self.controller.handle_save_settings(self.current_mode, data_to_save)

    def _validate_entry(self, name: str, value_str: str) -> bool:
        """Checks if a single value is valid for its parameter."""
        rule = PARAMETER_VALIDATION_RULES.get(name)
        if not rule:
            return True # No rule, so it's fine

        min_val, max_val, data_type = rule
        
        try:
            value = data_type(value_str)
        except ValueError:
            messagebox.showerror("Invalid Input", 
                                 f"Error in '{name}':\n\n"
                                 f"Value must be a number.")
            return False

        if not (min_val <= value <= max_val):
            messagebox.showerror("Invalid Input", 
                                 f"Error in '{name}':\n\n"
                                 f"Value must be between {min_val} and {max_val}.")
            return False
        
        if name == "Upper Rate Limit":
            try:
                lrl_entry = self.param_widgets["Lower Rate Limit"][1]
                lrl_val = int(lrl_entry.get())
                if value < lrl_val:
                    messagebox.showerror("Invalid Input", 
                                         "Error: 'Upper Rate Limit' cannot be less than 'Lower Rate Limit'.")
                    return False
            except Exception:
                pass 
        
        return True # All checks passed

    def set_user(self, username: str):
        # Updates the user label in the top bar
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        # Tells the controller to log us out
        self.controller.handle_logout()


# This is the main menu screen where you select a pacing mode.
class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.user_var = ctk.StringVar(value="")

        # The top bar showing the logged in user
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(side="top", fill="x")
        
        user_label = ctk.CTkLabel(top_bar, textvariable=self.user_var, font=ctk.CTkFont(family="Helvetica", size=12), fg_color="transparent")
        user_label.pack(side="left", padx=10)

        # The main part of the screen
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        ctk.CTkLabel(main_content, text="Select Pacing Mode", font=title_font).pack(pady=20)
        
        # A frame to hold the mode buttons
        controls_frame = ctk.CTkFrame(main_content)
        controls_frame.pack(fill="y", expand=True, padx=10, pady=10)

        # These buttons tell the controller to show the data entry page
        # for a specific mode
        AOO_Button = ctk.CTkButton(controls_frame, text="AOO", width=200, command=lambda: controller.show_data_entry_page("AOO"))
        AOO_Button.pack(pady=10, padx=20, ipady=5)
        
        VOO_Button = ctk.CTkButton(controls_frame, text="VOO", width=200, command=lambda: controller.show_data_entry_page("VOO"))
        VOO_Button.pack(pady=10, padx=20, ipady=5)
        
        AAI_Button = ctk.CTkButton(controls_frame, text="AAI", width=200, command=lambda: controller.show_data_entry_page("AAI"))
        AAI_Button.pack(pady=10, padx=20, ipady=5)
        
        VVI_Button = ctk.CTkButton(controls_frame, text="VVI", width=200, command=lambda: controller.show_data_entry_page("VVI"))
        VVI_Button.pack(pady=11, padx=20, ipady=5)

        # This frame holds the button at the bottom
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        # The logout button now lives in the bottom right
        logout_btn = ctk.CTkButton(bottom_frame, text="Logout", width=100, command=self._do_logout)
        logout_btn.pack(side="right", padx=10)

    def set_user(self, username: str):
        # Updates the user label in the top bar
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        # Tells the controller to log us out
        self.controller.handle_logout()