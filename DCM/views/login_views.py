import customtkinter as ctk

# This class is the main login screen, split in two.
class Welcome(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up a two-column grid that splits the screen 50/50
        self.grid_columnconfigure(0, weight=1, uniform="split") # Left half
        self.grid_columnconfigure(1, weight=1, uniform="split") # Right half
        self.grid_rowconfigure(0, weight=1)
        
        # This is the left side with the "Welcome Back!" text
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        # We put the text in a label and center it
        welcome_font = ctk.CTkFont(family="Helvetica", size=48, weight="bold")
        welcome_label = ctk.CTkLabel(left_frame, text="Welcome\nto DCM!", font=welcome_font)
        welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        # This is the right side with the login form
        # It gets the default lighter background color
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # This frame holds all the login widgets
        # It's transparent so it shows the right_frame's color
        content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        ctk.CTkLabel(content_frame, text="Login", font=title_font).pack(pady=16)

        # A frame for the entry boxes
        form = ctk.CTkFrame(content_frame, fg_color="transparent")
        form.pack(pady=8)
        
        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ctk.CTkLabel(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = ctk.CTkEntry(form, width=200)
        self.pass_entry = ctk.CTkEntry(form, width=200, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        # A frame for the buttons
        btns = ctk.CTkFrame(content_frame, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="Login", width=100, command=self._do_login).grid(row=0, column=0, padx=6)
        
        # This button switches to the Register screen
        ctk.CTkButton(btns, text="Register", width=100, command=lambda: controller.show_frame("Register")).grid(row=0, column=1, padx=6)

        # This label shows the user count
        self.count_var = ctk.StringVar(value="Users stored: 0 of 10")
        ctk.CTkLabel(content_frame, textvariable=self.count_var).pack(pady=20)

    def _do_login(self):
        # This runs when the 'Login' button is clicked
        username = self.name_entry.get()
        password = self.pass_entry.get()

        # Clear the fields first to prevent flickering
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        # Send the info to the controller to check it
        self.controller.handle_login(username, password)

    def refresh_user_count(self):
        # This updates the user count label
        count = self.controller.get_user_count()
        max_users = self.controller.get_max_users()
        self.count_var.set(f"Users stored: {count} of {max_users}")


# This class is the new user registration screen.
class Register(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up the same two-column grid
        self.grid_columnconfigure(0, weight=1, uniform="split")
        self.grid_columnconfigure(1, weight=1, uniform="split")
        self.grid_rowconfigure(0, weight=1)

        # This is the left side with the "Create Account" text
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        # Put the text in a label and center it
        welcome_font = ctk.CTkFont(family="Helvetica", size=48, weight="bold")
        welcome_label = ctk.CTkLabel(left_frame, text="Create\nAccount", font=welcome_font)
        welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        # This is the right side with the registration form
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # This frame holds the register form and is centered
        content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_font = ctk.CTkFont(family="Helvetica", size=16, weight="bold")
        ctk.CTkLabel(content_frame, text="Register New User", font=title_font).pack(pady=16)

        # A frame for the entry boxes
        form = ctk.CTkFrame(content_frame, fg_color="transparent")
        form.pack(pady=8)
        
        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ctk.CTkLabel(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = ctk.CTkEntry(form, width=200)
        self.pass_entry = ctk.CTkEntry(form, width=200, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        # A frame for the buttons
        btns = ctk.CTkFrame(content_frame, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="Register", width=100, command=self._do_register).grid(row=0, column=0, padx=6)
        
        # This button goes back to the "Welcome" (login) screen
        ctk.CTkButton(btns, text="Back", width=100, command=lambda: controller.show_frame("Welcome")).grid(row=0, column=1, padx=6)

    def _do_register(self):
        # This runs when the 'Register' button is clicked
        username = self.name_entry.get()
        password = self.pass_entry.get()
        
        # Clear the fields first
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        # Send the info to the controller to save it
        self.controller.handle_register(username, password)