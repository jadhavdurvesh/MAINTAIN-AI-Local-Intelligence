import json
import os
import socket
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from urllib.request import Request, urlopen

import uvicorn
from app.main import app as api_app

HOST = "127.0.0.1"
PORT = 8000
API = f"http://{HOST}:{PORT}/api"

BG = "#0a0d10"
SURFACE = "#11161b"
SURFACE_2 = "#171d23"
SURFACE_3 = "#202831"
BORDER = "#29323b"
TEXT = "#f5f7fa"
MUTED = "#8e9aa7"
ACCENT = "#39d98a"
ACCENT_SOFT = "#153a2a"
BLUE = "#78aefc"
BLUE_SOFT = "#172b45"
DANGER = "#ff6b6b"
DANGER_SOFT = "#3a2025"
WARNING = "#f4c95d"

# The desktop UI keeps a small catalog of the supported local adapters. This is
# intentionally duplicated from the API contract so a packaged build can still
# render the model workspace while an optional API dependency is initializing.
CATALOG = [
    {"name": "Online anomaly", "kind": "online", "downloadable": False,
     "description": "Fast streaming anomaly statistics. No model download required.",
     "dependencies": "numpy", "source_label": "Built in"},
    {"name": "Random Forest baseline", "kind": "baseline", "downloadable": False,
     "description": "Lightweight local baseline for signal range and statistical checks.",
     "dependencies": "scikit-learn", "source_label": "Built in"},
    {"name": "TimeRadar", "kind": "zero_shot_anomaly", "downloadable": True,
     "description": "Zero-shot time-series anomaly detection using a 100-sample window.",
     "dependencies": "torch, transformers, torch-frft, safetensors", "source_label": "mala-lab/TimeRadar"},
    {"name": "Chronos-2", "kind": "forecast", "downloadable": True,
     "description": "Foundation model for time-series forecasting.",
     "dependencies": "torch, chronos-forecasting", "source_label": "amazon/chronos-2"},
    {"name": "Timer", "kind": "forecast", "downloadable": True,
     "description": "Local foundation model for zero-shot time-series forecasting.",
     "dependencies": "torch, transformers", "source_label": "thuml/timer-base-84m"},
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("1480x940")
        self.minsize(1180, 780)
        self.configure(bg=BG)

        self.engine = None
        self.busy = False
        self.models = []
        self.active_model = None

        self.status_var = tk.StringVar(value="Starting")
        self.detail_var = tk.StringVar(value="Preparing local intelligence…")
        self.progress_var = tk.StringVar(value="Ready")
        self.search_var = tk.StringVar()
        self.machine_var = tk.StringVar(value="machine-001")
        self.horizon_var = tk.StringVar(value="12")
        self.model_var = tk.StringVar(value="Online anomaly")

        self._styles()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(250, self.start)

    # ---------- styling ----------
    def _styles(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("MAINTAIN.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 10),
                    background=SURFACE_3, foreground=TEXT, borderwidth=0)
        s.map("MAINTAIN.TButton", background=[("active", "#2a333d"), ("pressed", "#34404c"), ("disabled", SURFACE)],
              foreground=[("disabled", "#5c6670")])
        s.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(17, 10),
                    background=ACCENT, foreground="#06130d", borderwidth=0)
        s.map("Accent.TButton", background=[("active", "#55eaa0"), ("pressed", "#25bd73"), ("disabled", "#234d39")])
        s.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 10),
                    background=DANGER_SOFT, foreground="#ffb7b7", borderwidth=0)
        s.map("Danger.TButton", background=[("active", "#54272d"), ("disabled", SURFACE)])
        s.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    rowheight=52, borderwidth=0, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=SURFACE_2, foreground=MUTED,
                    borderwidth=0, font=("Segoe UI", 9, "bold"), padding=(10, 10))
        s.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT)])
        s.configure("Horizontal.TProgressbar", troughcolor=SURFACE_3, background=ACCENT,
                    bordercolor=SURFACE_3, lightcolor=ACCENT, darkcolor=ACCENT, thickness=5)
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=SURFACE_2, foreground=MUTED, padding=(20, 10), font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", SURFACE)], foreground=[("selected", TEXT)])
        s.configure("Search.TEntry", fieldbackground=SURFACE_2, foreground=TEXT, insertcolor=TEXT,
                    borderwidth=0, padding=(10, 8))
        s.configure("MAINTAIN.TCombobox", fieldbackground=SURFACE_2, background=SURFACE_2,
                    foreground=TEXT, arrowcolor=MUTED, borderwidth=0, padding=(10, 8))

    def _label(self, parent, text=None, size=10, color=TEXT, weight="normal", **kw):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, weight), **kw)

    def _button(self, parent, text, command, style="MAINTAIN.TButton", **kw):
        return ttk.Button(parent, text=text, command=command, style=style, **kw)

    def _card(self, parent, **kw):
        return tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, **kw)

    # ---------- UI ----------
    def _build(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=34, pady=(24, 16))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self._label(brand, "MAINTAIN AI", 27, TEXT, "bold").pack(anchor="w")
        self._label(brand, "LOCAL INTELLIGENCE   /   EDGE INFERENCE", 9, MUTED, "bold").pack(anchor="w", pady=(2, 0))

        status = tk.Frame(header, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        status.pack(side="right", ipadx=14, ipady=8)
        row = tk.Frame(status, bg=SURFACE)
        row.pack()
        self.status_dot = tk.Label(row, text="●", bg=SURFACE, fg=ACCENT, font=("Segoe UI", 10, "bold"))
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_label = self._label(row, "Starting", 10, TEXT, "bold")
        self.status_label.pack(side="left")
        self._label(status, None, 8, MUTED, textvariable=self.detail_var).pack(anchor="e", pady=(2, 0))

        hero = self._card(root)
        hero.pack(fill="x", padx=34, pady=(0, 14))
        left = tk.Frame(hero, bg=SURFACE)
        left.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        self._label(left, "Edge inference workspace", 20, TEXT, "bold").pack(anchor="w")
        self._label(left, "Detect anomalies and generate forecasts on this PC. Models stay local; the desktop app is an operator workspace, not a training console.",
                    10, MUTED, wraplength=820, justify="left").pack(anchor="w", pady=(6, 0))

        stats = tk.Frame(hero, bg=SURFACE)
        stats.pack(side="right", padx=20, pady=16)
        self.model_stat = self._stat(stats, "MODELS", "0")
        self.model_stat.pack(side="left", padx=4)
        self.ready_stat = self._stat(stats, "READY", "0")
        self.ready_stat.pack(side="left", padx=4)
        self.storage_stat = self._stat(stats, "LOCAL DATA", "—")
        self.storage_stat.pack(side="left", padx=4)

        toolbar = tk.Frame(root, bg=BG)
        toolbar.pack(fill="x", padx=34, pady=(0, 10))
        self.start_btn = self._button(toolbar, "Start Engine", self.start, "Accent.TButton")
        self.start_btn.pack(side="left")
        self.stop_btn = self._button(toolbar, "Stop", self.stop)
        self.stop_btn.pack(side="left", padx=(8, 0))
        self.refresh_btn = self._button(toolbar, "Refresh", self.refresh)
        self.refresh_btn.pack(side="left", padx=(8, 0))
        self.docs_btn = self._button(toolbar, "API Docs", self.open_docs)
        self.docs_btn.pack(side="left", padx=(8, 0))
        self.data_btn = self._button(toolbar, "Data Folder", self.open_data_folder)
        self.data_btn.pack(side="left", padx=(8, 0))
        self.diag_btn = self._button(toolbar, "Diagnostics", self.diagnostics)
        self.diag_btn.pack(side="left", padx=(8, 0))

        search = tk.Frame(toolbar, bg=BG)
        search.pack(side="right")
        self._label(search, "⌕", 15, MUTED).pack(side="left", padx=(0, 6))
        ttk.Entry(search, textvariable=self.search_var, width=25, style="Search.TEntry").pack(side="left")
        self.search_var.trace_add("write", lambda *_: self.render_models())

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=34, pady=(0, 10))
        self.workspace_tab = tk.Frame(self.tabs, bg=BG)
        self.models_tab = tk.Frame(self.tabs, bg=BG)
        self.system_tab = tk.Frame(self.tabs, bg=BG)
        self.tabs.add(self.workspace_tab, text="  Workspace  ")
        self.tabs.add(self.models_tab, text="  Models  ")
        self.tabs.add(self.system_tab, text="  System  ")
        self._build_workspace()
        self._build_models()
        self._build_system()

        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", padx=34, pady=(0, 16))
        top = tk.Frame(footer, bg=BG)
        top.pack(fill="x")
        self._label(top, None, 9, MUTED, textvariable=self.progress_var).pack(side="left")
        self._label(top, "LOCAL ONLY   •   127.0.0.1:8000", 8, MUTED).pack(side="right")
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(7, 7))
        self._label(footer, "Data  ~/.maintain-ai    •    Models  ~/.maintain-ai/models", 8, "#68737e").pack(anchor="w")
        self.update_buttons()

    def _stat(self, parent, title, value):
        f = tk.Frame(parent, bg=SURFACE_2, width=96, height=66)
        f.pack_propagate(False)
        self._label(f, title, 7, MUTED, "bold").pack(anchor="w", padx=10, pady=(10, 0))
        lab = self._label(f, value, 17, TEXT, "bold")
        lab.pack(anchor="w", padx=10, pady=(2, 0))
        f.value_label = lab
        return f

    def _build_workspace(self):
        outer = tk.Frame(self.workspace_tab, bg=BG)
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        controls = self._card(outer)
        controls.pack(side="left", fill="y", padx=(0, 10))
        self._label(controls, "RUN INFERENCE", 9, MUTED, "bold").pack(anchor="w", padx=20, pady=(20, 5))
        self._label(controls, "Model", 9, MUTED).pack(anchor="w", padx=20, pady=(12, 4))
        self.model_combo = ttk.Combobox(controls, textvariable=self.model_var, state="readonly", width=28, style="MAINTAIN.TCombobox")
        self.model_combo.pack(padx=20, fill="x")
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_combo)

        self._label(controls, "Machine / asset", 9, MUTED).pack(anchor="w", padx=20, pady=(18, 4))
        ttk.Entry(controls, textvariable=self.machine_var, width=28, style="Search.TEntry").pack(padx=20, fill="x")
        self._label(controls, "Forecast horizon", 9, MUTED).pack(anchor="w", padx=20, pady=(18, 4))
        ttk.Entry(controls, textvariable=self.horizon_var, width=10, style="Search.TEntry").pack(anchor="w", padx=20)

        self.run_btn = self._button(controls, "Run Analysis", self.run_inference, "Accent.TButton")
        self.run_btn.pack(fill="x", padx=20, pady=(24, 8))
        self.use_model_btn = self._button(controls, "Open Model Library", lambda: self.tabs.select(self.models_tab))
        self.use_model_btn.pack(fill="x", padx=20, pady=6)
        self._label(controls, "INPUT", 8, ACCENT, "bold").pack(anchor="w", padx=20, pady=(26, 5))
        self._label(controls, "Enter telemetry as comma/newline separated numeric samples. The last sample is treated as the newest observation.",
                    9, MUTED, wraplength=250, justify="left").pack(anchor="w", padx=20)

        right = tk.Frame(outer, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        input_card = self._card(right)
        input_card.pack(fill="both", expand=True)
        head = tk.Frame(input_card, bg=SURFACE)
        head.pack(fill="x", padx=18, pady=(16, 8))
        self._label(head, "Telemetry", 12, TEXT, "bold").pack(side="left")
        self._label(head, "Local input • never uploaded", 8, MUTED).pack(side="right")
        self.telemetry = tk.Text(input_card, bg="#0d1216", fg=TEXT, insertbackground=TEXT,
                                 relief="flat", borderwidth=0, font=("Consolas", 10), wrap="word", padx=16, pady=14)
        self.telemetry.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.telemetry.insert("1.0", "101, 102, 100, 103, 101, 102, 104, 105, 103, 106")

        result = self._card(right)
        result.pack(fill="both", expand=True, pady=(10, 0))
        self._label(result, "RESULT", 9, MUTED, "bold").pack(anchor="w", padx=18, pady=(15, 5))
        self.result_title = self._label(result, "Ready", 17, TEXT, "bold")
        self.result_title.pack(anchor="w", padx=18)
        self.result_text = tk.Text(result, bg=SURFACE, fg=MUTED, relief="flat", borderwidth=0,
                                   font=("Consolas", 9), wrap="word", height=9, padx=18, pady=10)
        self.result_text.pack(fill="both", expand=True, padx=8, pady=(4, 10))
        self.result_text.insert("1.0", "Start the local engine, choose a model, then run an analysis.")
        self.result_text.configure(state="disabled")

    def _build_models(self):
        body = tk.Frame(self.models_tab, bg=BG)
        body.pack(fill="both", expand=True)
        library = self._card(body)
        library.pack(side="left", fill="both", expand=True, padx=(0, 10))
        h = tk.Frame(library, bg=SURFACE)
        h.pack(fill="x", padx=18, pady=(15, 10))
        self._label(h, "Local model library", 13, TEXT, "bold").pack(side="left")
        self._label(h, "Built-in adapters are ready immediately", 9, MUTED).pack(side="right")
        tw = tk.Frame(library, bg=SURFACE)
        tw.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        cols = ("name", "kind", "state", "size", "source")
        self.tree = ttk.Treeview(tw, columns=cols, show="headings", selectmode="extended")
        widths = {"name": 210, "kind": 150, "state": 130, "size": 100, "source": 260}
        for c, w in widths.items():
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tw, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection)
        self.tree.bind("<Double-1>", lambda _e: self.use_selected_model())

        details = self._card(body, width=360)
        details.pack(side="right", fill="y")
        details.pack_propagate(False)
        self._label(details, "MODEL", 9, MUTED, "bold").pack(anchor="w", padx=20, pady=(20, 4))
        self.selection_var = tk.StringVar(value="No model selected")
        self.selection_detail = tk.StringVar(value="Select a model to inspect readiness, capabilities and storage.")
        tk.Label(details, textvariable=self.selection_var, bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 18, "bold"), wraplength=315, justify="left").pack(anchor="w", padx=20)
        self.state_pill = tk.Label(details, text="NOT SELECTED", bg=SURFACE_3, fg=MUTED,
                                   font=("Segoe UI", 8, "bold"), padx=9, pady=5)
        self.state_pill.pack(anchor="w", padx=20, pady=(10, 13))
        tk.Label(details, textvariable=self.selection_detail, bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 10), wraplength=315, justify="left", anchor="nw").pack(fill="x", padx=20)
        self.use_selected_btn = self._button(details, "Use In Workspace", self.use_selected_model, "Accent.TButton")
        self.use_selected_btn.pack(fill="x", padx=20, pady=(24, 6))
        self.install_btn = self._button(details, "Install Selected", self.install_selected)
        self.install_btn.pack(fill="x", padx=20, pady=6)
        self.remove_btn = self._button(details, "Delete Downloaded", self.delete_selected, "Danger.TButton")
        self.remove_btn.pack(fill="x", padx=20, pady=6)
        self.unload_btn = self._button(details, "Unload From Memory", self.unload_selected)
        self.unload_btn.pack(fill="x", padx=20, pady=6)
        self.folder_btn = self._button(details, "Open Models Folder", self.open_models_folder)
        self.folder_btn.pack(fill="x", padx=20, pady=6)

        info = tk.Frame(details, bg=SURFACE_2)
        info.pack(fill="x", padx=20, pady=(20, 0))
        self._label(info, "LOCAL-FIRST", 8, ACCENT, "bold").pack(anchor="w", padx=12, pady=(11, 3))
        self._label(info, "Models are optional. Built-in statistical adapters work without a download; large foundation models are installed only when needed.",
                    9, MUTED, wraplength=290, justify="left").pack(anchor="w", padx=12, pady=(0, 11))

    def _build_system(self):
        body = tk.Frame(self.system_tab, bg=BG)
        body.pack(fill="both", expand=True)
        for title, value in [
            ("LOCAL API", "127.0.0.1:8000"),
            ("DATA", os.path.expanduser("~/.maintain-ai")),
            ("MODELS", os.path.expanduser("~/.maintain-ai/models")),
            ("PRIVACY", "Local inference • no telemetry upload from this desktop control panel"),
        ]:
            card = self._card(body)
            card.pack(fill="x", pady=(0, 10))
            self._label(card, title, 8, MUTED, "bold").pack(anchor="w", padx=18, pady=(14, 3))
            self._label(card, value, 11, TEXT).pack(anchor="w", padx=18, pady=(0, 14))
        self._label(body, "Use Diagnostics to verify the local API and model manager. API Docs opens the local FastAPI contract.",
                    9, MUTED, wraplength=700, justify="left").pack(anchor="w", pady=(8, 0))

    # ---------- status / state ----------
    def set_status(self, status, detail, color=ACCENT):
        self.status_var.set(status)
        self.detail_var.set(detail)
        self.status_label.configure(text=status)
        self.status_dot.configure(fg=color)
        self.update_buttons()

    def update_stats(self):
        installed = [m for m in self.models if m.get("installed")]
        ready = [m for m in installed if m.get("available") or not m.get("downloadable")]
        size_mb = sum(float(m.get("size_mb") or 0) for m in installed)
        self.model_stat.value_label.configure(text=str(len(self.models)))
        self.ready_stat.value_label.configure(text=str(len(ready)))
        self.storage_stat.value_label.configure(text=f"{size_mb / 1024:.1f} GB" if size_mb >= 1024 else (f"{size_mb:.0f} MB" if size_mb else "—"))

    def update_buttons(self):
        running = bool(self.engine and self.engine.is_alive())
        selected = self.selected_models() if hasattr(self, "tree") else []
        downloadable_missing = any(m.get("downloadable") and not m.get("installed") for m in selected)
        removable = any(m.get("downloadable") and m.get("installed") for m in selected)
        self.start_btn.configure(state="disabled" if running or self.busy else "normal")
        self.stop_btn.configure(state="normal" if running and not self.busy else "disabled")
        self.refresh_btn.configure(state="disabled" if self.busy else "normal")
        self.run_btn.configure(state="normal" if running and not self.busy else "disabled")
        self.install_btn.configure(state="normal" if running and downloadable_missing and not self.busy else "disabled")
        self.remove_btn.configure(state="normal" if running and removable and not self.busy else "disabled")
        self.unload_btn.configure(state="normal" if running and selected and not self.busy else "disabled")
        self.use_selected_btn.configure(state="normal" if selected and not self.busy else "disabled")

    # ---------- engine ----------
    def start(self):
        if self.engine and self.engine.is_alive():
            self.refresh()
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex((HOST, PORT)) == 0:
                    self.set_status("Port in use", f"{HOST}:{PORT} is already occupied", DANGER)
                    return
            self.busy = True
            self.set_status("Starting", "Launching local inference API…", BLUE)
            config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning", access_log=False, log_config=None)
            self.engine = uvicorn.Server(config)
            threading.Thread(target=self._run_engine, daemon=True, name="maintain-api").start()
            threading.Thread(target=self._wait_ready, daemon=True, name="maintain-api-health").start()
        except Exception as exc:
            self._engine_failed(exc)

    def _run_engine(self):
        try:
            self.engine.run()
        except Exception as exc:
            self.after(0, lambda e=exc: self._engine_failed(e))

    def _wait_ready(self):
        last = None
        for _ in range(80):
            try:
                with urlopen(f"{API}/health", timeout=1) as r:
                    if r.status == 200:
                        self.after(0, self._engine_ready)
                        return
            except Exception as exc:
                last = exc
                time.sleep(0.25)
        self.after(0, lambda: self._engine_failed(RuntimeError(f"Local API did not become ready: {last}")))

    def _engine_ready(self):
        self.busy = False
        self.set_status("Running", "Local API ready • loading intelligence workspace", ACCENT)
        self.progress_var.set("Engine ready")
        self.refresh()

    def _engine_failed(self, exc):
        self.engine = None
        self.busy = False
        self.set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER)
        messagebox.showerror("MAINTAIN AI", f"The local engine could not start.\n\n{exc}")

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="indeterminate")
        self.progress_var.set("Engine stopped")
        self.models = self._catalog_with_defaults([])
        self.render_models()
        self.update_stats()
        self.set_status("Stopped", "Local inference engine is not running", MUTED)
        self.update_model_combo()
        self.update_buttons()

    # ---------- models ----------
    def _catalog_with_defaults(self, api_models):
        by_name = {m.get("name"): dict(m) for m in api_models if isinstance(m, dict)}
        merged = []
        for base in CATALOG:
            item = dict(base)
            item.update(by_name.get(base["name"], {}))
            if base["name"] in {"Online anomaly", "Random Forest baseline"}:
                item["installed"] = True
                item["available"] = True
            else:
                item["installed"] = bool(item.get("installed", False))
                item["available"] = bool(item.get("available", item["installed"]))
            item.setdefault("size_mb", 0)
            item.setdefault("source", "built-in" if not base["downloadable"] else "optional")
            merged.append(item)
        return merged

    def refresh(self):
        if not (self.engine and self.engine.is_alive()):
            self.models = self._catalog_with_defaults([])
            self.render_models()
            self.update_stats()
            self.update_model_combo()
            self.set_status("Stopped", "Start the local engine to sync model readiness", MUTED)
            return self.models
        try:
            with urlopen(f"{API}/model-manager", timeout=5) as response:
                data = json.load(response)
            api_models = data.get("models", []) if isinstance(data, dict) else []
            self.models = self._catalog_with_defaults(api_models)
            self.render_models()
            self.update_stats()
            self.update_model_combo()
            self.set_status("Running", f"Local API ready • {len(self.models)} adapters available", ACCENT)
            return self.models
        except Exception as exc:
            # Keep the operator workspace usable if the optional manager endpoint
            # is temporarily unavailable in a packaged build.
            self.models = self._catalog_with_defaults([])
            self.render_models()
            self.update_stats()
            self.update_model_combo()
            self.set_status("Running", f"API ready • model catalog fallback ({type(exc).__name__})", WARNING)
            return self.models

    def render_models(self):
        if not hasattr(self, "tree"):
            return
        query = self.search_var.get().strip().lower()
        selected_names = {self.tree.item(i, "values")[0] for i in self.tree.selection() if self.tree.exists(i)}
        self.tree.delete(*self.tree.get_children())
        for m in self.models:
            name = m.get("name", "")
            haystack = " ".join(str(m.get(k, "")) for k in ("name", "kind", "source_label", "description")).lower()
            if query and query not in haystack:
                continue
            installed = bool(m.get("installed"))
            state = "READY" if installed else "AVAILABLE"
            if m.get("downloadable") and not installed:
                state = "INSTALL"
            elif installed and not m.get("downloadable"):
                state = "BUILT-IN"
            size = f"{m.get('size_mb', 0):g} MB" if installed and m.get("size_mb") else ("Built in" if not m.get("downloadable") else "—")
            iid = "m" + str(len(self.tree.get_children()))
            self.tree.insert("", "end", iid=iid, values=(name, m.get("kind", ""), state, size, m.get("source_label", "Local")))
            if name in selected_names:
                self.tree.selection_add(iid)
        self.on_selection()

    def update_model_combo(self):
        if not hasattr(self, "model_combo"):
            return
        names = [m["name"] for m in self.models]
        self.model_combo.configure(values=names)
        if self.model_var.get() not in names and names:
            self.model_var.set(names[0])

    def on_model_combo(self, _event=None):
        self.active_model = self.model_var.get()
        model = next((m for m in self.models if m.get("name") == self.active_model), None)
        if model and model.get("downloadable") and not model.get("installed"):
            self.progress_var.set(f"{self.active_model} is not installed — install it from Models")
        else:
            self.progress_var.set(f"Selected {self.active_model}")

    def on_selection(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.selection_var.set("No model selected")
            self.selection_detail.set("Select a model to inspect readiness, capabilities and storage.")
            self.state_pill.configure(text="NOT SELECTED", bg=SURFACE_3, fg=MUTED)
            self.update_buttons()
            return
        names = [self.tree.item(i, "values")[0] for i in selected]
        if len(names) > 1:
            self.selection_var.set(f"{len(names)} models selected")
            self.state_pill.configure(text="MULTI-SELECT", bg=BLUE_SOFT, fg=BLUE)
            self.selection_detail.set("Install missing downloadable models, delete installed downloadable models, or unload their in-memory caches.")
            self.update_buttons()
            return
        m = next((x for x in self.models if x.get("name") == names[0]), None)
        self.selection_var.set(names[0])
        if not m:
            return
        installed = bool(m.get("installed"))
        if installed and not m.get("downloadable"):
            state, bg, fg = "BUILT-IN", BLUE_SOFT, BLUE
        elif installed:
            state, bg, fg = "READY", ACCENT_SOFT, ACCENT
        else:
            state, bg, fg = "INSTALL", SURFACE_3, MUTED
        self.state_pill.configure(text=state, bg=bg, fg=fg)
        size = f"{m.get('size_mb', 0):g} MB locally" if installed and m.get("size_mb") else ("Built into the application" if not m.get("downloadable") else "Not downloaded")
        self.selection_detail.set(f"{m.get('description', '')}\n\nReadiness: {state}\nStorage: {size}\nSource: {m.get('source_label', 'Local')}\nDependencies: {m.get('dependencies', '—')}")
        self.update_buttons()

    def selected_models(self):
        if not hasattr(self, "tree"):
            return []
        names = [self.tree.item(i, "values")[0] for i in self.tree.selection()]
        return [m for m in self.models if m.get("name") in names]

    def use_selected_model(self):
        selected = self.selected_models()
        if not selected:
            return
        if len(selected) != 1:
            messagebox.showinfo("Model", "Select one model to use in the inference workspace.")
            return
        name = selected[0]["name"]
        self.model_var.set(name)
        self.active_model = name
        self.tabs.select(self.workspace_tab)
        self.on_model_combo()

    # ---------- download / delete ----------
    def post_json(self, url):
        with urlopen(Request(url, method="POST"), timeout=10) as response:
            return json.load(response)

    def install_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and not m.get("installed")]
        if not models:
            messagebox.showinfo("Models", "Select a downloadable model marked INSTALL.")
            return
        names = "\n".join("• " + m["name"] for m in models)
        if messagebox.askyesno("Install Models", f"Download these models to local storage?\n\n{names}"):
            self.download_queue(models)

    def download_queue(self, models):
        if self.busy:
            return
        self.busy = True
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        self.progress_var.set("Preparing model downloads…")
        self.update_buttons()
        threading.Thread(target=self._download_worker, args=(list(models),), daemon=True).start()

    def _download_worker(self, models):
        failures = []
        total = len(models)
        for i, model in enumerate(models, 1):
            name = model["name"]
            try:
                self.after(0, lambda n=name, x=i: self.progress_var.set(f"Installing {n}  •  {x}/{total}"))
                result = self.post_json(f"{API}/model-manager/{name}/download")
                job = result.get("job_id")
                if job:
                    self._wait_job(job, name, i, total)
                elif result.get("state") == "error":
                    raise RuntimeError(result.get("message", "Download failed"))
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
        self.after(0, lambda: self._download_finished(failures))

    def _wait_job(self, job_id, name, index, total):
        while True:
            with urlopen(f"{API}/model-manager/jobs/{job_id}", timeout=5) as r:
                job = json.load(r)
            state = job.get("state", "unknown")
            progress = job.get("progress")
            message = job.get("message", "Working…")
            if isinstance(progress, (int, float)):
                self.after(0, lambda p=progress, n=name, i=index: (self.progress.configure(mode="determinate", value=p), self.progress_var.set(f"{n}  •  {p:.0f}%  •  {i}/{total}")))
            else:
                self.after(0, lambda n=name, i=index, msg=message: self.progress_var.set(f"{n}  •  {msg}  •  {i}/{total}"))
            if state == "done":
                return
            if state == "error":
                raise RuntimeError(message)
            time.sleep(0.8)

    def _download_finished(self, failures):
        self.progress.stop()
        self.progress.configure(mode="indeterminate")
        self.busy = False
        if failures:
            self.progress_var.set("Installation finished with errors")
            messagebox.showerror("Model Installation", "Some models could not be installed:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Model installation complete")
            messagebox.showinfo("Model Installation", "The selected model(s) are now stored locally.")
        self.refresh()
        self.update_buttons()

    def delete_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and m.get("installed")]
        if not models:
            messagebox.showinfo("Models", "Select an installed downloadable model to delete.")
            return
        names = "\n".join("• " + m["name"] for m in models)
        if not messagebox.askyesno("Delete Models", f"Delete these downloaded model files?\n\n{names}\n\nBuilt-in adapters are protected."):
            return
        failures = []
        for m in models:
            try:
                with urlopen(Request(f"{API}/model-manager/{m['name']}", method="DELETE"), timeout=10) as r:
                    json.load(r)
            except Exception as exc:
                failures.append(f"{m['name']}: {type(exc).__name__}: {exc}")
        if failures:
            messagebox.showerror("Delete Models", "Some models could not be deleted:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Downloaded model files deleted")
        self.refresh()

    def unload_selected(self):
        models = self.selected_models()
        if not models:
            return
        failures = []
        count = 0
        for m in models:
            try:
                with urlopen(Request(f"{API}/model-manager/{m['name']}/unload", method="POST"), timeout=10) as r:
                    result = json.load(r)
                count += int(bool(result.get("unloaded")))
            except Exception as exc:
                failures.append(f"{m['name']}: {type(exc).__name__}: {exc}")
        if failures:
            messagebox.showerror("Unload", "Some caches could not be cleared:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set(f"Memory caches cleared • {count} model(s)")

    # ---------- inference ----------
    def _parse_values(self):
        raw = self.telemetry.get("1.0", "end").replace("\n", ",")
        values = []
        for part in raw.split(","):
            part = part.strip()
            if part:
                values.append(float(part))
        if len(values) < 2:
            raise ValueError("Enter at least 2 numeric telemetry samples.")
        return values

    def run_inference(self):
        if not (self.engine and self.engine.is_alive()):
            messagebox.showwarning("Engine", "Start the local engine first.")
            return
        try:
            values = self._parse_values()
            horizon = max(1, min(512, int(self.horizon_var.get() or "12")))
            model = self.model_var.get()
            endpoint = {
                "Online anomaly": "online",
                "Random Forest baseline": "baseline",
                "TimeRadar": "timeradar",
                "Chronos-2": "chronos2",
                "Timer": "timer",
            }.get(model)
            if not endpoint:
                raise ValueError("Choose a supported model.")
            local = next((m for m in self.models if m.get("name") == model), None)
            if local and local.get("downloadable") and not local.get("installed"):
                messagebox.showinfo("Model not installed", f"Install {model} from the Models tab before running it.")
                self.tabs.select(self.models_tab)
                return
            self.busy = True
            self.update_buttons()
            self.progress_var.set(f"Running {model} locally…")
            payload = json.dumps({"machine_id": self.machine_var.get().strip() or "machine-001", "values": values, "horizon": horizon}).encode()
            threading.Thread(target=self._inference_worker, args=(endpoint, payload, model), daemon=True).start()
        except Exception as exc:
            messagebox.showerror("Inference", str(exc))

    def _inference_worker(self, endpoint, payload, model):
        try:
            req = Request(f"{API}/inference/{endpoint}", data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=120) as response:
                result = json.load(response)
            self.after(0, lambda: self._show_result(model, result))
        except Exception as exc:
            self.after(0, lambda: self._show_result(model, {"available": False, "error": f"{type(exc).__name__}: {exc}"}))

    def _show_result(self, model, result):
        self.busy = False
        self.progress_var.set(f"Analysis complete • {model}")
        self.result_title.configure(text=f"{model} • {'Ready' if result.get('available', True) else 'Unavailable'}")
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
        self.result_text.configure(state="disabled")
        self.update_buttons()

    # ---------- utilities ----------
    def open_docs(self):
        webbrowser.open(f"{API[:-4]}/docs")

    def open_path(self, path):
        os.makedirs(path, exist_ok=True)
        if os.name == "nt":
            os.startfile(path)
        else:
            webbrowser.open("file://" + path)

    def open_data_folder(self):
        self.open_path(os.path.expanduser("~/.maintain-ai"))

    def open_models_folder(self):
        self.open_path(os.path.expanduser("~/.maintain-ai/models"))

    def diagnostics(self):
        checks = []
        try:
            with urlopen(f"{API}/health", timeout=2) as r:
                checks.append(f"API health: OK • HTTP {r.status}")
        except Exception as exc:
            checks.append(f"API health: FAILED • {type(exc).__name__}: {exc}")
        try:
            with urlopen(f"{API}/model-manager", timeout=3) as r:
                data = json.load(r)
            checks.append(f"Model manager: OK • {len(data.get('models', []))} API models")
        except Exception as exc:
            checks.append(f"Model manager: FAILED • {type(exc).__name__}: {exc}")
        checks.append(f"Desktop catalog: {len(CATALOG)} supported adapters")
        checks.append(f"Engine: {'running' if self.engine and self.engine.is_alive() else 'stopped'}")
        checks.append(f"Models directory: {os.path.expanduser('~/.maintain-ai/models')}")
        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def on_close(self):
        if self.engine:
            self.engine.should_exit = True
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
