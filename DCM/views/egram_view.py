import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
import numpy as np
import time
import math
import random

def create_access_buttons(parent_frame, controller):
    """Adds Font Size buttons to a frame"""
    btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    btn_frame.pack(side="right", padx=10)
    
    ctk.CTkButton(btn_frame, text="A-", width=30, command=controller.decrease_font_size).pack(side="left", padx=2)
    ctk.CTkButton(btn_frame, text="A+", width=30, command=controller.increase_font_size).pack(side="left", padx=2)

class EgramView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.is_running = False
        
        # --- Dual Channel Buffer ---
        self.data_size = 500
        self.atr_data = np.zeros(self.data_size)
        self.vent_data = np.zeros(self.data_size)
        
        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # --- 1. Top Controls ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        create_access_buttons(controls_frame, controller)

        self.channel_var = ctk.StringVar(value="Both")
        self.lbl_select = ctk.CTkLabel(controls_frame, text="Select Channel:")
        self.lbl_select.pack(side="left", padx=10)
        
        self.radio_btns = []
        for m in ["Atrium", "Ventricle", "Both"]:
            rb = ctk.CTkRadioButton(controls_frame, text=m, variable=self.channel_var, value=m, 
                               command=self._update_visibility)
            rb.pack(side="left", padx=10)
            self.radio_btns.append(rb)

        self.btn_stop = ctk.CTkButton(controls_frame, text="Stop", fg_color="red", width=80, state="disabled", command=self._stop_graph)
        self.btn_stop.pack(side="right", padx=10)
        
        self.btn_start = ctk.CTkButton(controls_frame, text="Start Stream", fg_color="green", width=100, command=self._start_graph)
        self.btn_start.pack(side="right", padx=10)

        # --- 2. Graph Area ---
        graph_container = ctk.CTkFrame(self, fg_color="transparent")
        graph_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        graph_container.grid_rowconfigure(0, weight=1)
        graph_container.grid_columnconfigure(0, weight=1)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax_atr = self.fig.add_subplot(211) 
        self.ax_vent = self.fig.add_subplot(212, sharex=self.ax_atr) 
        self.fig.subplots_adjust(hspace=0.4) 

        self._style_plot(self.ax_atr, "Atrium")
        self._style_plot(self.ax_vent, "Ventricle")
        
        # Initialize Plot Lines (Both active)
        self.line_atr, = self.ax_atr.plot(np.arange(self.data_size), self.atr_data, color="orange", linewidth=1.5)
        self.line_vent, = self.ax_vent.plot(np.arange(self.data_size), self.vent_data, color="cyan", linewidth=1.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.toolbar_frame = ctk.CTkFrame(graph_container)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        # --- 3. Bottom Controls ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self.back_btn = ctk.CTkButton(bottom_frame, text="Back to Main Menu", width=200, command=self._go_back)
        self.back_btn.pack(side="bottom")

    def _style_plot(self, ax, title):
        ax.set_title(title, fontsize=10, color="#333", fontweight="bold")
        ax.set_facecolor('#f0f0f0') 
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xlim(0, self.data_size)
        ax.set_ylim(-1.0, 6.0)

    def update_font_size(self, size):
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        self.lbl_select.configure(font=normal_font)
        for rb in self.radio_btns: rb.configure(font=normal_font)
        for btn in [self.btn_start, self.btn_stop, self.back_btn]: btn.configure(font=normal_font)
        
        try:
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception: pass

    def _update_visibility(self):
        mode = self.channel_var.get()
        self.ax_atr.set_visible(mode in ["Atrium", "Both"])
        self.ax_vent.set_visible(mode in ["Ventricle", "Both"])
        try: self.canvas.draw()
        except Exception: pass

    def _start_graph(self):
        if self.controller.connected:
            self.controller.serial_manager.start_egram_stream()
        
        # Reset Buffers
        self.atr_data = np.zeros(self.data_size)
        self.vent_data = np.zeros(self.data_size)
        self.line_atr.set_ydata(self.atr_data)
        self.line_vent.set_ydata(self.vent_data)
        
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._animate()

    def _stop_graph(self):
        if self.controller.connected:
            self.controller.serial_manager.stop_egram_stream()

        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _go_back(self):
        self._stop_graph()
        self.controller.show_frame("MainFrame")

    def destroy(self):
        self.is_running = False
        super().destroy()

    def _animate(self):
        if not self.is_running or not self.winfo_exists():
            return

        # 1. Read Tuple (Atr, Vent)
        new_sample = None
        if self.controller.connected:
            new_sample = self.controller.serial_manager.read_egram_sample()
        else:
            # Mock Data
            curr_time = time.time()
            new_sample = (
                2.5 + math.sin(curr_time * 5) + random.uniform(-0.1, 0.1),
                2.0 + math.cos(curr_time * 5) + random.uniform(-0.1, 0.1)
            )

        if new_sample:
            # Unpack
            new_atr, new_vent = new_sample
            
            # --- Update Atrial Buffer ---
            self.atr_data[:-1] = self.atr_data[1:]
            self.atr_data[-1] = new_atr
            self.line_atr.set_ydata(self.atr_data)

            # --- Update Ventricular Buffer ---
            self.vent_data[:-1] = self.vent_data[1:]
            self.vent_data[-1] = new_vent
            self.line_vent.set_ydata(self.vent_data)
            
            self.canvas.draw()
        
        self.after(20, self._animate)