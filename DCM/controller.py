import tkinter as tk
from tkinter import messagebox
from typing import Tuple, Dict

# Import Models
from models.user_model import UserModel, MAX_USERS
from models.pacing_model import PacingModel 


# Import Views
from views.login_views import Welcome, Register, Login
from views.main_view import MainFrame, DataEntry

#  Get screen dimensions for initial window size
root = tk.Tk()
width = int(root.winfo_screenwidth() / 2)
height = int(root.winfo_screenheight() / 2)
root.destroy()



class DCMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM - Device Controller-Monitor")
        self.geometry(str(width) + "x" + str(height))
        self.resizable(True, True)

        # Models
        self.user_model = UserModel()
        self.pacing_model = PacingModel()
        self.current_user = None

        # Main Container
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Frames
        self.frames = {}
        # We pass 'self' as the controller to each frame
        for F in (Welcome, Register, Login, MainFrame, DataEntry):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Welcome")

    def show_frame(self, frame_name: str):
       # Brings the specified frame to the front
        frame = self.frames[frame_name]
        
        # Refreshing data when a frame is shown
        if frame_name == "Welcome":
            frame.refresh_user_count()

        frame.tkraise()

    # Public methods for views
    
    def handle_register(self, username: str, password: str):
        # Handles register request from Register view.
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

    def show_data_entry_page(self, mode: str):
        """
        Loads data and shows the DataEntry frame.
        """
        if not self.current_user:
             messagebox.showerror("Error", "Not logged in.")
             return

        # Load settings from the model
        settings = self.pacing_model.load_settings(self.current_user, mode)
        
        # Pass the mode and loaded settings to the frame
        self.frames["DataEntry"].set_pacing_mode(mode, settings)

        self.show_frame("DataEntry")

    def handle_save_settings(self, mode: str, data: Dict[str, str]):
            """
            Handles save request from DataEntry view.
            """
            if not self.current_user:
                messagebox.showerror("Error", "Not logged in.")
                return
            
            # Save the settings via the model
            self.pacing_model.save_settings(self.current_user, mode, data)
            messagebox.showinfo("Success", f"{mode} settings have been saved.")
            
            # Go back to the main menu
            self.show_frame("MainFrame")

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
            self.current_user = username 
            self.frames["MainFrame"].set_user(username)
            self.frames["DataEntry"].set_user(username)
            self.show_frame("MainFrame")
        else:
            messagebox.showerror("Error", message)
            
    def handle_logout(self):
        """Handles logout request from MainFrame view."""
        self.current_user = None 
        self.frames["MainFrame"].set_user("") 
        self.frames["DataEntry"].set_user("")
        self.show_frame("Welcome")


