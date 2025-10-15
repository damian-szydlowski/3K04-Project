import tkinter as tk
from tkinter import messagebox
import json
import os
import base64
import hashlib
import secrets

USER_FILE = "users.json"
MAX_USERS = 10

# ---------------- Security helpers ----------------
def hash_password(password: str, salt: bytes) -> str:
    """Return base64-encoded PBKDF2-HMAC-SHA256 hash."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(dk).decode("utf-8")

def new_salt() -> bytes:
    return secrets.token_bytes(16)

# ---------------- Storage helpers ----------------
def load_users() -> dict:
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict) -> None:
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------------- App ----------------
class DCMLoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM User Access")
        self.geometry("420x320")
        self.resizable(False, False)

        self.users = load_users()  # dict username -> {salt, hash}

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (Welcome, Register, Login, Home):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show("Welcome")

    def show(self, name: str):
        frame = self.frames[name]
        if name == "Welcome":
            frame.refresh_count()
        frame.tkraise()

    # -------- Actions --------
    def register_user(self, username: str, password: str):
        username = username.strip()
        if not username or not password:
            messagebox.showerror("Error", "Both fields are required.")
            return

        if len(self.users) >= MAX_USERS:
            messagebox.showerror("Error", "User limit reached. Maximum of 10 users.")
            return

        if username in self.users:
            messagebox.showerror("Error", "That username is already registered.")
            return

        salt = new_salt()
        pw_hash = hash_password(password, salt)
        self.users[username] = {
            "salt": base64.b64encode(salt).decode("utf-8"),
            "hash": pw_hash,
        }
        save_users(self.users)
        messagebox.showinfo("Success", f"User '{username}' registered.")
        self.show("Welcome")

    def authenticate(self, username: str, password: str):
        username = username.strip()
        rec = self.users.get(username)
        if not rec:
            messagebox.showerror("Error", "Invalid username or password.")
            return

        salt = base64.b64decode(rec["salt"].encode("utf-8"))
        if hash_password(password, salt) == rec["hash"]:
            self.frames["Home"].set_user(username)
            self.show("Home")
        else:
            messagebox.showerror("Error", "Invalid username or password.")

# ---------------- Frames ----------------
class Welcome(tk.Frame):
    def __init__(self, parent, controller: DCMLoginApp):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Welcome to DCM", font=("Helvetica", 16, "bold")).pack(pady=24)
        self.count_var = tk.StringVar(value="Users stored: 0 of 10")
        tk.Label(self, textvariable=self.count_var).pack(pady=4)

        tk.Button(self, text="Login", width=18, command=lambda: controller.show("Login")).pack(pady=8)
        tk.Button(self, text="Register", width=18, command=lambda: controller.show("Register")).pack(pady=4)
        tk.Button(self, text="Exit", width=18, command=controller.destroy).pack(pady=18)

    def refresh_count(self):
        count = len(self.controller.users)
        self.count_var.set(f"Users stored: {count} of {MAX_USERS}")

class Register(tk.Frame):
    def __init__(self, parent, controller: DCMLoginApp):
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
        tk.Button(btns, text="Back", width=14, command=lambda: controller.show("Welcome")).grid(row=0, column=1, padx=6)

    def _do_register(self):
        self.controller.register_user(self.name_entry.get(), self.pass_entry.get())

class Login(tk.Frame):
    def __init__(self, parent, controller: DCMLoginApp):
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
        tk.Button(btns, text="Back", width=14, command=lambda: controller.show("Welcome")).grid(row=0, column=1, padx=6)

    def _do_login(self):
        self.controller.authenticate(self.name_entry.get(), self.pass_entry.get())

class Home(tk.Frame):
    def __init__(self, parent, controller: DCMLoginApp):
        super().__init__(parent)
        self.controller = controller
        self.user_var = tk.StringVar(value="")

        tk.Label(self, textvariable=self.user_var, font=("Helvetica", 14, "bold")).pack(pady=28)
        tk.Button(self, text="Logout", width=14, command=lambda: controller.show("Welcome")).pack(pady=10)

    def set_user(self, username: str):
        self.user_var.set(f"Logged in as: {username}")

# ---------------- Main ----------------
if __name__ == "__main__":
    app = DCMLoginApp()
    app.mainloop()
