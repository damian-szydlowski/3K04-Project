# views/login_views.py
import tkinter as tk

class Welcome(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Welcome to DCM", font=("Helvetica", 16, "bold")).pack(pady=24)
        self.count_var = tk.StringVar(value="Users stored: 0 of 10")
        tk.Label(self, textvariable=self.count_var).pack(pady=4)

        tk.Button(self, text="Login", width=18, command=lambda: controller.show_frame("Login")).pack(pady=8)
        tk.Button(self, text="Register", width=18, command=lambda: controller.show_frame("Register")).pack(pady=4)
        tk.Button(self, text="Exit", width=18, command=controller.destroy).pack(pady=18)

    def refresh_user_count(self):
        count = self.controller.get_user_count()
        max_users = self.controller.get_max_users()
        self.count_var.set(f"Users stored: {count} of {max_users}")

class Register(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Register New User", font=("Helvetica", 14, "bold")).pack(pady=16)

        form = tk.Frame(self)
        form.pack(pady=8)
        tk.Label(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tk.Label(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = tk.Entry(form, width=26)
        self.pass_entry = tk.Entry(form, width=26, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        btns = tk.Frame(self)
        btns.pack(pady=10)
        tk.Button(btns, text="Register", width=14, command=self._do_register).grid(row=0, column=0, padx=6)
        tk.Button(btns, text="Back", width=14, command=lambda: controller.show_frame("Welcome")).grid(row=0, column=1, padx=6)

    def _do_register(self):
        # Get the values first
        username = self.name_entry.get()
        password = self.pass_entry.get()
        
        # --- FIX: Clear the fields BEFORE calling the controller ---
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        # Now pass the data to the controller
        self.controller.handle_register(username, password)


class Login(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Login", font=("Helvetica", 14, "bold")).pack(pady=16)

        form = tk.Frame(self)
        form.pack(pady=8)
        tk.Label(form, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tk.Label(form, text="Password").grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.name_entry = tk.Entry(form, width=26)
        self.pass_entry = tk.Entry(form, width=26, show="*")
        self.name_entry.grid(row=0, column=1, padx=6, pady=6)
        self.pass_entry.grid(row=1, column=1, padx=6, pady=6)

        btns = tk.Frame(self)
        btns.pack(pady=10)
        tk.Button(btns, text="Login", width=14, command=self._do_login).grid(row=0, column=0, padx=6)
        tk.Button(btns, text="Back", width=14, command=lambda: controller.show_frame("Welcome")).grid(row=0, column=1, padx=6)

    def _do_login(self):
        # Get the values first
        username = self.name_entry.get()
        password = self.pass_entry.get()

        # --- FIX: Clear the fields BEFORE calling the controller ---
        self.name_entry.delete(0, 'end')
        self.pass_entry.delete(0, 'end')

        # Now pass the data to the controller
        self.controller.handle_login(username, password)