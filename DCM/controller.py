import customtkinter as ctk
from tkinter import messagebox
from typing import Tuple, Dict

# Get our data models
from models.user_model import UserModel, MAX_USERS
from models.pacing_model import PacingModel 

# Get our screen/view classes
from views.login_views import Welcome, Register, Login
from views.main_view import MainFrame, DataEntry

# Set the overall look of the app
ctk.set_appearance_mode("System") # Can be "System", "Light", or "Dark"
ctk.set_default_color_theme("blue") 

class DCMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DCM - Device Controller-Monitor")

        # Let's make the window half the screen size
        window_width = int(self.winfo_screenwidth() * 0.5)
        window_height = int(self.winfo_screenheight() * 0.5)

        # Find out how big the monitor is
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Figure out the x/y coords to center the window
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)

        # Set the window's size and position
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        
        self.resizable(True, True)

        # Set up our data management classes
        self.user_model = UserModel()
        self.pacing_model = PacingModel()
        self.current_user = None

        # This is the main container frame that holds all our screens
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create all the screens (frames) for the app
        self.frames = {}
        
        # We give each frame a way to talk back to this controller
        for F in (Welcome, Register, Login, MainFrame, DataEntry):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Welcome")

    def show_frame(self, frame_name: str):
       # This function just brings the frame you want to the front
        frame = self.frames[frame_name]
        
        # We need to update the user count when we show the welcome screen
        if frame_name == "Welcome":
            frame.refresh_user_count()

        frame.tkraise()

    # These are the functions our screens can call
    
    def handle_register(self, username: str, password: str):
        # This runs when the register button is clicked
        success, message = self.user_model.register_user(username, password)
        
        if success:
            messagebox.showinfo("Success", message)
            self.show_frame("Welcome")
        else:
            messagebox.showerror("Error", message)

    def handle_login(self, username: str, password: str):
        """This runs when the login button is clicked."""
        success, message = self.user_model.authenticate(username, password)
        
        if success:
            self.current_user = username # We need to remember who just logged in
            self.frames["MainFrame"].set_user(username)
            self.frames["DataEntry"].set_user(username)
            self.show_frame("MainFrame")
        else:
            messagebox.showerror("Error", message)
            
    def handle_logout(self):
        """This runs when the logout button is clicked."""
        self.current_user = None # Forget who was logged in
        self.frames["MainFrame"].set_user("") 
        self.frames["DataEntry"].set_user("")
        self.show_frame("Welcome")

    def get_user_count(self) -> int:
        return self.user_model.get_user_count()

    def get_max_users(self) -> int:
        return MAX_USERS

    def show_data_entry_page(self, mode: str):
        """
        This gets the settings for a pacing mode and shows the data entry page.
        """
        if not self.current_user:
             messagebox.showerror("Error", "Not logged in.")
             return

        # Ask the pacing model to load the saved settings
        settings = self.pacing_model.load_settings(self.current_user, mode)
        
        # Tell the data entry screen which mode we're in and what data to show
        self.frames["DataEntry"].set_pacing_mode(mode, settings)

        self.show_frame("DataEntry")

    def handle_save_settings(self, mode: str, data: Dict[str, str]):
            """
            This runs when the 'Save' button is clicked on the data entry page.
            """
            if not self.current_user:
                messagebox.showerror("Error", "Not logged in.")
                return
            
            # Tell the pacing model to save the new data
            self.pacing_model.save_settings(self.current_user, mode, data)
            messagebox.showinfo("Success", f"{mode} settings have been saved.")
            
            # Go back to the main menu screen
            self.show_frame("MainFrame")