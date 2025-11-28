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
        # Buffers for plotting
        self.t_data = []
        self.atr_data = []
        self.vent_data = []
        self.marker_points = []


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

        # Reset plotting buffers
        self.t_data.clear()
        self.atr_data.clear()
        self.vent_data.clear()
        self.marker_points.clear()

        # Clear any old text annotations
        for txt in self.annotations:
            txt.remove()
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

        serial_mgr = self.controller.serial_manager
        egram_model = getattr(self.controller, "egram_model", None)

        # Drain all complete frames that are currently waiting
        while True:
            sample = serial_mgr.read_egram_sample()
            if sample is None:
                break

            raw_val, marker = sample
            t_rel = time.time() - self.start_time

            # Save to shared model for later saving or analysis
            if egram_model is not None:
                egram_model.append_sample(raw_val, marker)

            # Append to local plotting buffers
            self.t_data.append(t_rel)
            # We only have ventricular raw data from the spec
            self.vent_data.append(raw_val)
            # For now atrial trace is empty or you can mirror the same value
            self.atr_data.append(0.0)

            if marker != "--":
                self.marker_points.append((t_rel, raw_val, marker, "vent"))

        # If no new data arrived this frame, just schedule the next call
        if not self.t_data:
            self.after(20, self._animate)
            return

        # Keep only a sliding window of recent data
        visible_window = 5.0   # seconds
        min_t = self.t_data[-1] - visible_window

        # Find first index that is inside the window
        first_idx = 0
        while first_idx < len(self.t_data) and self.t_data[first_idx] < min_t:
            first_idx += 1

        t_view = self.t_data[first_idx:]
        atr_view = self.atr_data[first_idx:]
        vent_view = self.vent_data[first_idx:]

        # Update line data
        self.line_atr.set_data(t_view, atr_view)
        self.line_vent.set_data(t_view, vent_view)

        # Redraw markers
        for txt in self.annotations:
            txt.remove()
        self.annotations.clear()

        for (m_t, m_y, m_text, m_chan) in self.marker_points:
            if m_t >= min_t:
                ax = self.ax_vent if m_chan == "vent" else self.ax_atr
                color = "blue"
                txt_obj = ax.text(
                    m_t, m_y, m_text,
                    fontsize=8, color=color, ha="center",
                    fontweight="bold", clip_on=True,
                )
                self.annotations.append(txt_obj)

        # Set fixed y limits or derive from data
        if vent_view:
            v_min = min(vent_view)
            v_max = max(vent_view)
            margin = max(10, 0.1 * max(abs(v_min), abs(v_max)))
            self.ax_vent.set_ylim(v_min - margin, v_max + margin)
        else:
            self.ax_vent.set_ylim(-1.0, 6.0)

        self.ax_atr.set_ylim(-1.0, 6.0)

        # Auto scroll x axis if user is not panning
        if self.toolbar.mode == "":
            t_now = self.t_data[-1]
            self.ax_atr.set_xlim(t_now - visible_window, t_now)
            self.ax_vent.set_xlim(t_now - visible_window, t_now)

        try:
            self.canvas.draw()
        except tk.TclError:
            self.is_running = False
            return

        # Schedule next frame
        self.after(20, self._animate)
