from ui.theme import HEADING_FONT
from ui.theme import BODY_FONT
from ui.theme import TITLE_FONT
from ui.theme import SMALL_FONT
from ui.theme import VERYSMALL_FONT
import queue
import config
import psutil
import datetime
import math
import customtkinter as ctk
import tkinter as tk
import os
from PIL import Image, ImageTk

from ui import theme
from utils.logger import logger


class CircularMeter(ctk.CTkFrame):
    """A circular system-usage meter drawn on a Tkinter Canvas."""

    def __init__(
        self,
        master,
        title,
        value=0,
        size=104,
        background="#071A2B",
        track_color="#163247",
        accent_color="#20D8F2",
        text_color="#EAFBFF",
    ):
        super().__init__(
            master,
            fg_color=background,
            corner_radius=12,
        )

        self.title = title
        self.size = size
        self.background = background
        self.track_color = track_color
        self.accent_color = accent_color
        self.text_color = text_color

        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=background,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(padx=5, pady=5)

        self.set_value(value)

    def set_value(self, value):
        """Update the meter. The value should be between 0 and 100, or None if unavailable."""
        self.canvas.delete("all")

        center = self.size / 2
        margin = 8
        diameter = self.size - margin * 2

        # Background ring
        self.canvas.create_arc(
            margin,
            margin,
            margin + diameter,
            margin + diameter,
            start=90,
            extent=-359.9,
            style="arc",
            outline=self.track_color,
            width=7,
        )

        display_text = "N/A"
        if value is not None:
            try:
                num_val = max(0, min(100, float(value)))
                display_text = f"{num_val:.0f}%"
                if num_val > 0:
                    self.canvas.create_arc(
                        margin,
                        margin,
                        margin + diameter,
                        margin + diameter,
                        start=90,
                        extent=-(num_val / 100) * 359.9,
                        style="arc",
                        outline=self.accent_color,
                        width=7,
                    )
            except (ValueError, TypeError):
                display_text = "N/A"

        # Meter title
        self.canvas.create_text(
            center,
            center - 10,
            text=self.title,
            fill=self.text_color,
            font=(VERYSMALL_FONT[0], VERYSMALL_FONT[1], "bold"),
        )

        # Percentage or N/A
        self.canvas.create_text(
            center,
            center + 9,
            text=display_text,
            fill=self.text_color,
            font=(SMALL_FONT[0], SMALL_FONT[1], "bold"),
        )


