import customtkinter as ctk

# This class is the first screen the user sees.
class Welcome(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # This frame will hold all our content and we'll center it
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Just a simple title font
        title_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")
        
        # Make sure all widgets are inside the content_frame
        ctk.CTkLabel(content_frame, text="Welcome to DCM", font=title_font).pack(pady=24)
        
        self.count_var = ctk.StringVar(value="Users stored: 0 of 10")
        ctk.CTkLabel(content_frame, textvariable=self.count_var).pack(pady=4)

        ctk.CTkButton(content_frame, text="Login", width=140, command=lambda: controller.show_frame("Login")).pack(pady=8)
        ctk.CTkButton(content_frame, text="Register", width=140, command=lambda: controller.show_frame("Register")).pack(pady=4)
        ctk.CTkButton(content_frame, text="Exit", width=140, command=controller.destroy).pack(pady=18)

        # This is the magic line that centers the content
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

    def refresh_user_count(self):
        # Asks the controller for the current user count and updates the label
        count = self.controller.get_user_count()
        max_users = self.controller.get_max_users()
        self.count_var.set(f"Users stored: {count} of {max_users}")

# This class is the new user registration screen.
class Register(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # This frame will hold all our content and we'll center it
        content_frame = ctk.CTkFrame(self, fg_color="transparent")

        title_font = ctk.CTkFont(family="Helvetica", size=16, weight="bold")
        # Put the title in the content_frame
        ctk.CTkLabel(content_frame, text="Register New User", font=title_font).pack(pady=16)

        # We put the labels and entry boxes in their own frame
        # This frame also goes inside the content_frame
        form = ctk.CTkFrame(content_frame, fg_color="transparent")
        form.pack(pady=8)
        
        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ctk.CTkLabel(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = ctk.CTkEntry(form, width=200)
        self.pass_entry = ctk.CTkEntry(form, width=200, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        # We put the buttons in their own frame
        # This frame also goes inside the content_frame
        btns = ctk.CTkFrame(content_frame, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="Register", width=100, command=self._do_register).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text="Back", width=100, command=lambda: controller.show_frame("Welcome")).grid(row=0, column=1, padx=6)

        # This is the magic line that centers the content
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

    def _do_register(self):
        # This function runs when the 'Register' button is clicked
        username = self.name_entry.get()
        password = self.pass_entry.get()
        
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        self.controller.handle_register(username, password)

# This class is the existing user login screen.
class Login(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # This frame will hold all our content and we'll center it
        content_frame = ctk.CTkFrame(self, fg_color="transparent")

        title_font = ctk.CTkFont(family="Helvetica", size=16, weight="bold")
        # Put the title in the content_frame
        ctk.CTkLabel(content_frame, text="Login", font=title_font).pack(pady=16)

        # Frame for the entry boxes
        # This frame also goes inside the content_frame
        form = ctk.CTkFrame(content_frame, fg_color="transparent")
        form.pack(pady=8)
        
        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ctk.CTkLabel(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = ctk.CTkEntry(form, width=200)
        self.pass_entry = ctk.CTkEntry(form, width=200, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        # Frame for the buttons
        # This frame also goes inside the content_frame
        btns = ctk.CTkFrame(content_frame, fg_color="transparent")
        btns.pack(pady=10)
        
        ctk.CTkButton(btns, text="Login", width=100, command=self._do_login).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text="Back", width=100, command=lambda: controller.show_frame("Welcome")).grid(row=0, column=1, padx=6)

        # This is the magic line that centers the content
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

    def _do_login(self):
        # This function runs when the 'Login' button is clicked
        username = self.name_entry.get()
        password = self.pass_entry.get()

        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        self.controller.handle_login(username, password)