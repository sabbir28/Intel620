import ctypes
import os
import platform
import threading
import time
import tkinter as tk
from tkinter import ttk

from intel620.gui.theme import *
from intel620.services.brightness_service import BrightnessService
from intel620.services.display_service import DisplayService, is_success
from intel620.services.system_info_service import SystemInfoService

display_service = DisplayService()
brightness_service = BrightnessService()
system_info_service = SystemInfoService()

DISP_CHANGE_SUCCESSFUL = 0


def get_all_adapters():
    return display_service.get_all_adapters()


def get_monitors_for(device_name):
    return display_service.get_monitors_for(device_name)


def get_current_mode(device_name):
    return display_service.get_current_mode(device_name)


def get_supported_modes(device_name):
    return display_service.get_supported_modes(device_name)


def enable_display(device_name, pos_x, pos_y, width, height, freq=60):
    return display_service.enable_display(device_name, pos_x, pos_y, width, height, freq)


def disable_display(device_name):
    return display_service.disable_display(device_name)


def commit_changes():
    return display_service.commit_changes()


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _test_wmi():
    return brightness_service.test_wmi()


def set_brightness(device_name, level, is_primary=False):
    return brightness_service.set_brightness(device_name, level, is_primary)


def get_current_brightness():
    return brightness_service.get_current_brightness()


def collect_system_info():
    return system_info_service.collect()

class IntelDisplayPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Intel® Graphics Control Panel  v2.0")
        self.geometry("1100x730")
        self.minsize(920, 640)
        self.configure(bg=BG)
        self.resizable(True, True)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._brightness_vars = {}
        self._current_tab     = "displays"
        self._tabs            = {}
        self._sys_info        = {}

        self._build_ui()
        self.after(150, self.refresh_displays)
        self.after(300, lambda: threading.Thread(
            target=self._load_sysinfo, daemon=True).start())

    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_nav()
        self._tab_container = tk.Frame(self, bg=BG)
        self._tab_container.pack(fill=tk.BOTH, expand=True)
        self._build_displays_tab()
        self._build_brightness_tab()
        self._build_quect_tools_tab()
        self._build_about_tab()
        self._build_statusbar()
        self._show_tab("displays")

    # ── HEADER ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, height=54)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        badge = tk.Frame(hdr, bg="white", width=38, height=38)
        badge.place(x=14, y=8)
        badge.pack_propagate(False)
        tk.Label(badge, text="i", font=("Segoe UI",20,"bold"),
                 bg="white", fg=ACCENT).pack(expand=True)

        tk.Label(hdr, text="Intel® HD Graphics 620",
                 font=("Segoe UI",14,"bold"), bg=ACCENT, fg="white").place(x=65, y=7)
        tk.Label(hdr, text="Display Manager  ·  Brightness Control  ·  System Information",
                 font=FONT_SMALL, bg=ACCENT, fg="#a8d4f0").place(x=67, y=31)

        ac = SUCCESS if is_admin() else WARNING
        at = "● Administrator" if is_admin() else "▲ Limited (Run as Admin)"
        tk.Label(hdr, text=at, font=("Segoe UI",8,"bold"),
                 bg=ACCENT, fg=ac).place(relx=1.0, x=-16, y=10, anchor="ne")

        rb = tk.Label(hdr, text="⟳  Refresh", font=("Segoe UI",9,"bold"),
                      bg="#005a9e", fg="white", padx=10, pady=4, cursor="hand2")
        rb.place(relx=1.0, x=-150, y=14, anchor="ne")
        rb.bind("<Button-1>", lambda e: self.refresh_displays())
        rb.bind("<Enter>",    lambda e: rb.config(bg=ACCENT2))
        rb.bind("<Leave>",    lambda e: rb.config(bg="#005a9e"))

    # ── NAV ──────────────────────────────────────────────────────────────────
    def _build_nav(self):
        nav = tk.Frame(self, bg=BG2, height=38)
        nav.pack(fill=tk.X)
        nav.pack_propagate(False)
        self._nav_btns = {}
        for key, label in [("displays","⊞  Displays"),
                            ("brightness","☀  Brightness"),
                            ("quect_tools","🧰  Quect Tools"),
                            ("about","ℹ  About & System Info")]:
            btn = tk.Label(nav, text=label, font=("Segoe UI",9,"bold"),
                           bg=BG2, fg=TEXT2, padx=18, pady=9, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, k=key: self._show_tab(k))
            self._nav_btns[key] = btn

    def _show_tab(self, key):
        self._current_tab = key
        for k, btn in self._nav_btns.items():
            btn.config(fg="white" if k==key else TEXT2,
                       bg=ACCENT  if k==key else BG2)
        for k, frame in self._tabs.items():
            if k == key:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — DISPLAYS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_displays_tab(self):
        frame = tk.Frame(self._tab_container, bg=BG)
        self._tabs["displays"] = frame
        content = tk.Frame(frame, bg=BG)
        content.pack(fill=tk.BOTH, expand=True)
        self._build_sidebar(content)
        self._build_display_main(content)

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG2, width=206)
        side.pack(side=tk.LEFT, fill=tk.Y)
        side.pack_propagate(False)

        tk.Label(side, text="QUICK ACTIONS", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(18,6))
        for lbl, cmd, clr in [
            ("▶  Auto Enable All",  self._do_auto_enable,          ACCENT),
            ("⊞  Extend Desktop",   self._do_extend,               "#1a4a7a"),
            ("⊟  Mirror / Clone",   self._do_mirror,               "#1a4a7a"),
            ("✕  Disable Inactive", self._do_disable_all_inactive, "#3a1a2a"),
        ]:
            self._sidebar_btn(side, lbl, clr, cmd)

        tk.Label(side, text="DISPLAY MODE", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(20,6))
        self._mode_var = tk.StringVar(value="extend")
        for val, lbl in [("extend","Extended"),("mirror","Mirror/Clone"),("single","Single Only")]:
            tk.Radiobutton(side, text=lbl, variable=self._mode_var, value=val,
                           font=FONT_BODY, bg=BG2, fg=TEXT2, selectcolor=BG3,
                           activebackground=BG2, activeforeground=TEXT
                           ).pack(anchor="w", padx=20, pady=2)

        tk.Label(side, text="DRIVER DLLs", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(20,6))
        self._dll_frame = tk.Frame(side, bg=BG2)
        self._dll_frame.pack(fill=tk.X, padx=12)
        self._populate_dll_status()

        tk.Frame(side, bg=BG2).pack(fill=tk.BOTH, expand=True)
        tk.Label(side, text="Intel® HD/UHD Graphics 620\nPCI\\VEN_8086&DEV_5916",
                 font=FONT_MONO, bg=BG2, fg=TEXT3, justify=tk.LEFT
                 ).pack(anchor="w", padx=16, pady=10)

    def _populate_dll_status(self):
        for w in self._dll_frame.winfo_children():
            w.destroy()
        dlls = ["igc64.dll","igd9dxva64.dll","igdgmm64.dll","igdumdim64.dll"]
        ds   = r"C:\Windows\System32\DriverStore\FileRepository"
        found = {}
        if os.path.isdir(ds):
            for folder in os.listdir(ds):
                if "igd" in folder.lower() or "igfx" in folder.lower():
                    for dll in dlls:
                        fp = os.path.join(ds, folder, dll)
                        if os.path.isfile(fp) and dll not in found:
                            found[dll] = fp
        for dll in dlls:
            ok = dll in found
            tk.Label(self._dll_frame,
                     text=f"{'●' if ok else '○'} {dll.replace('.dll','')}",
                     font=FONT_MONO, bg=BG2, fg=SUCCESS if ok else DANGER
                     ).pack(anchor="w", pady=1)

    def _build_display_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tb = tk.Frame(main, bg=BG)
        tb.pack(fill=tk.X, padx=20, pady=(14,6))
        tk.Label(tb, text="Connected Displays", font=FONT_BIG, bg=BG, fg=TEXT).pack(side=tk.LEFT)
        self._count_lbl = tk.Label(tb, text="", font=FONT_BODY, bg=BG, fg=TEXT2)
        self._count_lbl.pack(side=tk.LEFT, padx=10)

        cv = tk.Canvas(main, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(main, orient=tk.VERTICAL, command=cv.yview)
        self._cards_frame = tk.Frame(cv, bg=BG)
        self._cards_frame.bind("<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=self._cards_frame, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20,0), pady=4)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        rp = tk.Frame(main, bg=BG2, width=228)
        rp.pack(side=tk.RIGHT, fill=tk.Y)
        rp.pack_propagate(False)

        tk.Label(rp, text="DESKTOP LAYOUT", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=12, pady=(14,4))
        self._preview_canvas = tk.Canvas(rp, bg=BG3, width=204, height=132,
                                          highlightthickness=1,
                                          highlightbackground=CARD_BORDER)
        self._preview_canvas.pack(padx=12, pady=2)

        tk.Label(rp, text="ACTIVITY LOG", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=12, pady=(12,4))
        lf = tk.Frame(rp, bg=BG3)
        lf.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,12))
        self._log_text = tk.Text(lf, bg=BG3, fg=TEXT2, font=FONT_MONO, width=26,
                                  state=tk.DISABLED, wrap=tk.WORD, relief=tk.FLAT,
                                  bd=0, highlightthickness=0)
        self._log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — BRIGHTNESS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_brightness_tab(self):
        frame = tk.Frame(self._tab_container, bg=BG)
        self._tabs["brightness"] = frame

        tk.Label(frame, text="Brightness Control", font=FONT_BIG, bg=BG, fg=TEXT
                 ).pack(anchor="w", padx=24, pady=(18,4))

        wmi_ok = _test_wmi()
        wmi_c  = SUCCESS if wmi_ok else WARNING
        wmi_t  = ("● WMI Hardware Brightness: Available (laptop panel)"
                  if wmi_ok else
                  "○ WMI: Not available  →  Using Gamma Ramp (visual, works on all displays)")
        tk.Label(frame, text=wmi_t, font=FONT_BODY, bg=BG, fg=wmi_c
                 ).pack(anchor="w", padx=24, pady=(0,10))

        # Main area split
        split = tk.Frame(frame, bg=BG)
        split.pack(fill=tk.BOTH, expand=True)

        # Left: per-display sliders
        left = tk.Frame(split, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cv = tk.Canvas(left, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(left, orient=tk.VERTICAL, command=cv.yview)
        self._bright_frame = tk.Frame(cv, bg=BG)
        self._bright_frame.bind("<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=self._bright_frame, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(24,0), pady=4)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        # Right: global controls
        right = tk.Frame(split, bg=BG2, width=284)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        tk.Label(right, text="ALL DISPLAYS", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(20,6))
        tk.Label(right, text="Apply same brightness\nto every active display:",
                 font=FONT_SMALL, bg=BG2, fg=TEXT2).pack(anchor="w", padx=16)

        self._global_bright_var = tk.IntVar(value=80)
        self._build_slider(right, self._global_bright_var, "Global", compact=True)
        self._make_btn(right, "Apply to All Displays",
                       ACCENT, "white", self._apply_global_brightness
                       ).pack(padx=16, pady=6, fill=tk.X)

        tk.Label(right, text="PRESETS", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(18,6))
        for lbl, val, bg in [
            ("☀  Day  (100%)",     100, "#4a3800"),
            ("⊙  Work  (70%)",      70, "#1a3a4a"),
            ("◑  Evening  (40%)",   40, "#2a1a3a"),
            ("☽  Night  (10%)",     10, "#1a1a2a"),
        ]:
            self._make_btn(right, lbl, bg, BRIGHT_CLR,
                           lambda v=val: self._preset_brightness(v)
                           ).pack(padx=16, pady=3, fill=tk.X)

        tk.Frame(right, bg=BG2).pack(fill=tk.BOTH, expand=True)
        tk.Label(right,
                 text="Note: Gamma ramp resets on\ndriver reload or reboot.\nHardware brightness persists.",
                 font=FONT_SMALL, bg=BG2, fg=TEXT3, justify=tk.LEFT
                 ).pack(anchor="w", padx=16, pady=12)

    def _build_slider(self, parent, var, label="", compact=False):
        outer = tk.Frame(parent, bg=BG3, padx=12, pady=10)
        outer.pack(fill=tk.X, padx=16 if not compact else 12,
                   pady=6 if not compact else 4)

        top = tk.Frame(outer, bg=BG3)
        top.pack(fill=tk.X)

        sc = tk.Canvas(top, width=22, height=22, bg=BG3, highlightthickness=0)
        sc.pack(side=tk.LEFT, padx=(0,6))
        self._draw_sun(sc)

        if label:
            tk.Label(top, text=label, font=("Segoe UI",9,"bold"),
                     bg=BG3, fg=TEXT).pack(side=tk.LEFT)

        val_lbl = tk.Label(top, text=f"{var.get()}%",
                           font=("Segoe UI",11,"bold"), bg=BG3, fg=BRIGHT_CLR)
        val_lbl.pack(side=tk.RIGHT)

        def on_change(v):
            iv = int(float(v))
            val_lbl.config(text=f"{iv}%")
            clr = BRIGHT_CLR if iv >= 70 else (ACCENT2 if iv >= 40 else TEXT3)
            sl.config(fg=clr)

        sl = tk.Scale(outer, variable=var, from_=0, to=100,
                      orient=tk.HORIZONTAL, showvalue=False,
                      bg=BG3, fg=BRIGHT_CLR, troughcolor=BG2,
                      highlightthickness=0, relief=tk.FLAT,
                      activebackground=BRIGHT_CLR, sliderrelief=tk.FLAT,
                      command=on_change,
                      length=190 if not compact else 210)
        sl.pack(fill=tk.X, pady=(4,0))
        return sl

    def _draw_sun(self, canvas):
        import math
        canvas.create_oval(6,6,16,16, fill=BRIGHT_CLR, outline="")
        for a in range(0,360,45):
            r = math.radians(a)
            canvas.create_line(11+7*math.cos(r), 11+7*math.sin(r),
                               11+10*math.cos(r), 11+10*math.sin(r),
                               fill=BRIGHT_CLR, width=2)

    def _build_brightness_cards(self, adapters):
        for w in self._bright_frame.winfo_children():
            w.destroy()
        active = [a for a in adapters if a["is_active"]]
        if not active:
            tk.Label(self._bright_frame, text="No active displays.",
                     font=FONT_BODY, bg=BG, fg=TEXT3).pack(pady=30)
            return

        for adapter in active:
            name = adapter["name"]
            ip   = adapter["is_primary"]

            outer = tk.Frame(self._bright_frame,
                             bg=ACCENT if ip else CARD_BORDER, padx=1, pady=1)
            outer.pack(fill=tk.X, pady=5)
            card = tk.Frame(outer, bg=BG3, padx=18, pady=14)
            card.pack(fill=tk.X)

            top = tk.Frame(card, bg=BG3)
            top.pack(fill=tk.X)
            ic = tk.Canvas(top, width=32, height=28, bg=BG3, highlightthickness=0)
            ic.pack(side=tk.LEFT, padx=(0,10))
            self._draw_monitor_icon(ic, True)

            inf = tk.Frame(top, bg=BG3)
            inf.pack(side=tk.LEFT, fill=tk.X, expand=True)
            nr = tk.Frame(inf, bg=BG3)
            nr.pack(fill=tk.X)
            tk.Label(nr, text=f"DISPLAY{adapter['index']+1}  —  {adapter['string']}",
                     font=FONT_HEAD, bg=BG3, fg=TEXT).pack(side=tk.LEFT)
            if ip:
                self._badge(nr, "PRIMARY", ACCENT)

            cur = get_current_mode(name)
            if cur:
                tk.Label(inf,
                         text=f"{cur.dmPelsWidth}×{cur.dmPelsHeight} @ {cur.dmDisplayFrequency}Hz",
                         font=FONT_MONO, bg=BG3, fg=TEXT2).pack(anchor="w")

            init_val = get_current_brightness() if ip else 80
            if name not in self._brightness_vars:
                self._brightness_vars[name] = tk.IntVar(value=init_val)
            bvar = self._brightness_vars[name]

            self._build_slider(card, bvar, "Brightness")

            def make_apply(n=name, v=bvar, p=ip):
                def _a():
                    lvl = v.get()
                    self._log(f"Setting brightness {lvl}% → {n}")
                    def _r():
                        method, ok = set_brightness(n, lvl, p)
                        self.after(0, lambda: self._log(
                            f"{'✓' if ok else '✗'} {method} → {lvl}% on {n}"))
                    threading.Thread(target=_r, daemon=True).start()
                return _a

            btn_row = tk.Frame(card, bg=BG3)
            btn_row.pack(fill=tk.X, pady=(8,0))
            self._make_btn(btn_row, "Apply Brightness",
                           "#2a3800", BRIGHT_CLR, make_apply()
                           ).pack(side=tk.LEFT)

            # Quick presets inline
            for pct, lbl in [(25,"25%"),(50,"50%"),(75,"75%"),(100,"100%")]:
                def make_preset(n=name, p=ip, v=pct, bv=bvar):
                    def _p():
                        bv.set(v)
                        method, ok = set_brightness(n, v, p)
                        self._log(f"{'✓' if ok else '✗'} {method} → {v}% on {n}")
                    return _p
                pb = tk.Label(btn_row, text=lbl, font=FONT_SMALL,
                              bg="#1a2a00", fg=BRIGHT_CLR, padx=8, pady=4, cursor="hand2")
                pb.pack(side=tk.LEFT, padx=(6,0))
                pb.bind("<Button-1>", lambda e, f=make_preset(): f())
                pb.bind("<Enter>",    lambda e, b=pb: b.config(bg=BRIGHT_CLR, fg=BG))
                pb.bind("<Leave>",    lambda e, b=pb: b.config(bg="#1a2a00", fg=BRIGHT_CLR))

    def _apply_global_brightness(self):
        level = self._global_bright_var.get()
        self._log(f"Applying global brightness {level}%...")
        def _r():
            for a in get_all_adapters():
                if a["is_active"]:
                    method, ok = set_brightness(a["name"], level, a["is_primary"])
                    self.after(0, lambda n=a["name"], m=method, s=ok:
                               self._log(f"{'✓' if s else '✗'} {m} → {level}% on {n}"))
        threading.Thread(target=_r, daemon=True).start()

    def _preset_brightness(self, val):
        self._global_bright_var.set(val)
        self._apply_global_brightness()


    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — QUECT TOOLS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_quect_tools_tab(self):
        frame = tk.Frame(self._tab_container, bg=BG)
        self._tabs["quect_tools"] = frame

        tk.Label(frame, text="Quect Tools", font=FONT_BIG, bg=BG, fg=TEXT
                 ).pack(anchor="w", padx=24, pady=(18, 6))
        tk.Label(frame,
                 text="Starter area for your next tools. Click buttons now, wire logic later.",
                 font=FONT_BODY, bg=BG, fg=TEXT2).pack(anchor="w", padx=24, pady=(0, 14))

        content = tk.Frame(frame, bg=BG)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))

        left = tk.Frame(content, bg=BG3, padx=16, pady=16)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(left, text="Quick Buttons", font=FONT_SEC, bg=BG3, fg=TEXT3
                 ).pack(anchor="w", pady=(0, 8))

        button_specs = [
            ("🔄  Rifresh", ACCENT),
            ("➕  Add Tool", "#1a4a7a"),
            ("🧪  Run Test Tool", "#2a3a1a"),
            ("📦  Export Config", "#4a3800"),
        ]
        for label, color in button_specs:
            self._make_btn(
                left,
                label,
                color,
                "white",
                lambda n=label: self._set_status(f"{n} clicked — TODO: implement action."),
            ).pack(fill=tk.X, pady=4)

        right = tk.Frame(content, bg=BG2, width=330)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        tk.Label(right, text="TODO", font=FONT_SEC, bg=BG2, fg=TEXT3
                 ).pack(anchor="w", padx=16, pady=(16, 8))
        todo_text = tk.Text(
            right,
            bg=BG3,
            fg=TEXT,
            font=FONT_BODY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            wrap=tk.WORD,
            height=16,
        )
        todo_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))
        todo_text.insert(
            "1.0",
            "TODO:\n"
            "- Implement tool action handlers\n"
            "- Connect buttons to services\n"
            "- Add validation and logs\n"
            "- Save and load user presets\n"
            "\n"
            "(You can edit this list directly.)",
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — ABOUT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_about_tab(self):
        frame = tk.Frame(self._tab_container, bg=BG)
        self._tabs["about"] = frame

        cv = tk.Canvas(frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(frame, orient=tk.VERTICAL, command=cv.yview)
        self._about_inner = tk.Frame(cv, bg=BG)
        self._about_inner.bind("<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=self._about_inner, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self._about_inner, text="⟳  Collecting system information...",
                 font=FONT_BIG, bg=BG, fg=TEXT2).pack(pady=60)

    def _load_sysinfo(self):
        self._sys_info = collect_system_info()
        self.after(0, self._populate_about)

    def _populate_about(self):
        for w in self._about_inner.winfo_children():
            w.destroy()
        info = self._sys_info

        # ── Banner ──
        banner = tk.Frame(self._about_inner, bg=ACCENT, padx=28, pady=22)
        banner.pack(fill=tk.X)
        tk.Label(banner, text="Intel® HD Graphics 620",
                 font=("Segoe UI",22,"bold"), bg=ACCENT, fg="white").pack(anchor="w")
        tk.Label(banner, text="Display Control Panel  ·  v2.0  ·  System Information Report",
                 font=FONT_BODY, bg=ACCENT, fg="#a8d4f0").pack(anchor="w")
        tk.Label(banner,
                 text=f"Generated: {time.strftime('%Y-%m-%d  %H:%M:%S')}   |   "
                      f"Python {platform.python_version()}   |   "
                      f"{'Administrator' if is_admin() else 'Standard User'}",
                 font=FONT_MONO, bg=ACCENT, fg="#7ac8f0").pack(anchor="w", pady=(8,0))

        content = tk.Frame(self._about_inner, bg=BG)
        content.pack(fill=tk.X, padx=0)

        # Two-column layout for compact sections
        cols = tk.Frame(content, bg=BG)
        cols.pack(fill=tk.X, padx=28, pady=(20,0))
        col_l = tk.Frame(cols, bg=BG)
        col_l.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
        col_r = tk.Frame(cols, bg=BG)
        col_r.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0))

        self._info_card(col_l, "🖥  GPU / Graphics Card", [
            ("GPU Name",       info.get("gpu_name","Intel(R) HD Graphics 620")),
            ("PCI Vendor",     "VEN_8086  (Intel Corporation)"),
            ("PCI Device",     "DEV_5916  (Kaby Lake HD 620)"),
            ("Subsystem",      "SUBSYS_81ED103C  (HP Inc.)"),
            ("Revision",       "REV_02"),
            ("Driver Ver.",    info.get("gpu_driverversion","27.20.100.9664")),
            ("Video Proc.",    info.get("gpu_videoprocessor","Intel HD Graphics Family")),
            ("Adapter RAM",    self._fmt_bytes(info.get("gpu_adapterram","0"))),
            ("Video Mode",     info.get("gpu_videomodedescrition",
                                        "1366 x 768 x 32-bit")),
            ("API Support",    "DX12 · OpenGL 4.6 · Vulkan 1.2 · OpenCL 3.0"),
        ])

        self._info_card(col_r, "💻  System", [
            ("Hostname",       info.get("node", platform.node())),
            ("OS",             f"Windows {info.get('os_rel','10')}"),
            ("Build",          info.get("os_ver","")[:40]),
            ("Architecture",   info.get("machine", platform.machine())),
            ("Python",         info.get("python", platform.python_version())),
            ("Admin Rights",   "Yes ✓" if is_admin() else "No (run as admin)"),
        ])
        self._info_card(col_r, "⚙  CPU", [
            ("Processor",      info.get("cpu_name","Unknown")),
            ("Cores",          info.get("cpu_numberofcores","—")),
            ("Logical CPUs",   info.get("cpu_numberoflogicalprocessors","—")),
            ("Max Clock",      f"{info.get('cpu_maxclockspeed','—')} MHz"),
        ])
        self._info_card(col_r, "🧠  Memory", [
            ("Total RAM",      self._fmt_kb(info.get("ram_totalvisiblememorysiz","0"))),
            ("Free RAM",       self._fmt_kb(info.get("ram_freephysicalmemory","0"))),
        ])

        # DLL section
        self._dll_card(content, info.get("dll_paths",{}))

        # Display adapters section
        self._display_card(content)

        # Technology section
        self._tech_card(content)

        # Footer
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X, padx=28, pady=(20,8))
        tk.Label(content,
                 text="Intel HD/UHD Graphics 620  ·  Gen 9.5  ·  24 EU  ·  Kaby Lake  ·  "
                      "This panel uses Win32 ChangeDisplaySettingsEx + GDI Gamma Ramp APIs",
                 font=FONT_SMALL, bg=BG, fg=TEXT3).pack(anchor="w", padx=28, pady=(0,20))

    def _info_card(self, parent, title, fields):
        tk.Label(parent, text=title, font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", pady=(12,4))
        card = tk.Frame(parent, bg=BG3, padx=14, pady=10)
        card.pack(fill=tk.X, pady=(0,2))
        for key, val in fields:
            row = tk.Frame(card, bg=BG3)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{key}:", font=("Segoe UI",8),
                     bg=BG3, fg=TEXT3, width=16, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=str(val), font=("Segoe UI",8,"bold"),
                     bg=BG3, fg=TEXT, anchor="w", wraplength=340
                     ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _dll_card(self, parent, dll_paths):
        tk.Label(parent, text="📦  Driver DLL Files", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", padx=28, pady=(16,4))
        card = tk.Frame(parent, bg=BG3, padx=16, pady=12)
        card.pack(fill=tk.X, padx=28, pady=(0,4))

        dll_info = {
            "igc64.dll":      "Intel Graphics Compiler — shader compile for DX12/Vulkan/OpenGL",
            "igd9dxva64.dll": "Intel DXVA — DirectX Video Acceleration (HW video decode)",
            "igdgmm64.dll":   "Intel GMM — Graphics Memory Manager (VRAM allocation)",
            "igdumdim64.dll": "Intel UMD — User Mode Driver for DX11/DX12",
        }
        for dll, desc in dll_info.items():
            found = dll in dll_paths
            row   = tk.Frame(card, bg=BG4 if not found else BG3, padx=8, pady=4)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="●" if found else "○",
                     font=("Segoe UI",12), bg=row.cget("bg"),
                     fg=SUCCESS if found else DANGER).pack(side=tk.LEFT, padx=(0,8))
            col = tk.Frame(row, bg=row.cget("bg"))
            col.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(col, text=dll, font=("Consolas",9,"bold"),
                     bg=row.cget("bg"), fg=TEXT).pack(anchor="w")
            tk.Label(col, text=desc, font=FONT_SMALL,
                     bg=row.cget("bg"), fg=TEXT2).pack(anchor="w")
            if found:
                tk.Label(col, text=dll_paths[dll], font=FONT_MONO,
                         bg=row.cget("bg"), fg=TEXT3, wraplength=560,
                         justify=tk.LEFT).pack(anchor="w")
            tk.Label(row, text="LOADED" if found else "NOT FOUND",
                     font=("Segoe UI",8,"bold"),
                     bg=SUCCESS if found else DANGER, fg="white",
                     padx=6, pady=2).pack(side=tk.RIGHT, anchor="n")

    def _display_card(self, parent):
        adapters = get_all_adapters()
        tk.Label(parent, text="🖵  Detected Display Adapters",
                 font=("Segoe UI",10,"bold"), bg=BG, fg=TEXT
                 ).pack(anchor="w", padx=28, pady=(16,4))
        card = tk.Frame(parent, bg=BG3, padx=16, pady=12)
        card.pack(fill=tk.X, padx=28, pady=(0,4))

        for a in adapters:
            sc = SUCCESS if a["is_active"] else TEXT3
            row = tk.Frame(card, bg=BG3)
            row.pack(fill=tk.X, pady=4)

            tk.Label(row, text=f"● D{a['index']+1}",
                     font=("Segoe UI",9,"bold"), bg=BG3, fg=sc
                     ).pack(side=tk.LEFT, padx=(0,10))

            inf = tk.Frame(row, bg=BG3)
            inf.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(inf, text=a["string"], font=("Segoe UI",9,"bold"),
                     bg=BG3, fg=TEXT).pack(anchor="w")
            tk.Label(inf, text=f"{a['name']}  |  {a['device_id'][:70]}",
                     font=FONT_MONO, bg=BG3, fg=TEXT3).pack(anchor="w")

            if a["is_active"]:
                cur = get_current_mode(a["name"])
                if cur:
                    tk.Label(inf,
                             text=f"{cur.dmPelsWidth}×{cur.dmPelsHeight} @ "
                                  f"{cur.dmDisplayFrequency}Hz  {cur.dmBitsPerPel}bpp  "
                                  f"pos({cur.dmPositionX},{cur.dmPositionY})",
                             font=FONT_MONO, bg=BG3, fg=ACCENT2).pack(anchor="w")

            for m in get_monitors_for(a["name"]):
                tk.Label(inf, text=f"  ↳ {m['string']}  {m['device_id'][:50]}",
                         font=FONT_MONO, bg=BG3, fg=TEXT2).pack(anchor="w")

            badges = tk.Frame(row, bg=BG3)
            badges.pack(side=tk.RIGHT, anchor="n")
            self._badge(badges, "ACTIVE" if a["is_active"] else "INACTIVE",
                        SUCCESS if a["is_active"] else DANGER)
            if a["is_primary"]:
                self._badge(badges, "PRIMARY", ACCENT)

            tk.Frame(card, bg=BORDER, height=1).pack(fill=tk.X, pady=4)

    def _tech_card(self, parent):
        tk.Label(parent, text="🔧  Technology & API Support",
                 font=("Segoe UI",10,"bold"), bg=BG, fg=TEXT
                 ).pack(anchor="w", padx=28, pady=(16,4))
        card = tk.Frame(parent, bg=BG3, padx=16, pady=12)
        card.pack(fill=tk.X, padx=28, pady=(0,4))

        for name, desc in [
            ("DirectX 12",        "Feature level 12_1 — hardware tier 2 rasterizer ordered views"),
            ("OpenGL 4.6",        "Full 4.6 + compatibility profile via Intel ICD"),
            ("Vulkan 1.2",        "Intel ANV driver — sparse binding, descriptor indexing"),
            ("OpenCL 3.0",        "GPU compute via Intel NEO OpenCL runtime"),
            ("DXVA2 / MFT",       "HW decode: H.264, HEVC 4K, VP8, VP9"),
            ("HDMI 1.4 / DP 1.2", "Up to 3 simultaneous outputs (eDP + 2 external)"),
            ("Quick Sync",        "7th Gen Kaby Lake — HW encode/decode HEVC 4K @ 60fps"),
            ("Intel Clear Video", "Adaptive contrast enhancement + color correction engine"),
            ("Gen 9.5 GPU",       "24 Execution Units  ·  Base 300MHz  ·  Boost 1100MHz"),
            ("Win32 APIs Used",   "ChangeDisplaySettingsEx · EnumDisplayDevices · SetDeviceGammaRamp"),
        ]:
            row = tk.Frame(card, bg=BG3)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text="▸", font=("Segoe UI",10), bg=BG3, fg=ACCENT2
                     ).pack(side=tk.LEFT, padx=(0,8))
            tk.Label(row, text=name, font=("Segoe UI",9,"bold"),
                     bg=BG3, fg=TEXT, width=24, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=desc, font=FONT_SMALL, bg=BG3, fg=TEXT2,
                     anchor="w", justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)

    @staticmethod
    def _fmt_bytes(val):
        try:
            b = int(val)
            if b == 0:
                return "Shared (Dynamic VRAM)"
            for u in ["B","KB","MB","GB"]:
                if b < 1024:
                    return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} TB"
        except Exception:
            return str(val)

    @staticmethod
    def _fmt_kb(val):
        try:
            kb = int(val)
            return f"{kb/1024/1024:.2f} GB  ({kb:,} KB)"
        except Exception:
            return str(val)

    # ══════════════════════════════════════════════════════════════════════════
    #  DISPLAY CARDS (Tab 1)
    # ══════════════════════════════════════════════════════════════════════════
    def refresh_displays(self):
        self._log("Scanning display adapters...")
        for w in self._cards_frame.winfo_children():
            w.destroy()
        adapters = get_all_adapters()
        self._count_lbl.config(
            text=f"({len(adapters)} adapter{'s' if len(adapters)!=1 else ''} found)")
        for a in adapters:
            self._build_display_card(a)
        self._draw_preview(adapters)
        self._build_brightness_cards(adapters)
        active = sum(1 for a in adapters if a["is_active"])
        self._log(f"Found {len(adapters)} adapters, {active} active")
        self._status_var.set(
            f"✓  {active} active  |  {len(adapters)-active} inactive  |  {time.strftime('%H:%M:%S')}")

    def _build_display_card(self, adapter):
        is_active  = adapter["is_active"]
        is_primary = adapter["is_primary"]
        border_c   = ACCENT if is_primary else (SUCCESS if is_active else BORDER)

        outer = tk.Frame(self._cards_frame, bg=border_c, padx=1, pady=1)
        outer.pack(fill=tk.X, pady=5)
        card = tk.Frame(outer, bg=BG3, padx=16, pady=12)
        card.pack(fill=tk.X)

        top = tk.Frame(card, bg=BG3)
        top.pack(fill=tk.X)
        ic = tk.Canvas(top, width=42, height=34, bg=BG3, highlightthickness=0)
        ic.pack(side=tk.LEFT, padx=(0,12))
        self._draw_monitor_icon(ic, is_active)

        inf = tk.Frame(top, bg=BG3)
        inf.pack(side=tk.LEFT, fill=tk.X, expand=True)
        nr = tk.Frame(inf, bg=BG3)
        nr.pack(fill=tk.X)
        tk.Label(nr, text=f"DISPLAY{adapter['index']+1}  —  {adapter['string']}",
                 font=FONT_HEAD, bg=BG3, fg=TEXT).pack(side=tk.LEFT)
        if is_primary:
            self._badge(nr, "PRIMARY", ACCENT)
        self._badge(nr, "ACTIVE" if is_active else "INACTIVE",
                    SUCCESS if is_active else DANGER)
        tk.Label(inf, text=adapter["name"], font=FONT_MONO, bg=BG3, fg=TEXT3).pack(anchor="w")

        cur = get_current_mode(adapter["name"]) if is_active else None
        if cur:
            ol = ["Landscape","Portrait","Landscape (Flipped)","Portrait (Flipped)"]
            ot = ol[cur.dmDisplayOrientation] if cur.dmDisplayOrientation < 4 else "?"
            tk.Label(card,
                     text=(f"{cur.dmPelsWidth}×{cur.dmPelsHeight}  "
                           f"@{cur.dmDisplayFrequency}Hz  {cur.dmBitsPerPel}bpp  "
                           f"pos({cur.dmPositionX},{cur.dmPositionY})  {ot}"),
                     font=FONT_MONO, bg=BG3, fg=ACCENT2).pack(anchor="w", pady=(4,0))
        else:
            tk.Label(card, text="No signal — display not active",
                     font=FONT_MONO, bg=BG3, fg=TEXT3).pack(anchor="w", pady=(4,0))

        modes = get_supported_modes(adapter["name"])
        if modes:
            ml = "  ".join(f"{w}×{h}@{f}Hz" for w,h,f in modes[:5])
            if len(modes) > 5:
                ml += f"  +{len(modes)-5} more"
            tk.Label(card, text=f"Supported: {ml}",
                     font=("Consolas",7), bg=BG3, fg=TEXT3).pack(anchor="w")

        ctrl = tk.Frame(card, bg=BG3)
        ctrl.pack(fill=tk.X, pady=(10,0))

        if modes:
            mode_strings = [f"{w}×{h} @ {f}Hz" for w,h,f in modes]
            res_var = tk.StringVar(value=mode_strings[0])
            cb = ttk.Combobox(ctrl, textvariable=res_var, values=mode_strings,
                              width=20, state="readonly", font=FONT_BODY)
            cb.pack(side=tk.LEFT, padx=(0,8))
            self.option_add("*TCombobox*Listbox.background",      BG3)
            self.option_add("*TCombobox*Listbox.foreground",      TEXT)
            self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        else:
            res_var = None

        def do_enable(n=adapter["name"], rv=res_var, ip=is_primary):
            w, h, f = 1366, 768, 60
            if rv:
                try:
                    sel   = rv.get()
                    parts = sel.replace("×","x").replace("Hz","").replace("@","").split()
                    dims  = parts[0].split("x")
                    w, h, f = int(dims[0]), int(dims[1]), int(parts[1])
                except Exception:
                    pass
            all_a = get_all_adapters()
            max_x = max((get_current_mode(a["name"]).dmPositionX +
                         get_current_mode(a["name"]).dmPelsWidth
                         for a in all_a
                         if a["is_active"] and a["name"] != n and get_current_mode(a["name"])),
                        default=0)
            self._log(f"Enabling {n} {w}×{h}@{f}Hz at x={max_x}")
            def _r():
                r  = enable_display(n, max_x, 0, w, h, f)
                r2 = commit_changes()
                ok = r == DISP_CHANGE_SUCCESSFUL and r2 == DISP_CHANGE_SUCCESSFUL
                self.after(0, lambda: self._log(f"{'✓ OK' if ok else '✗ Failed'} — {n}"))
                self.after(300, self.refresh_displays)
            threading.Thread(target=_r, daemon=True).start()

        def do_disable(n=adapter["name"]):
            self._log(f"Disabling {n}...")
            def _r():
                disable_display(n)
                commit_changes()
                self.after(300, self.refresh_displays)
            threading.Thread(target=_r, daemon=True).start()

        en  = self._make_btn(ctrl, "⏻  Enable",  "#0d4f2a", SUCCESS, do_enable)
        dis = self._make_btn(ctrl, "⏼  Disable", "#4a1520", DANGER,  do_disable)
        en.pack(side=tk.LEFT, padx=(0,6))
        dis.pack(side=tk.LEFT)
        if is_primary:
            dis.config(state=tk.DISABLED, fg=TEXT3)

    # ══════════════════════════════════════════════════════════════════════════
    #  DESKTOP PREVIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _draw_preview(self, adapters):
        cv = self._preview_canvas
        cv.delete("all")
        active = [a for a in adapters if a["is_active"]]
        if not active:
            cv.create_text(102, 66, text="No active displays", fill=TEXT3, font=FONT_SMALL)
            return
        modes_d, total_w = {}, 0
        for a in active:
            cur = get_current_mode(a["name"])
            if cur:
                modes_d[a["name"]] = cur
                total_w = max(total_w, cur.dmPositionX + cur.dmPelsWidth)
        if total_w == 0:
            total_w = 1366
        scale = 190 / total_w
        for a in active:
            cur = modes_d.get(a["name"])
            if not cur:
                continue
            x1 = 7  + cur.dmPositionX * scale
            y1 = 16
            x2 = x1 + cur.dmPelsWidth  * scale
            y2 = y1 + cur.dmPelsHeight * scale * 0.58
            clr = ACCENT if a["is_primary"] else ACCENT2
            cv.create_rectangle(x1,y1,x2,y2, fill=BG2, outline=clr, width=2)
            cv.create_rectangle(x1+2,y1+2,x2-2,y2-2, fill=clr, outline="")
            cv.create_text((x1+x2)/2,(y1+y2)/2,
                           text=f"D{a['index']+1}\n{cur.dmPelsWidth}×{cur.dmPelsHeight}",
                           fill="white", font=("Segoe UI",7,"bold"))
        cv.create_text(102, 118, text=f"{len(active)} display(s) active",
                       fill=TEXT2, font=FONT_SMALL)

    # ══════════════════════════════════════════════════════════════════════════
    #  BULK ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _do_auto_enable(self):
        self._log("Auto-enabling inactive displays...")
        def _r():
            adapters = get_all_adapters()
            max_x = max(
                (get_current_mode(a["name"]).dmPositionX + get_current_mode(a["name"]).dmPelsWidth
                 for a in adapters if a["is_active"] and get_current_mode(a["name"])),
                default=1366)
            for a in adapters:
                if not a["is_active"]:
                    rc = enable_display(a["name"], max_x, 0, 1366, 768, 60)
                    self.after(0, lambda n=a["name"], r=rc:
                               self._log(f"{'✓' if r==0 else '✗'} {n}"))
                    if rc == DISP_CHANGE_SUCCESSFUL:
                        max_x += 1366
            commit_changes()
            self.after(300, self.refresh_displays)
        threading.Thread(target=_r, daemon=True).start()

    def _do_extend(self):
        self._log("Extending all displays...")
        def _r():
            x = 0
            for a in get_all_adapters():
                ms = get_supported_modes(a["name"])
                w,h,f = (ms[0][0],ms[0][1],ms[0][2]) if ms else (1366,768,60)
                enable_display(a["name"], x, 0, w, h, f)
                x += w
            commit_changes()
            self.after(300, self.refresh_displays)
        threading.Thread(target=_r, daemon=True).start()

    def _do_mirror(self):
        self._log("Mirroring all displays...")
        def _r():
            adapters = get_all_adapters()
            pri = next((a for a in adapters if a["is_primary"]), adapters[0])
            cur = get_current_mode(pri["name"])
            w = cur.dmPelsWidth if cur else 1366
            h = cur.dmPelsHeight if cur else 768
            f = cur.dmDisplayFrequency if cur else 60
            for a in adapters:
                enable_display(a["name"], 0, 0, w, h, f)
            commit_changes()
            self.after(300, self.refresh_displays)
        threading.Thread(target=_r, daemon=True).start()

    def _do_disable_all_inactive(self):
        self._log("Disabling inactive outputs...")
        def _r():
            for a in get_all_adapters():
                if not a["is_active"] and not a["is_primary"]:
                    disable_display(a["name"])
            commit_changes()
            self.after(300, self.refresh_displays)
        threading.Thread(target=_r, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _sidebar_btn(self, parent, text, color, command):
        f   = tk.Frame(parent, bg=color, cursor="hand2")
        f.pack(fill=tk.X, padx=12, pady=3)
        lbl = tk.Label(f, text=text, font=("Segoe UI",9,"bold"),
                       bg=color, fg="white", anchor="w", padx=10, pady=7)
        lbl.pack(fill=tk.X)
        for w in (f, lbl):
            w.bind("<Button-1>", lambda e, c=command: c())
            w.bind("<Enter>",    lambda e, ww=f, ll=lbl: [ww.config(bg=ACCENT_GLOW),
                                                            ll.config(bg=ACCENT_GLOW)])
            w.bind("<Leave>",    lambda e, ww=f, ll=lbl, c=color: [ww.config(bg=c),
                                                                     ll.config(bg=c)])
        return f

    def _make_btn(self, parent, text, bg, fg, command):
        btn = tk.Button(parent, text=text, font=("Segoe UI",8,"bold"),
                        bg=bg, fg=fg, activebackground=fg, activeforeground="white",
                        relief=tk.FLAT, padx=10, pady=5, cursor="hand2",
                        command=command, bd=0, highlightthickness=0)
        btn.bind("<Enter>", lambda e: btn.config(bg=fg, fg="white"))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg, fg=fg))
        return btn

    def _badge(self, parent, text, color):
        tk.Label(parent, text=f" {text} ", font=("Segoe UI",7,"bold"),
                 bg=color, fg="white", padx=2).pack(side=tk.LEFT, padx=4)

    def _draw_monitor_icon(self, canvas, active):
        c    = ACCENT2 if active else TEXT3
        fill = ACCENT  if active else BG2
        canvas.create_rectangle(2, 2, 40, 26, outline=c, fill=BG, width=2)
        canvas.create_rectangle(5, 5, 37, 23, outline="", fill=fill)
        canvas.create_line(21, 26, 21, 32, fill=c, width=2)
        canvas.create_line(14, 32, 28, 32, fill=c, width=2)
        if active:
            canvas.create_oval(17, 10, 25, 18, fill=SUCCESS, outline="")

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _set_status(self, msg):
        self._status_var.set(msg)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG2, height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Initialising...")
        tk.Label(bar, textvariable=self._status_var,
                 font=FONT_SMALL, bg=BG2, fg=TEXT2, anchor="w"
                 ).pack(side=tk.LEFT, padx=12, pady=4)
        tk.Label(bar, text="Intel® HD Graphics 620  |  PCI VEN_8086 DEV_5916  |  Gen 9.5 Kaby Lake",
                 font=FONT_SMALL, bg=BG2, fg=TEXT3
                 ).pack(side=tk.RIGHT, padx=12, pady=4)
