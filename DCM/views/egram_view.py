import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
import math
import random
import time

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
        self.start_time = time.time()
        self.annotations = []

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
        
        # FIX: Added clip_on=True to lines so they don't bleed out
        self.line_atr, = self.ax_atr.plot([], [], color="orange", linewidth=1.5, clip_on=True)
        self.line_vent, = self.ax_vent.plot([], [], color="cyan", linewidth=1.5, clip_on=True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Toolbar
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
        # We set initial limits, but _animate enforces them
        ax.set_ylim(-1.0, 6.0)

    def update_font_size(self, size):
        normal_font = ctk.CTkFont(family="Helvetica", size=size)
        self.lbl_select.configure(font=normal_font)
        for rb in self.radio_btns: rb.configure(font=normal_font)
        for btn in [self.btn_start, self.btn_stop, self.back_btn]: btn.configure(font=normal_font)

        title_size = size + 2
        tick_size = size - 2 if size > 10 else 8
        self.ax_atr.set_title("Atrium", fontsize=title_size, fontweight="bold")
        self.ax_vent.set_title("Ventricle", fontsize=title_size, fontweight="bold")
        for ax in [self.ax_atr, self.ax_vent]:
            ax.tick_params(axis='both', which='major', labelsize=tick_size)
        
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
        self.start_time = time.time()
        if hasattr(self, "mock_data"):
             self.mock_data = {"t": [], "atr": [], "vent": [], "markers": []}
        self.line_atr.set_data([], [])
        self.line_vent.set_data([], [])
        for txt in self.annotations: txt.remove()
        self.annotations.clear()
        
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._animate()

    def _stop_graph(self):
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

        curr_time = time.time() - self.start_time
        
        # --- Mock Data ---
        val = math.sin(curr_time * 5)
        raw_vent = 4.5 if val > 0.9 else 2.0 + val
        marker_vent = "VP" if val > 0.9 else "--"

        raw_atr = 2.5 + random.uniform(-0.5, 0.5)
        marker_atr = "AS" if random.random() < 0.05 else "--"

        if not hasattr(self, "mock_data"):
            self.mock_data = {"t": [], "atr": [], "vent": [], "markers": []}
        
        if len(self.mock_data["t"]) > 500: 
            for key in self.mock_data: self.mock_data[key].pop(0)

        self.mock_data["t"].append(curr_time)
        self.mock_data["atr"].append(raw_atr)
        self.mock_data["vent"].append(raw_vent)
        if marker_atr != "--": self.mock_data["markers"].append((curr_time, raw_atr + 0.3, marker_atr, "atr"))
        if marker_vent != "--": self.mock_data["markers"].append((curr_time, raw_vent + 0.3, marker_vent, "vent"))

        try:
            # 1. Update Lines
            self.line_atr.set_data(self.mock_data["t"], self.mock_data["atr"])
            self.line_vent.set_data(self.mock_data["t"], self.mock_data["vent"])

            # 2. Update Markers
            for txt in self.annotations: txt.remove()
            self.annotations.clear()

            visible_window = 5.0
            min_t = curr_time - visible_window
            
            for m_t, m_y, m_text, m_chan in self.mock_data["markers"]:
                if m_t >= min_t: # Optimization: only draw visible markers
                    ax = self.ax_atr if m_chan == "atr" else self.ax_vent
                    color = "red" if m_chan == "atr" else "blue"
                    # FIX: clip_on=True ensures markers don't float outside the axes
                    txt_obj = ax.text(m_t, m_y, m_text, fontsize=8, color=color, ha="center", 
                                      fontweight="bold", clip_on=True)
                    self.annotations.append(txt_obj)

            # 3. FIX: Lock Y-Axis Limits so dragging doesn't move the graph vertically
            self.ax_atr.set_ylim(-1.0, 6.0)
            self.ax_vent.set_ylim(-1.0, 6.0)

            # 4. Auto-Scroll (only if not manually panning)
            if self.toolbar.mode == "":  
                self.ax_atr.set_xlim(curr_time - 5, curr_time)
                self.ax_vent.set_xlim(curr_time - 5, curr_time)

            self.canvas.draw()
            self.after(50, self._animate)
            
        except tk.TclError:
            self.is_running = False
        except Exception as e:
            print(f"Graph Error: {e}")
            self.is_running = False