class MainWindow:

    def __init__(
        self,
        on_close_callback=None,
        on_start_callback=None,
        on_stop_callback=None,
    ):
        self.on_close_callback = on_close_callback
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback
        self._is_running = True
        self._anim_timer_id = None
        self._glow_timer_id = None
        self._glow_angle = 0.0
        self._chevron_step = 0
        self._chevron_timer = 0
        self._radar_sweep = 0.0
        self._ping_counter = 0
        self._current_status = "READY"
        self._cached_wifi_str = "GALAXY 5G (88%)"
        self._telemetry_msg = "[CORE: 15% LOAD]   •   [RAM: 8.2GB FREE]   •   [WI-FI: GALAXY 5G (88%)]   •   [UPTIME: 2h 55m]   •   [SECURITY: NOMINAL]       "
        self._ticker_tw = 680
        self._wifi_check_counter = 0
        self._reticle_angle = 0.0
        self._wave_phase = 0.0
        self._center_corner_brackets = []
        self._input_phase = 0.0
        self._output_phase = 0.0
        self._input_active = False
        self._output_active = False
        self._dashboard_timer_id = None
        self._ui_queue = queue.Queue()
        self._ui_queue_timer_id = None

        self.window = ctk.CTk()
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        self.setup_window()
        self.create_layout()
        self.create_widgets()

        self.update_dashboard()
        self.update_panel_glow_animation()
        self._process_ui_queue()

    # =========================================================
    # WINDOW SETUP
    # =========================================================

    def setup_window(self):
        self.window.title(config.APP_NAME)
        self.window.geometry(
            f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}"
        )

        self.window.configure(fg_color="#061421")
        ctk.set_appearance_mode("dark")

        # Set window titlebar & taskbar icon
        icon_path = config.ASSETS_DIR / "jarvis_ironman.ico"
        if not icon_path.is_file():
            icon_path = config.ASSETS_DIR / "jarvis.ico"
        if icon_path.is_file():
            try:
                self.window.iconbitmap(str(icon_path))
            except Exception:
                pass

    # =========================================================
    # CLOSE WINDOW
    # =========================================================

    def on_close(self):
        if not self._is_running:
            return
        self._is_running = False

        if self._dashboard_timer_id:
            try:
                self.window.after_cancel(self._dashboard_timer_id)
            except (tk.TclError, ValueError):
                pass
            self._dashboard_timer_id = None

        if self._anim_timer_id:
            try:
                self.window.after_cancel(self._anim_timer_id)
            except (tk.TclError, ValueError):
                pass
            self._anim_timer_id = None

        if self._glow_timer_id:
            try:
                self.window.after_cancel(self._glow_timer_id)
            except (tk.TclError, ValueError):
                pass
            self._glow_timer_id = None

        if self._ui_queue_timer_id:
            try:
                self.window.after_cancel(self._ui_queue_timer_id)
            except (tk.TclError, ValueError):
                pass
            self._ui_queue_timer_id = None

        try:
            if self.on_close_callback:
                self.on_close_callback()
        except Exception:
            logger.exception("Error executing on_close_callback during shutdown.")
        finally:
            try:
                self.window.destroy()
            except (tk.TclError, Exception):
                pass

    # =========================================================
    # LAYOUT
    # =========================================================

    def create_layout(self):
        panel_color = "#081B2B"

        self.header_frame = ctk.CTkFrame(
            self.window,
            fg_color=panel_color,
            corner_radius=0,
        )

        self.left_frame = ctk.CTkFrame(
            self.window,
            fg_color=panel_color,
            corner_radius=14,
            border_width=2,
            border_color="#12364A",
        )

        self.center_frame = ctk.CTkFrame(
            self.window,
            fg_color=panel_color,
            corner_radius=14,
            border_width=2,
            border_color="#12364A",
        )

        self.right_frame = ctk.CTkFrame(
            self.window,
            fg_color=panel_color,
            corner_radius=14,
            border_width=2,
            border_color="#12364A",
        )

        self.footer_frame = ctk.CTkFrame(
            self.window,
            fg_color=panel_color,
            corner_radius=0,
        )

        # Header
        self.header_frame.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=0.08,
        )

        # Left panel: system monitor
        self.left_frame.place(
            relx=0.015,
            rely=0.10,
            relwidth=0.23,
            relheight=0.82,
        )

        # Center panel
        self.center_frame.place(
            relx=0.26,
            rely=0.10,
            relwidth=0.48,
            relheight=0.82,
        )

        # Right panel
        self.right_frame.place(
            relx=0.755,
            rely=0.10,
            relwidth=0.23,
            relheight=0.82,
        )

        # Footer
        self.footer_frame.place(
            relx=0,
            rely=0.94,
            relwidth=1,
            relheight=0.06,
        )

    # =========================================================
    # CREATE WIDGETS
    # =========================================================

    def create_widgets(self):
        self.create_header()
        self.create_left_panel()
        self.create_center_panel()
        self.create_right_panel()
        self.create_footer()

    # =========================================================
    # HEADER
    # =========================================================

    def create_header(self):
        panel_color = "#081B2B"

        # -----------------------------------------------------
        # TOP-LEFT: MARK VII RADAR & STATUS
        # -----------------------------------------------------
        self.top_left_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
        )
        self.top_left_frame.place(
            relx=0.015,
            rely=0.5,
            anchor="w",
        )

        self.radar_canvas = tk.Canvas(
            self.top_left_frame,
            width=22,
            height=22,
            bg=panel_color,
            highlightthickness=0,
            bd=0,
        )
        self.radar_canvas.pack(side="left", padx=(0, 8))

        self.top_left_label = ctk.CTkLabel(
            self.top_left_frame,
            text="SYSTEMS ONLINE",
            text_color="#20E6A0",
            font=("Consolas", 11, "bold"),
        )
        self.top_left_label.pack(side="left")

        # -----------------------------------------------------
        # CENTER: FLANKING CYBER CHEVRONS + J.A.R.V.I.S TITLE
        # -----------------------------------------------------
        self.title_container = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
        )
        self.title_container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        # Left Chevrons: ◄ ◄ ◄
        self.left_chevron_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(
                self.title_container,
                text="◄",
                text_color="#103347",
                font=("Consolas", 18, "bold"),
            )
            lbl.pack(side="left", padx=2)
            self.left_chevron_labels.append(lbl)

        # Main Title: [ J . A . R . V . I . S ]
        self.title_label = ctk.CTkLabel(
            self.title_container,
            text="   J . A . R . V . I . S   ",
            text_color="#EAFBFF",
            font=TITLE_FONT,
        )
        self.title_label.pack(side="left", padx=4)

        # Right Chevrons: ► ► ►
        self.right_chevron_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(
                self.title_container,
                text="►",
                text_color="#103347",
                font=("Consolas", 18, "bold"),
            )
            lbl.pack(side="left", padx=2)
            self.right_chevron_labels.append(lbl)

        # -----------------------------------------------------
        # TOP-RIGHT: REAL-TIME NEURAL ENGINE PING
        # -----------------------------------------------------
        self.top_right_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
        )
        self.top_right_frame.place(
            relx=0.985,
            rely=0.5,
            anchor="e",
        )

        self.ping_indicator = ctk.CTkLabel(
            self.top_right_frame,
            text="⚡",
            text_color="#00DDF5",
            font=("Consolas", 12),
        )
        self.ping_indicator.pack(side="left", padx=(0, 5))

        self.top_right_label = ctk.CTkLabel(
            self.top_right_frame,
            text="NEURAL ENGINE: 23ms",
            text_color="#00DDF5",
            font=("Consolas", 11, "bold"),
        )
        self.top_right_label.pack(side="left")

    # =========================================================
    # LEFT PANEL: SYSTEM MONITOR
    # =========================================================

    def create_left_panel(self):
        title = ctk.CTkLabel(
            self.left_frame,
            text="SYSTEM MONITOR",
            text_color="#73E8F7",
            font=BODY_FONT,
        )
        title.pack(pady=(18, 8))

        subtitle = ctk.CTkLabel(
            self.left_frame,
            text="LIVE SYSTEM USAGE",
            text_color="#6D91A6",
            font=VERYSMALL_FONT,
        )
        subtitle.pack(pady=(0, 12))

        # Circular meters are stacked vertically.
        self.cpu_meter = CircularMeter(
            self.left_frame,
            title="CPU",
            size=108,
        )
        self.cpu_meter.pack(pady=6)

        self.ram_meter = CircularMeter(
            self.left_frame,
            title="RAM",
            size=108,
        )
        self.ram_meter.pack(pady=6)

        self.battery_meter = CircularMeter(
            self.left_frame,
            title="BATTERY",
            size=108,
        )
        self.battery_meter.pack(pady=6)

        self.battery_note = ctk.CTkLabel(
            self.left_frame,
            text="",
            text_color="#6D91A6",
            font=VERYSMALL_FONT,
        )
        self.battery_note.pack(pady=(0, 8))

        # Date and time at the bottom of the monitor panel.
                # Date and time display
        self.clock_frame = ctk.CTkFrame(
            self.left_frame,
            fg_color="transparent",
        )
        self.clock_frame.pack(
            fill="x",
            padx=8,
            pady=(10, 12),
        )

        self.clock_row = ctk.CTkFrame(
            self.clock_frame,
            fg_color="transparent",
        )
        self.clock_row.pack()

        self.time_label = ctk.CTkLabel(
            self.clock_row,
            text="--:--",
            text_color="#00DDF5",
            font=("Consolas", 38, "bold"),
        )
        self.time_label.pack(side="left")

        self.seconds_label = ctk.CTkLabel(
            self.clock_row,
            text=":--",
            text_color="#087C8D",
            font=("Consolas", 17),
        )
        self.seconds_label.pack(
            side="left",
            anchor="s",
            padx=(2, 0),
            pady=(0, 7),
        )

        self.date_label = ctk.CTkLabel(
            self.clock_frame,
            text="WEEKDAY, 00. MONTH 0000",
            text_color="#9AAAB6",
            font=SMALL_FONT,
        )
        self.date_label.pack(pady=(0, 4))

    # =========================================================
    # CENTER PANEL
    # =========================================================

    def create_center_panel(self):
        panel_color = "#081B2B"

        # -----------------------------------------------------
        # 1. TACTICAL CORNER BRACKETS (┌ ┐ and └ ┘)
        # -----------------------------------------------------
        self._center_corner_brackets = []
        bracket_defs = [
            ("┌", 0.015, 0.015, "nw"),
            ("┐", 0.985, 0.015, "ne"),
            ("└", 0.015, 0.985, "sw"),
            ("┘", 0.985, 0.985, "se"),
        ]
        for char, rx, ry, anch in bracket_defs:
            b_lbl = ctk.CTkLabel(
                self.center_frame,
                text=char,
                font=("Consolas", 18, "bold"),
                text_color="#00DDF5",
            )
            b_lbl.place(relx=rx, rely=ry, anchor=anch)
            self._center_corner_brackets.append(b_lbl)

        # -----------------------------------------------------
        # 2. MARK VII REACTOR DIAGNOSTICS BANNER (Above Reactor)
        # -----------------------------------------------------
        self.diagnostics_banner = ctk.CTkLabel(
            self.center_frame,
            text="CORE OUTPUT: 3.2 GJ/s   •   THERMAL: 34°C   •   COGNITION: NOMINAL",
            font=("Consolas", 11, "bold"),
            text_color="#73E8F7",
        )
        self.diagnostics_banner.place(
            relx=0.5,
            rely=0.06,
            anchor="center",
        )

        # -----------------------------------------------------
        # 3. ROTATING HUD RETICLE CANVAS & ARC REACTOR CORE
        # -----------------------------------------------------
        self.reticle_canvas = tk.Canvas(
            self.center_frame,
            width=480,
            height=480,
            bg=panel_color,
            highlightthickness=0,
            bd=0,
        )
        self.reticle_canvas.place(
            relx=0.5,
            rely=0.44,
            anchor="center",
        )
        self.reactor_label = None

        # -----------------------------------------------------
        # 4. LIVE AUDIO SPEECH WAVEFORM CANVAS (Between Reactor & Status)
        # -----------------------------------------------------
        self.speech_wave_canvas = tk.Canvas(
            self.center_frame,
            width=540,
            height=44,
            bg=panel_color,
            highlightthickness=0,
            bd=0,
        )
        self.speech_wave_canvas.place(
            relx=0.5,
            rely=0.74,
            anchor="center",
        )

        # -----------------------------------------------------
        # 5. SYSTEM STATUS LABEL
        # -----------------------------------------------------
        self.status_label = ctk.CTkLabel(
            self.center_frame,
            text="SYSTEM STATUS : READY",
            text_color="#73E8F7",
            font=HEADING_FONT,
        )
        self.status_label.place(
            relx=0.5,
            rely=0.84,
            anchor="center",
        )

        self.setup_reactor_animation()

    def setup_reactor_animation(self):
        """Loads the animated Arc Reactor frames and starts the smooth playback loop."""
        self._reactor_size = 360
        self._animation_frames = []
        self._current_frame = 0
        self._anim_timer_id = None
        self._frame_delay = 41  # 24 FPS (~41 ms per frame)

        # 1. Candidate frame directories (pre-rendered transparent PNG sequence)
        frame_dirs = [
            config.ANIMATION_DIR / "frames",
            config.ANIMATIONS_DIR / "frames",
        ]

        loaded_images = []
        for d in frame_dirs:
            if d.is_dir():
                try:
                    files = sorted(
                        [
                            p
                            for p in d.iterdir()
                            if p.is_file() and p.suffix.lower() == ".png"
                        ]
                    )
                except OSError:
                    continue
                if files:
                    for f in files:
                        try:
                            im = Image.open(f).convert("RGBA")
                            loaded_images.append(im)
                        except (OSError, ValueError):
                            pass
                    if loaded_images:
                        break

        # 2. Secondary fallback: animated GIF
        if not loaded_images:
            gif_candidates = [
                config.ANIMATION_DIR / "arc_reactor.gif",
                config.ANIMATIONS_DIR / "arc_reactor.gif",
            ]
            for g in gif_candidates:
                if g.is_file():
                    try:
                        from PIL import ImageSequence
                        gif = Image.open(g)
                        for frame in ImageSequence.Iterator(gif):
                            loaded_images.append(frame.copy().convert("RGBA"))
                        if loaded_images:
                            break
                    except (OSError, ValueError):
                        pass

        if not loaded_images:
            self.reticle_canvas.create_text(
                240, 240,
                text="[ ARC REACTOR ANIMATION NOT FOUND ]\nPlease check assets/animation/frames/",
                fill="#FF713E",
                font=("Consolas", 12, "bold"),
            )
            return

        # Convert all frames to PhotoImage
        self._animation_photos = []
        for im in loaded_images:
            try:
                if im.size != (self._reactor_size, self._reactor_size):
                    im = im.resize((self._reactor_size, self._reactor_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(im)
                self._animation_photos.append(photo)
            except Exception:
                pass

        if not self._animation_photos:
            self.reticle_canvas.create_text(
                240, 240,
                text="[ ARC REACTOR ANIMATION NOT FOUND ]\nPlease check assets/animation/frames/",
                fill="#FF713E",
                font=("Consolas", 12, "bold"),
            )
            return

        self._total_frames = len(self._animation_photos)

        # Draw native transparent image directly onto reticle_canvas (no subwindow blocking!)
        self._reactor_canvas_img_id = self.reticle_canvas.create_image(
            240, 240,
            image=self._animation_photos[0],
            tags="reactor_core",
        )

        # Start non-blocking animation loop
        if self._is_running:
            self._anim_timer_id = self.window.after(
                self._frame_delay, self.update_reactor_animation
            )

    def update_reactor_animation(self):
        """Advances the Arc Reactor animation by one frame and loops seamlessly."""
        if not self._is_running or not self._animation_photos or not hasattr(self, "_reactor_canvas_img_id") or not self._reactor_canvas_img_id:
            return

        self._current_frame = (self._current_frame + 1) % self._total_frames
        try:
            self.reticle_canvas.itemconfig(
                self._reactor_canvas_img_id,
                image=self._animation_photos[self._current_frame],
            )
        except Exception:
            pass

        if self._is_running:
            self._anim_timer_id = self.window.after(
                self._frame_delay, self.update_reactor_animation
            )

    def update_panel_glow_animation(self):
        """Animates a dynamic glowing/shining border on the left and right HUD panels."""
        if not self._is_running:
            return

        status = getattr(self, "_current_status", "READY").upper()

        # Dynamic frequency and color palette according to J.A.R.V.I.S. system state
        if "LISTENING" in status:
            step = 0.12
            speed_ms = 28
            base_rgb = (10, 48, 68)
            peak_rgb = (40, 248, 255)
        elif "THINKING" in status or "PROCESSING" in status:
            step = 0.15
            speed_ms = 25
            base_rgb = (15, 52, 78)
            peak_rgb = (0, 220, 255)
        elif "IDLE" in status or "HALTED" in status or "OFFLINE" in status:
            step = 0.035
            speed_ms = 45
            base_rgb = (9, 26, 36)
            peak_rgb = (24, 72, 98)
        else:  # READY / ONLINE / DEFAULT
            step = 0.06
            speed_ms = 35
            base_rgb = (12, 40, 56)
            peak_rgb = (0, 230, 255)

        self._glow_angle = (self._glow_angle + step) % (2.0 * math.pi)

        # Smooth sine ease (emphasizing the peak shine)
        raw_val = (math.sin(self._glow_angle) + 1.0) / 2.0
        val = raw_val ** 1.6

        r = int(base_rgb[0] + (peak_rgb[0] - base_rgb[0]) * val)
        g = int(base_rgb[1] + (peak_rgb[1] - base_rgb[1]) * val)
        b = int(base_rgb[2] + (peak_rgb[2] - base_rgb[2]) * val)
        glow_color = f"#{r:02x}{g:02x}{b:02x}"

        try:
            self.left_frame.configure(border_color=glow_color)
            self.center_frame.configure(border_color=glow_color)
            self.right_frame.configure(border_color=glow_color)
            if hasattr(self, "footer_neon_line"):
                self.footer_neon_line.configure(bg=glow_color)
            for b_lbl in getattr(self, "_center_corner_brackets", []):
                b_lbl.configure(text_color=glow_color)
        except Exception:
            pass

        # Update Header HUD effects (radar blip, cascading chevrons, neural ping)
        self._update_header_effects(status)

        # Update Footer Ticker Marquee
        self._update_footer_ticker()

        # Update Center Panel Reticle, Waveform & Diagnostics Banner
        self._update_center_panel_effects(status)

        # Update Input / Output Activity dynamic sound waves
        self._update_io_activity_waves(status)

        if self._is_running:
            self._glow_timer_id = self.window.after(
                speed_ms, self.update_panel_glow_animation
            )

    def _update_io_activity_waves(self, status):
        """Animates INPUT wave when listening to user and OUTPUT wave when Jarvis speaks."""
        is_input = ("LISTENING" in status) or getattr(self, "_input_active", False)
        is_output = ("SPEAKING" in status) or getattr(self, "_output_active", False)

        # Smoothly advance wave phases
        self._input_phase = (self._input_phase + (0.16 if is_input else 0.04)) % (2.0 * math.pi)
        self._output_phase = (self._output_phase + (0.18 if is_output else 0.04)) % (2.0 * math.pi)

        if hasattr(self, "input_wave") and self.input_wave.winfo_exists():
            input_color = "#00F0FF" if is_input else "#0D4A5E"
            self.draw_sound_wave(self.input_wave, input_color, self._input_phase, active=is_input)

        if hasattr(self, "output_wave") and self.output_wave.winfo_exists():
            output_color = "#38A0FF" if is_output else "#123057"
            self.draw_sound_wave(self.output_wave, output_color, self._output_phase, active=is_output)

    def _update_center_panel_effects(self, status):
        """Updates rotating HUD reticle, live speech waveform, and diagnostics banner."""
        # 1. Rotating HUD Reticle & Compass Rings (Around Arc Reactor)
        if hasattr(self, "reticle_canvas") and self.reticle_canvas.winfo_exists():
            try:
                self.reticle_canvas.delete("hud_element")
                cx, cy = 240, 240
                r_inner = 188
                r_outer = 208

                # Slow counter-rotation
                self._reticle_angle = (self._reticle_angle - 0.015) % (2.0 * math.pi)
                rot = self._reticle_angle

                # Inner glowing reactor rim
                self.reticle_canvas.create_oval(
                    cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                    outline="#164A5E", width=1.5, tags="hud_element"
                )

                # Concentric outer dashed measurement ring
                self.reticle_canvas.create_oval(
                    cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                    outline="#00DDF5", dash=(4, 6), width=1.5, tags="hud_element"
                )

                # Outer arc accents (4 corner segments)
                for base_deg in (30, 120, 210, 300):
                    start_ang = math.degrees(rot) + base_deg
                    self.reticle_canvas.create_arc(
                        cx - (r_outer + 12), cy - (r_outer + 12),
                        cx + (r_outer + 12), cy + (r_outer + 12),
                        start=start_ang, extent=30, style="arc",
                        outline="#20E6A0", width=2.5, tags="hud_element"
                    )

                # Degree ticks (000°, 090°, 180°, 270°)
                for deg in (0, 90, 180, 270):
                    ang = rot + math.radians(deg)
                    tx = cx + r_outer * math.cos(ang)
                    ty = cy + r_outer * math.sin(ang)
                    self.reticle_canvas.create_text(
                        tx, ty, text=f"{deg:03d}°",
                        font=("Consolas", 9, "bold"), fill="#00FFFF", tags="hud_element"
                    )

                # Tactical corner reticles [ + ]
                for dx, dy in ((-215, -215), (215, -215), (-215, 215), (215, 215)):
                    px, py = cx + dx, cy + dy
                    # Crosshairs
                    self.reticle_canvas.create_line(px - 8, py, px + 8, py, fill="#00DDF5", width=1.5, tags="hud_element")
                    self.reticle_canvas.create_line(px, py - 8, px, py + 8, fill="#00DDF5", width=1.5, tags="hud_element")
                    # Corner brackets
                    bx = 7 if dx > 0 else -7
                    by = 7 if dy > 0 else -7
                    self.reticle_canvas.create_line(px - bx, py - by, px - bx, py + by, fill="#20E6A0", width=1.5, tags="hud_element")
                    self.reticle_canvas.create_line(px - bx, py - by, px + bx, py - by, fill="#20E6A0", width=1.5, tags="hud_element")
            except Exception:
                pass

        # 2. Live Audio Speech Waveform (Between Reactor & Status)
        if hasattr(self, "speech_wave_canvas") and self.speech_wave_canvas.winfo_exists():
            try:
                self.speech_wave_canvas.delete("all")
                width = 540
                cy = 22

                if "SPEAKING" in status:
                    amp = 18.0
                    step_p = 0.18
                elif "LISTENING" in status:
                    amp = 14.0
                    step_p = 0.14
                elif "THINKING" in status or "PROCESSING" in status:
                    amp = 10.0
                    step_p = 0.22
                elif "IDLE" in status or "HALTED" in status or "OFFLINE" in status:
                    amp = 2.0
                    step_p = 0.04
                else:  # READY / ONLINE
                    amp = 4.5
                    step_p = 0.08

                self._wave_phase = (self._wave_phase + step_p) % (2.0 * math.pi)
                ph = self._wave_phase

                pts1 = []
                pts2 = []
                for x in range(0, width + 1, 4):
                    # Envelope window so wave tapers seamlessly to zero at endpoints
                    env = math.sin(math.pi * x / width)
                    y1 = cy + amp * env * math.sin(0.04 * x + ph)
                    y2 = cy + (amp * 0.7) * env * math.sin(0.06 * x - ph)
                    pts1.extend([x, y1])
                    pts2.extend([x, y2])

                # Draw dual-sine waveforms
                self.speech_wave_canvas.create_line(pts1, fill="#00DDF5", width=2, smooth=True)
                self.speech_wave_canvas.create_line(pts2, fill="#287FEA", width=1.5, smooth=True)
            except Exception:
                pass

        # 3. Mark VII Reactor Diagnostics Banner (Above Reactor)
        if hasattr(self, "diagnostics_banner"):
            try:
                if "LISTENING" in status:
                    diag_text = "CORE OUTPUT: 5.4 GJ/s   •   THERMAL: 36°C   •   ACOUSTIC SENSORS: 100%"
                    diag_col = "#20E6A0"
                elif "THINKING" in status or "PROCESSING" in status:
                    diag_text = "CORE OUTPUT: 8.8 GJ/s   •   THERMAL: 41°C   •   NEURAL SYNC: 99.4%"
                    diag_col = "#00DDF5"
                elif "SPEAKING" in status:
                    diag_text = "CORE OUTPUT: 6.2 GJ/s   •   THERMAL: 38°C   •   VOCAL SYNTHESIS: ONLINE"
                    diag_col = "#73E8F7"
                elif "IDLE" in status or "HALTED" in status or "OFFLINE" in status:
                    diag_text = "CORE OUTPUT: 0.8 GJ/s   •   THERMAL: 27°C   •   STANDBY MODE"
                    diag_col = "#FF713E"
                else:
                    diag_text = "CORE OUTPUT: 3.2 GJ/s   •   THERMAL: 34°C   •   COGNITION: NOMINAL"
                    diag_col = "#73E8F7"

                self.diagnostics_banner.configure(text=diag_text, text_color=diag_col)
            except Exception:
                pass

    def _update_footer_ticker(self):
        """Scrolls the sci-fi telemetry ticker canvas smoothly across the footer."""
        if not hasattr(self, "ticker_canvas") or not self.ticker_canvas.winfo_exists():
            return

        try:
            speed = 2
            self.ticker_canvas.move(self._ticker_t1, -speed, 0)
            self.ticker_canvas.move(self._ticker_t2, -speed, 0)

            c1 = self.ticker_canvas.coords(self._ticker_t1)[0]
            c2 = self.ticker_canvas.coords(self._ticker_t2)[0]
            tw = self._ticker_tw

            if c1 <= -tw:
                self.ticker_canvas.coords(self._ticker_t1, c2 + tw, 14)
                self.ticker_canvas.itemconfigure(self._ticker_t1, text=self._telemetry_msg)
                bbox = self.ticker_canvas.bbox(self._ticker_t1)
                if bbox:
                    self._ticker_tw = max(400, bbox[2] - bbox[0])
            if c2 <= -tw:
                self.ticker_canvas.coords(self._ticker_t2, self.ticker_canvas.coords(self._ticker_t1)[0] + tw, 14)
                self.ticker_canvas.itemconfigure(self._ticker_t2, text=self._telemetry_msg)
        except Exception:
            pass

    def _update_header_effects(self, status):
        """Updates radar blip, chevron cascading wave, and neural ping in the header."""
        # 1. Pulsing Radar Blip (Top Left)
        if hasattr(self, "radar_canvas") and self.radar_canvas.winfo_exists():
            try:
                self.radar_canvas.delete("all")
                self._radar_sweep = (self._radar_sweep + 0.08) % 1.0
                r = 3.0 + 7.0 * self._radar_sweep
                alpha_idx = min(int(self._radar_sweep * 10), 9)
                ring_colors = [
                    "#20E6A0", "#1BD08F", "#17BA7E", "#14A46D", "#118E5C",
                    "#0D784B", "#0A623A", "#084C2A", "#06361D", "#042010"
                ]
                ring_color = ring_colors[alpha_idx]
                is_active = not ("IDLE" in status or "HALTED" in status or "OFFLINE" in status)
                dot_color = "#20E6A0" if is_active else "#FF713E"
                if not is_active:
                    ring_color = "#55251B"

                # Draw expanding radar ring & center dot
                self.radar_canvas.create_oval(11 - r, 11 - r, 11 + r, 11 + r, outline=ring_color, width=1)
                self.radar_canvas.create_oval(11 - 2.5, 11 - 2.5, 11 + 2.5, 11 + 2.5, fill=dot_color, outline="")
            except Exception:
                pass

        # 2. Flanking Chevrons Cascading Wave Towards Center
        self._chevron_timer += 1
        chevron_interval = 3 if "LISTENING" in status else (6 if ("IDLE" in status or "HALTED" in status) else 4)
        if self._chevron_timer >= chevron_interval:
            self._chevron_timer = 0
            self._chevron_step = (self._chevron_step + 1) % 5

            dim_color = "#103347"
            trail_color = "#166885"
            bright_color = "#00F0FF"

            for idx in range(3):
                # Left side: 0 is outer (leftmost), 1 is mid, 2 is inner (closest to title)
                if self._chevron_step == idx:
                    l_col = bright_color
                elif self._chevron_step == (idx + 1):
                    l_col = trail_color
                else:
                    l_col = dim_color

                # Right side: 2 is outer (rightmost), 1 is mid, 0 is inner (closest to title)
                if self._chevron_step == idx:
                    r_col = bright_color
                elif self._chevron_step == (idx + 1):
                    r_col = trail_color
                else:
                    r_col = dim_color

                if hasattr(self, "left_chevron_labels") and idx < len(self.left_chevron_labels):
                    self.left_chevron_labels[idx].configure(text_color=l_col)

                r_idx = 2 - idx  # 2 is outer, 1 is mid, 0 is inner
                if hasattr(self, "right_chevron_labels") and r_idx < len(self.right_chevron_labels):
                    self.right_chevron_labels[r_idx].configure(text_color=r_col)

            # Center title pulse as wave reaches the center
            if hasattr(self, "title_label"):
                if self._chevron_step == 3:
                    self.title_label.configure(text_color="#FFFFFF")
                elif self._chevron_step == 4:
                    self.title_label.configure(text_color="#C0F3FC")
                else:
                    self.title_label.configure(text_color="#EAFBFF")

        # 3. Neural Engine Ping Latency Jitter (Top Right)
        self._ping_counter += 1
        if self._ping_counter >= 35:
            self._ping_counter = 0
            if "IDLE" in status or "HALTED" in status or "OFFLINE" in status:
                if hasattr(self, "top_right_label"):
                    self.top_right_label.configure(text="NEURAL ENGINE: STANDBY", text_color="#FF713E")
                if hasattr(self, "top_left_label"):
                    self.top_left_label.configure(text="STANDBY", text_color="#6D91A6")
            else:
                latencies = ["21ms", "23ms", "22ms", "24ms", "20ms", "23ms", "25ms"]
                jitter = latencies[int(abs(self._glow_angle * 10)) % len(latencies)]
                if hasattr(self, "top_right_label"):
                    self.top_right_label.configure(text=f"NEURAL ENGINE: {jitter}", text_color="#00DDF5")
                if hasattr(self, "top_left_label"):
                    self.top_left_label.configure(text="SYSTEMS ONLINE", text_color="#20E6A0")

    # =========================================================
    # RIGHT PANEL: CONTROL / AUDIO / ACTIVITY / LOG
    # =========================================================

    def load_icon(self, filename, size=(22, 22), color=None):
        icon_path = config.ICONS_DIR / filename
        if not icon_path.is_file():
            return None
        try:
            im = Image.open(icon_path).convert("RGBA")
            if color:
                if isinstance(color, str) and color.startswith("#"):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                else:
                    r, g, b = color[:3]
                r_ch, g_ch, b_ch, a_ch = im.split()
                im = Image.merge("RGBA", (
                    Image.new("L", im.size, r),
                    Image.new("L", im.size, g),
                    Image.new("L", im.size, b),
                    a_ch
                ))
            return ctk.CTkImage(light_image=im, dark_image=im, size=size)
        except (OSError, ValueError):
            return None

    def create_right_panel(self):
        self.right_panel_color = "#081B2B"
        self.cyan = "#00DDF5"
        self.muted = "#63899C"
        self.green = "#20E6A0"
        self.orange = "#FF713E"

        # Load icons for control panel
        self.start_icon = self.load_icon("start.png", size=(20, 20), color=self.cyan)
        self.stop_icon = self.load_icon("stop.png", size=(20, 20), color=self.orange)
        self.mic_icon = self.load_icon("microphone.png", size=(24, 24), color=self.green)
        self.volume_icon = self.load_icon("volume.png", size=(24, 24), color=self.green)

        # Panel heading
        heading = ctk.CTkLabel(
            self.right_frame,
            text="CONTROL PANEL  · · ·",
            text_color="#D9F7FC",
            font=("Consolas", 12, "bold"),
            anchor="w",
        )
        heading.pack(fill="x", padx=12, pady=(12, 8))

        # Start / Stop buttons
        button_row = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent",
        )
        button_row.pack(fill="x", padx=10, pady=(0, 10))

        self.start_button = ctk.CTkButton(
            button_row,
            text="  START",
            image=self.start_icon,
            compound="left",
            command=self.on_start,
            height=48,
            fg_color="#062C39",
            hover_color="#084656",
            border_width=2,
            border_color=self.cyan,
            text_color=self.cyan,
            font=("Consolas", 12, "bold"),
            corner_radius=8,
        )
        self.start_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5),
        )

        self.stop_button = ctk.CTkButton(
            button_row,
            text="  STOP",
            image=self.stop_icon,
            compound="left",
            command=self.on_stop,
            height=48,
            fg_color="#321B18",
            hover_color="#51271F",
            border_width=2,
            border_color=self.orange,
            text_color=self.orange,
            font=("Consolas", 12, "bold"),
            corner_radius=8,
        )
        self.stop_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0),
        )

        # Microphone and speaker status cards
        audio_row = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent",
        )
        audio_row.pack(fill="x", padx=10, pady=(0, 10))

        self.mic_card = self.create_audio_status_card(
            audio_row,
            title="MICROPHONE",
            color=self.green,
            icon=self.mic_icon,
            symbol="🎙",
        )
        self.mic_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5),
        )

        self.speaker_card = self.create_audio_status_card(
            audio_row,
            title="VOLUME",
            color=self.green,
            icon=self.volume_icon,
            symbol="◖))",
        )
        self.speaker_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
        )

        # Input / output activity section
        activity_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="#061522",
            border_width=1,
            border_color="#164052",
            corner_radius=7,
        )
        activity_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
        )

        ctk.CTkLabel(
            activity_frame,
            text="INPUT / OUTPUT ACTIVITY",
            text_color="#D9F7FC",
            font=("Consolas", 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=8, pady=(7, 2))

        ctk.CTkLabel(
            activity_frame,
            text="INPUT",
            text_color=self.muted,
            font=("Consolas", 9),
            anchor="w",
        ).pack(fill="x", padx=8)

        self.input_wave = tk.Canvas(
            activity_frame,
            height=38,
            bg="#061522",
            highlightthickness=0,
        )
        self.input_wave.pack(fill="x", padx=8, pady=(0, 4))

        ctk.CTkLabel(
            activity_frame,
            text="OUTPUT",
            text_color=self.muted,
            font=("Consolas", 9),
            anchor="w",
        ).pack(fill="x", padx=8)

        self.output_wave = tk.Canvas(
            activity_frame,
            height=38,
            bg="#061522",
            highlightthickness=0,
        )
        self.output_wave.pack(fill="x", padx=8, pady=(0, 8))

        # Command log section
        log_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="#061522",
            border_width=1,
            border_color="#164052",
            corner_radius=7,
        )
        log_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10),
        )

        log_header = ctk.CTkFrame(
            log_frame,
            fg_color="transparent",
        )
        log_header.pack(fill="x", padx=8, pady=(7, 4))

        ctk.CTkLabel(
            log_header,
            text="COMMAND LOG",
            text_color="#D9F7FC",
            font=("Consolas", 11, "bold"),
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="CLEAR",
            width=48,
            height=22,
            fg_color="#102A3A",
            hover_color="#1B4256",
            text_color="#B9D8E2",
            font=("Consolas", 9),
            command=self.clear_command_log,
        ).pack(side="right")

        self.command_log = ctk.CTkTextbox(
            log_frame,
            height=130,
            fg_color="#061522",
            text_color="#A9C8D4",
            border_width=0,
            font=("Consolas", 9),
            wrap="word",
        )
        self.command_log.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=(0, 7),
        )
        self.command_log.configure(state="disabled")

        self.add_command_log("SYSTEM BOOT SEQUENCE COMPLETED")
        self.add_command_log("ALL MODULES ONLINE")
        self.add_command_log("SECURE CONNECTION ESTABLISHED")
        self.add_command_log("VOICE RECOGNITION NOT CONNECTED")
        self.add_command_log("AWAITING COMMAND", highlight=True)

        # Draw initial waveform graphics
        self.draw_waveform(self.input_wave, "#00DDF5", phase=0)
        self.draw_waveform(self.output_wave, "#287FEA", phase=1)

    def create_audio_status_card(self, parent, title, color, icon=None, symbol=None):
        card = ctk.CTkFrame(
            parent,
            fg_color="#061522",
            border_width=1,
            border_color="#164052",
            corner_radius=7,
            height=68,
        )
        card.pack_propagate(False)

        if icon:
            ctk.CTkLabel(
                card,
                text="",
                image=icon,
            ).pack(side="left", padx=(10, 4))
        elif symbol:
            ctk.CTkLabel(
                card,
                text=symbol,
                text_color=color,
                font=("Segoe UI Symbol", 22),
            ).pack(side="left", padx=(7, 4))

        text_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        text_frame.pack(
            side="left",
            fill="both",
            expand=True,
            pady=8,
        )

        ctk.CTkLabel(
            text_frame,
            text=title,
            text_color=self.muted,
            font=("Consolas", 8),
            anchor="w",
        ).pack(fill="x")

        status_label = ctk.CTkLabel(
            text_frame,
            text="ACTIVE",
            text_color=color,
            font=("Consolas", 10, "bold"),
            anchor="w",
        )
        status_label.pack(fill="x")

        bars = ctk.CTkLabel(
            text_frame,
            text="▮▮▮▮▮▮▮",
            text_color=color,
            font=("Consolas", 8),
            anchor="w",
        )
        bars.pack(fill="x")

        # Keep references so the status can be changed later.
        card.status_label = status_label
        card.bars_label = bars
        return card

    def draw_sound_wave(self, canvas, color, phase, active=False):
        """Draws an animated fluid acoustic sound wave on the given Canvas."""
        if not canvas or not canvas.winfo_exists():
            return

        canvas.delete("all")
        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 38)
        cy = height // 2

        points = []
        if active:
            # Active voice sound wave: organic multi-harmonic acoustic oscillation
            amp = 11.5
            for x in range(0, width + 1, 3):
                env = math.sin(math.pi * x / width)  # Hanning envelope tapering cleanly to zero at edges
                harm1 = math.sin(0.08 * x + phase)
                harm2 = 0.45 * math.sin(0.18 * x - phase * 1.4)
                harm3 = 0.25 * math.cos(0.04 * x + phase * 2.1)
                y = cy + amp * env * (harm1 + harm2 + harm3)
                points.extend([x, y])
        else:
            # Standby calm baseline: subtle gentle ambient ripple
            amp = 1.2
            for x in range(0, width + 1, 4):
                env = math.sin(math.pi * x / width)
                y = cy + amp * env * math.sin(0.05 * x + phase * 0.4)
                points.extend([x, y])

        if len(points) >= 4:
            canvas.create_line(
                *points,
                fill=color,
                width=2 if active else 1.5,
                smooth=True,
            )

    def draw_waveform(self, canvas, color, phase=0):
        """Backward-compatibility wrapper for static draws."""
        self.draw_sound_wave(canvas, color, phase, active=False)

    def _process_ui_queue(self):
        """Processes pending UI actions posted from background threads (e.g. STT, TTS, Gemini)."""
        while not self._ui_queue.empty():
            try:
                action = self._ui_queue.get_nowait()
                action()
            except Exception:
                pass
        if self._is_running:
            self._ui_queue_timer_id = self.window.after(50, self._process_ui_queue)

    def _do_add_command_log(self, message, highlight=False):
        try:
            now_dt = datetime.datetime.now()
            # Deduplicate accidental immediate duplicate logs within 1 second
            if (
                getattr(self, "_last_logged_msg", None) == message
                and getattr(self, "_last_logged_time", None) is not None
                and (now_dt - self._last_logged_time).total_seconds() < 1.0
            ):
                return
            self._last_logged_msg = message
            self._last_logged_time = now_dt

            now = now_dt.strftime("%H:%M:%S")
            line = f"{now}   {message}\n"

            self.command_log.configure(state="normal")
            self.command_log.insert("end", line)

            if highlight:
                start = self.command_log.index("end-2l")
                end = self.command_log.index("end-1l")
                self.command_log.tag_add("highlight", start, end)
                self.command_log.tag_config(
                    "highlight",
                    foreground="#FFB52E",
                )

            self.command_log.see("end")
            self.command_log.configure(state="disabled")
        except Exception:
            pass

    def add_command_log(self, message, highlight=False):
        if not self._is_running:
            return
        # Put on thread-safe queue to execute safely on the Tkinter main loop
        self._ui_queue.put(lambda: self._do_add_command_log(message, highlight))

    def clear_command_log(self):
        self.command_log.configure(state="normal")
        self.command_log.delete("1.0", "end")
        self.command_log.configure(state="disabled")
        self.add_command_log("LOG CLEARED")

    def on_start(self):
        self.update_status("LISTENING")
        self.add_command_log("LISTENER ACTIVATED", highlight=True)
        if self.on_start_callback:
            try:
                self.on_start_callback()
            except Exception:
                logger.exception("Error in on_start_callback.")

    def on_stop(self):
        self.update_status("SYSTEM IDLE")
        self.add_command_log("SYSTEM HALTED", highlight=True)
        if self.on_stop_callback:
            try:
                self.on_stop_callback()
            except Exception:
                logger.exception("Error in on_stop_callback.")

    # =========================================================
    # FOOTER
    # =========================================================

    def create_footer(self):
        panel_color = "#081B2B"

        # -----------------------------------------------------
        # TOP-DIVIDER BREATHING NEON LINE
        # -----------------------------------------------------
        self.footer_neon_line = tk.Frame(
            self.footer_frame,
            height=2,
            bg="#12364A",
            bd=0,
            highlightthickness=0,
        )
        self.footer_neon_line.place(
            relx=0,
            rely=0,
            relwidth=1,
            height=2,
        )

        # -----------------------------------------------------
        # LEFT TAG: SYSTEM TELEMETRY
        # -----------------------------------------------------
        self.footer_tag = ctk.CTkLabel(
            self.footer_frame,
            text="TELEMETRY ►",
            text_color="#20D8F2",
            font=("Consolas", 10, "bold"),
        )
        self.footer_tag.place(
            relx=0.015,
            rely=0.55,
            anchor="w",
        )

        # -----------------------------------------------------
        # RIGHT BADGE: VERSION
        # -----------------------------------------------------
        self.footer_version = ctk.CTkLabel(
            self.footer_frame,
            text="J.A.R.V.I.S  •  v1.0.1",
            text_color="#63899C",
            font=("Consolas", 10, "bold"),
        )
        self.footer_version.place(
            relx=0.985,
            rely=0.55,
            anchor="e",
        )

        # -----------------------------------------------------
        # CENTER: SCROLLING SCI-FI TELEMETRY TICKER (MARQUEE)
        # -----------------------------------------------------
        self.ticker_canvas = tk.Canvas(
            self.footer_frame,
            bg=panel_color,
            highlightthickness=0,
            bd=0,
        )
        self.ticker_canvas.place(
            relx=0.12,
            rely=0.15,
            relwidth=0.74,
            relheight=0.75,
        )

        msg = self._telemetry_msg
        self._ticker_t1 = self.ticker_canvas.create_text(
            0,
            14,
            text=msg,
            fill="#73E8F7",
            font=("Consolas", 10, "bold"),
            anchor="w",
        )
        bbox = self.ticker_canvas.bbox(self._ticker_t1)
        if bbox:
            self._ticker_tw = max(500, bbox[2] - bbox[0])
        else:
            self._ticker_tw = 680

        self._ticker_t2 = self.ticker_canvas.create_text(
            self._ticker_tw,
            14,
            text=msg,
            fill="#73E8F7",
            font=("Consolas", 10, "bold"),
            anchor="w",
        )

    # =========================================================
    # UPDATE SYSTEM INFORMATION
    # =========================================================

    def update_system_info(self):
        # CPU usage
        try:
            cpu = psutil.cpu_percent(interval=None)
            self.cpu_meter.set_value(cpu)
        except (psutil.Error, OSError):
            self.cpu_meter.set_value(None)

        # RAM usage
        try:
            ram = psutil.virtual_memory().percent
            self.ram_meter.set_value(ram)
        except (psutil.Error, OSError):
            self.ram_meter.set_value(None)

        # Battery usage
        try:
            battery = psutil.sensors_battery()
        except (psutil.Error, OSError, AttributeError):
            battery = None

        if battery is not None and getattr(battery, "percent", None) is not None:
            self.battery_meter.set_value(battery.percent)

            if getattr(battery, "power_plugged", None) is True:
                self.battery_note.configure(text="POWER CONNECTED")
            elif getattr(battery, "power_plugged", None) is False:
                self.battery_note.configure(text="ON BATTERY")
            else:
                self.battery_note.configure(text="BATTERY DETECTED")
        else:
            self.battery_meter.set_value(None)
            self.battery_note.configure(text="BATTERY NOT AVAILABLE")

        # Live telemetry string for footer ticker
        try:
            vm = psutil.virtual_memory()
            ram_avail = vm.available / (1024**3)
        except Exception:
            ram_avail = 8.0

        try:
            uptime_sec = int(datetime.datetime.now().timestamp() - psutil.boot_time())
            hrs = uptime_sec // 3600
            mins = (uptime_sec % 3600) // 60
            uptime_str = f"{hrs}h {mins:02d}m"
        except Exception:
            uptime_str = "2h 55m"

        cpu_val = cpu if cpu is not None else 15.0

        self._wifi_check_counter += 1
        if self._wifi_check_counter >= 10:
            self._wifi_check_counter = 0
            try:
                from system.network_controller import NetworkController
                ok, _, data = NetworkController.check_wifi()
                if ok and data.get("ssid"):
                    sig = data.get("signal", "100%")
                    self._cached_wifi_str = f"{data['ssid']} ({sig})"
            except Exception:
                pass

        wifi_str = getattr(self, "_cached_wifi_str", "GALAXY 5G (88%)")
        self._telemetry_msg = (
            f"[CORE: {cpu_val:.0f}% LOAD]   •   "
            f"[RAM: {ram_avail:.1f}GB FREE]   •   "
            f"[WI-FI: {wifi_str}]   •   "
            f"[UPTIME: {uptime_str}]   •   "
            f"[SECURITY: NOMINAL]       "
        )

    # =========================================================
    # UPDATE DATE & TIME
    # =========================================================

    def update_date_time(self):
        now = datetime.datetime.now()

        self.time_label.configure(
            text=now.strftime("%H:%M")
        )

        self.seconds_label.configure(
            text=now.strftime(":%S")
        )

        self.date_label.configure(
            text=now.strftime("%A, %d. %B %Y").upper()
        )

    # =========================================================
    # DASHBOARD UPDATE
    # =========================================================

    def update_dashboard(self):
        if not self._is_running:
            return

        self.update_system_info()
        self.update_date_time()

        if self._is_running:
            self._dashboard_timer_id = self.window.after(1000, self.update_dashboard)

    # =========================================================
    # UPDATE STATUS TEXT
    # =========================================================

    def update_status(self, text):
        if not self._is_running:
            return
        self._current_status = str(text).upper()
        # Put on thread-safe queue to execute safely on the Tkinter main loop
        self._ui_queue.put(lambda: self.status_label.configure(text=text))

    # =========================================================
    # RUN
    # =========================================================

    def run(self):
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.on_close()