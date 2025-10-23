# views/main_view.py
import tkinter as tk
from tkinter import ttk # For better widgets like Notebook or PanedWindow

class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_var = tk.StringVar(value="")

        # --- Top Bar ---
        top_bar = tk.Frame(self, bg="#f0f0f0", height=40, relief="groove", borderwidth=1)
        top_bar.pack(side="top", fill="x")
        
        user_label = tk.Label(top_bar, textvariable=self.user_var, font=("Helvetica", 12), bg="#f0f0f0")
        user_label.pack(side="left", padx=10)

        logout_btn = tk.Button(top_bar, text="Logout", width=10, command=self._do_logout)
        logout_btn.pack(side="right", padx=10)

        # --- Main Content Area ---
        # This is where you will build the rest of your UI
        
        main_content = tk.Frame(self)
        main_content.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_content, text="Pacing Parameters", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # TODO: Add your Pacing Mode selection (AOO, VOO, etc.)
        # TODO: Add your parameter entry fields (LRL, URL, etc.)
        # TODO: Add your visual indicators for comms
        
        # Placeholder for pacing controls
        controls_frame = tk.LabelFrame(main_content, text="Controls")
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(controls_frame, text="Your pacing mode selectors and parameter fields will go here.").pack(pady=50)


    def set_user(self, username: str):
        if username:
            self.user_var.set(f"Logged in as: {username}")
        else:
            self.user_var.set("")
            
    def _do_logout(self):
        self.controller.handle_logout()