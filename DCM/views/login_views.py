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
        
        # --- Left Side (Welcome Text) ---
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        welcome_font = ctk.CTkFont(family="Helvetica", size=48, weight="bold")
        welcome_label = ctk.CTkLabel(left_frame, text="Welcome\nto DCM!", font=welcome_font)
        welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Right Side (Login Form) ---
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # Container for the form elements
        # CHANGED: Added relwidth=0.7 so it takes 70% of the right frame's width
        content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.7)

        # Title
        title_font = ctk.CTkFont(family="Helvetica", size=32, weight="bold")
        ctk.CTkLabel(content_frame, text="Login", font=title_font).pack(pady=(0, 40))

        # Inputs
        # CHANGED: Removed fixed width, added fill="x" to pack
        self.name_entry = ctk.CTkEntry(content_frame, height=50, 
                                       font=ctk.CTkFont(size=16), placeholder_text="Username")
        self.name_entry.pack(pady=10, fill="x")
        
        self.pass_entry = ctk.CTkEntry(content_frame, height=50, 
                                       font=ctk.CTkFont(size=16), placeholder_text="Password", show="*")
        self.pass_entry.pack(pady=10, fill="x")

        # Buttons
        # CHANGED: Removed fixed width, added fill="x" to pack
        ctk.CTkButton(content_frame, text="Login", height=50, 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      command=self._do_login).pack(pady=(30, 10), fill="x")
        
        ctk.CTkButton(content_frame, text="Create New Account", height=50, 
                      font=ctk.CTkFont(size=16), fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"),
                      command=lambda: controller.show_frame("Register")).pack(pady=10, fill="x")

        # User Count Label
        self.count_var = ctk.StringVar(value="Users stored: 0 of 10")
        ctk.CTkLabel(content_frame, textvariable=self.count_var, font=ctk.CTkFont(size=14)).pack(pady=20)

    def _do_login(self):
        username = self.name_entry.get()
        password = self.pass_entry.get()

        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        self.controller.handle_login(username, password)

    def refresh_user_count(self):
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

        # --- Left Side ---
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        welcome_font = ctk.CTkFont(family="Helvetica", size=48, weight="bold")
        welcome_label = ctk.CTkLabel(left_frame, text="Create\nAccount", font=welcome_font)
        welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Right Side ---
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # CHANGED: Added relwidth=0.7
        content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.7)

        # Title
        title_font = ctk.CTkFont(family="Helvetica", size=32, weight="bold")
        ctk.CTkLabel(content_frame, text="Register", font=title_font).pack(pady=(0, 40))

        # Inputs
        # CHANGED: Removed fixed width, added fill="x"
        self.name_entry = ctk.CTkEntry(content_frame, height=50, 
                                       font=ctk.CTkFont(size=16), placeholder_text="New Username")
        self.name_entry.pack(pady=10, fill="x")
        
        self.pass_entry = ctk.CTkEntry(content_frame, height=50, 
                                       font=ctk.CTkFont(size=16), placeholder_text="New Password", show="*")
        self.pass_entry.pack(pady=10, fill="x")

        # Buttons
        # CHANGED: Removed fixed width, added fill="x"
        ctk.CTkButton(content_frame, text="Confirm Registration", height=50,
                      font=ctk.CTkFont(size=18, weight="bold"),
                      command=self._do_register).pack(pady=(30, 10), fill="x")
        
        ctk.CTkButton(content_frame, text="Back to Login", height=50,
                      font=ctk.CTkFont(size=16), fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"),
                      command=lambda: controller.show_frame("Welcome")).pack(pady=10, fill="x")

    def _do_register(self):
        username = self.name_entry.get()
        password = self.pass_entry.get()
        
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        self.controller.handle_register(username, password)