# app_controller.py
import tkinter as tk
from tkinter import messagebox

# Import Models
from models.user_model import UserModel, MAX_USERS

# Import Views
from views.login_views import Welcome, Register, Login
from views.main_view import MainFrame
# We will create PacingModel later
# from models.pacing_model import PacingModel 

class DCMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM - Device Controller-Monitor")
        self.geometry("420x320") # Start with login size
        self.resizable(False, False)

        # --- Models ---
        self.user_model = UserModel()
        # self.pacing_model = PacingModel() # For when you add parameters

        # --- Main Container ---
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # --- Frames ---
        self.frames = {}
        # We pass 'self' as the controller to each frame
        for F in (Welcome, Register, Login, MainFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Welcome")

    def show_frame(self, frame_name: str):
        """Raises the given frame to the top."""
        frame = self.frames[frame_name]
        
        # Special logic for refreshing data when a frame is shown
        if frame_name == "Welcome":
            frame.refresh_user_count()
        elif frame_name == "MainFrame":
            # Resize window for the main application
            self.geometry("800x600") 
            self.resizable(True, True)
            
        elif frame_name in ("Login", "Register"):
            self.geometry("420x320")
            self.resizable(False, False)

        frame.tkraise()

    # --- Public methods for views to call ---
    
    def handle_register(self, username: str, password: str):
        """Handles register request from Register view."""
        success, message = self.user_model.register_user(username, password)
        
        if success:
            messagebox.showinfo("Success", message)
            self.show_frame("Welcome")
        else:
            messagebox.showerror("Error", message)

    def handle_login(self, username: str, password: str):
        """Handles login request from Login view."""
        success, message = self.user_model.authenticate(username, password)
        
        if success:
            # Set user info on the main frame
            self.frames["MainFrame"].set_user(username)
            self.show_frame("MainFrame")
        else:
            messagebox.showerror("Error", message)
            
    def handle_logout(self):
        """Handles logout request from MainFrame view."""
        self.frames["MainFrame"].set_user("") # Clear user
        self.show_frame("Welcome")

    def get_user_count(self) -> int:
        return self.user_model.get_user_count()

    def get_max_users(self) -> int:
        return MAX_USERS