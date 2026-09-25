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

# MAINTAIN AI desktop palette — quiet graphite + mint accent.
BG = "#0b0d10"
SURFACE = "#111418"
SURFACE_2 = "#171b20"
SURFACE_3 = "#1d2228"
BORDER = "#282e35"
TEXT = "#f5f7fa"
MUTED = "#98a2ad"
ACCENT = "#32d583"
ACCENT_SOFT = "#17372a"
BLUE = "#6ea8fe"
BLUE_SOFT = "#172942"
DANGER = "#ff6b6b"
DANGER_SOFT = "#3a1d21"
WARNING = "#f4c95d"
WHITE = "#ffffff"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("1440x900")
        self.minsize(1180, 760)
        self.configure(bg=BG)

        self.engine = None
        self.models = []
        self.busy = False
        self.active_model = None

        self.status_var = tk.StringVar(value="Starting")
        self.detail_var = tk.StringVar(value="Preparing local intelligence…")
        self.selection_var = tk.StringVar(value="No model selected")
        self.selection_detail = tk.StringVar(value="Select a model to see capabilities, storage and dependencies.")
        self.progress_var = tk.StringVar(value="Ready")
        self.search_var = tk.StringVar()

        self.build_styles()
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(250, self.start)

    def build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("MAINTAIN.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 10), background=SURFACE_3, foreground=TEXT, borderwidth=0, relief="flat")
        style.map("MAINTAIN.TButton", background=[("active", "#262d35"), ("pressed", "#303944"), ("disabled", SURFACE)], foreground=[("disabled", "#5f6974")])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(17, 10), background=ACCENT, foreground="#07120d", borderwidth=0, relief="flat")
        style.map("Accent.TButton", background=[("active", "#54e69a"), ("pressed", "#25bd73"), ("disabled", "#244b39")], foreground=[("disabled", "#6d9581")])
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 10), background=DANGER_SOFT, foreground="#ffb2b2", borderwidth=0, relief="flat")
        style.map("Danger.TButton", background=[("active", "#51262c"), ("disabled", SURFACE)])
        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT, rowheight=58, borderwidth=0, relief="flat", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=SURFACE_2, foreground=MUTED, borderwidth=0, relief="flat", font=("Segoe UI", 9, "bold"), padding=(12, 10))
        style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", WHITE)])
        style.configure("Horizontal.TProgressbar", troughcolor=SURFACE_3, background=ACCENT, bordercolor=SURFACE_3, lightcolor=ACCENT, darkcolor=ACCENT, thickness=6)
        style.configure("Search.TEntry", fieldbackground=SURFACE_2, foreground=TEXT, insertcolor=TEXT, borderwidth=0, padding=(12, 9))

    def label(self, parent, text=None, size=10, color=TEXT, weight="normal", **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color, font=("Segoe UI", size, weight), **kwargs)

    def button(self, parent, text, command, style="MAINTAIN.TButton", **kwargs):
        return ttk.Button(parent, text=text, command=command, style=style, **kwargs)

    def build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=34, pady=(24, 14))
        brand = tk.Frame(top, bg=BG)
        brand.pack(side="left")
        self.label(brand, "MAINTAIN AI", 26, TEXT, "bold").pack(anchor="w")
        self.label(brand, "LOCAL INTELLIGENCE  /  EDGE INFERENCE", 9, MUTED, "bold").pack(anchor="w", pady=(2, 0))

        status_card = tk.Frame(top, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        status_card.pack(side="right", ipadx=14, ipady=7)
        status_row = tk.Frame(status_card, bg=SURFACE)
        status_row.pack()
        self.status_dot = tk.Label(status_row, text="●", bg=SURFACE, fg=ACCENT, font=("Segoe UI", 10, "bold"))
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_label = self.label(status_row, "Starting", 10, TEXT, "bold")
        self.status_label.pack(side="left")
        self.label(status_card, None, 8, MUTED, textvariable=self.detail_var).pack(anchor="e", pady=(2, 0))

        hero = tk.Frame(root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        hero.pack(fill="x", padx=34, pady=(0, 14))
        hero_left = tk.Frame(hero, bg=SURFACE)
        hero_left.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        self.label(hero_left, "Local model workspace", 19, TEXT, "bold").pack(anchor="w")
        self.label(hero_left, "Run MAINTAIN AI inference on this PC. Download only what you need; nothing is trained here.", 10, MUTED, wraplength=700, justify="left").pack(anchor="w", pady=(6, 0))

        stats = tk.Frame(hero, bg=SURFACE)
        stats.pack(side="right", padx=22, pady=16)
        self.models_stat = self.stat_card(stats, "MODELS", "0")
        self.models_stat.pack(side="left", padx=5)
        self.storage_stat = self.stat_card(stats, "LOCAL STORAGE", "—")
        self.storage_stat.pack(side="left", padx=5)

        actions = tk.Frame(root, bg=BG)
        actions.pack(fill="x", padx=34, pady=(0, 12))
        self.start_btn = self.button(actions, "Start Engine", self.start, "Accent.TButton")
        self.start_btn.pack(side="left")
        self.stop_btn = self.button(actions, "Stop", self.stop)
        self.stop_btn.pack(side="left", padx=(8, 0))
        self.refresh_btn = self.button(actions, "Refresh", self.refresh)
        self.refresh_btn.pack(side="left", padx=(8, 0))
        self.download_all_btn = self.button(actions, "Download All", self.download_all)
        self.download_all_btn.pack(side="left", padx=(8, 0))
        self.docs_btn = self.button(actions, "API Docs", self.open_docs)
        self.docs_btn.pack(side="left", padx=(8, 0))
        self.data_btn = self.button(actions, "Data Folder", self.open_data_folder)
        self.data_btn.pack(side="left", padx=(8, 0))
        self.diagnostics_btn = self.button(actions, "Diagnostics", self.diagnostics)
        self.diagnostics_btn.pack(side="left", padx=(8, 0))

        search_wrap = tk.Frame(actions, bg=BG)
        search_wrap.pack(side="right")
        self.label(search_wrap, "⌕", 16, MUTED).pack(side="left", padx=(0, 5))
        search = ttk.Entry(search_wrap, textvariable=self.search_var, width=25, style="Search.TEntry")
        search.pack(side="left")
        self.search_var.trace_add("write", lambda *_: self.render_models())

        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=34, pady=(0, 12))

        library = tk.Frame(content, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        library.pack(side="left", fill="both", expand=True)
        lib_head = tk.Frame(library, bg=SURFACE)
        lib_head.pack(fill="x", padx=18, pady=(15, 10))
        self.label(lib_head, "Model Library", 12, TEXT, "bold").pack(side="left")
        self.label(lib_head, "Select a model to install, inspect or remove", 9, MUTED).pack(side="right")

        tree_wrap = tk.Frame(library, bg=SURFACE)
        tree_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        cols = ("name", "kind", "state", "size", "source")
        self.tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", selectmode="extended")
        widths = {"name": 190, "kind": 145, "state": 125, "size": 95, "source": 240}
        for col, width in widths.items():
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection)
        self.tree.bind("<Double-1>", lambda _event: self.install_selected())

        details = tk.Frame(content, bg=SURFACE, width=370, highlightbackground=BORDER, highlightthickness=1)
        details.pack(side="right", fill="y", padx=(14, 0))
        details.pack_propagate(False)
        self.label(details, "MODEL DETAILS", 9, MUTED, "bold").pack(anchor="w", padx=20, pady=(19, 4))
        tk.Label(details, textvariable=self.selection_var, bg=SURFACE, fg=TEXT, font=("Segoe UI", 18, "bold"), wraplength=325, justify="left").pack(anchor="w", padx=20)
        self.state_pill = tk.Label(details, text="NOT SELECTED", bg=SURFACE_3, fg=MUTED, font=("Segoe UI", 8, "bold"), padx=9, pady=5)
        self.state_pill.pack(anchor="w", padx=20, pady=(10, 13))
        tk.Label(details, textvariable=self.selection_detail, bg=SURFACE, fg=MUTED, font=("Segoe UI", 10), wraplength=325, justify="left", anchor="nw").pack(fill="x", anchor="w", padx=20)
        self.install_btn = self.button(details, "Install Selected", self.install_selected, "Accent.TButton")
        self.install_btn.pack(fill="x", padx=20, pady=(22, 6))
        self.remove_btn = self.button(details, "Remove Downloaded", self.delete_selected, "Danger.TButton")
        self.remove_btn.pack(fill="x", padx=20, pady=6)
        self.unload_btn = self.button(details, "Unload From Memory", self.unload_selected)
        self.unload_btn.pack(fill="x", padx=20, pady=6)
        self.models_folder_btn = self.button(details, "Open Models Folder", self.open_models_folder)
        self.models_folder_btn.pack(fill="x", padx=20, pady=6)

        info = tk.Frame(details, bg=SURFACE_2)
        info.pack(fill="x", padx=20, pady=(22, 0))
        self.label(info, "LOCAL-FIRST", 8, ACCENT, "bold").pack(anchor="w", padx=12, pady=(11, 3))
        self.label(info, "Pretrained models are downloaded and run locally. The desktop app does not train them.", 9, MUTED, wraplength=300, justify="left").pack(anchor="w", padx=12, pady=(0, 11))

        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", padx=34, pady=(0, 20))
        progress_top = tk.Frame(footer, bg=BG)
        progress_top.pack(fill="x")
        self.label(progress_top, None, 9, MUTED, textvariable=self.progress_var).pack(side="left")
        self.label(progress_top, "Local only • 127.0.0.1", 8, MUTED).pack(side="right")
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(7, 7))
        self.label(footer, "API  127.0.0.1:8000    •    Data  ~/.maintain-ai    •    Models  ~/.maintain-ai/models", 8, "#68737e").pack(anchor="w")
        self.update_buttons()

    def stat_card(self, parent, title, value):
        card = tk.Frame(parent, bg=SURFACE_2, width=105, height=66)
        card.pack_propagate(False)
        self.label(card, title, 7, MUTED, "bold").pack(anchor="w", padx=11, pady=(10, 0))
        value_label = self.label(card, value, 17, TEXT, "bold")
        value_label.pack(anchor="w", padx=11, pady=(2, 0))
        card.value_label = value_label
        return card

    def set_status(self, status, detail, color=ACCENT):
        self.status_var.set(status)
        self.detail_var.set(detail)
        self.status_label.configure(text=status, fg=TEXT)
        self.status_dot.configure(fg=color)
        self.update_buttons()

    def update_stats(self):
        count = len(self.models)
        installed = [m for m in self.models if m.get("installed")]
        storage_mb = sum(float(m.get("size_mb") or 0) for m in installed)
        self.models_stat.value_label.configure(text=str(count))
        if storage_mb >= 1024:
            self.storage_stat.value_label.configure(text=f"{storage_mb / 1024:.1f} GB")
        else:
            self.storage_stat.value_label.configure(text=f"{storage_mb:.0f} MB" if storage_mb else "—")

    def update_buttons(self):
        running = bool(self.engine and self.engine.is_alive())
        selected = bool(self.tree.selection()) if hasattr(self, "tree") else False
        selected_models = self.selected_models() if selected else []
        downloadable_selected = any(m.get("downloadable") and not m.get("installed") for m in selected_models)
        removable_selected = any(m.get("downloadable") and m.get("installed") for m in selected_models)
        self.start_btn.configure(state="disabled" if running or self.busy else "normal")
        self.stop_btn.configure(state="normal" if running and not self.busy else "disabled")
        self.refresh_btn.configure(state="disabled" if self.busy else "normal")
        self.download_all_btn.configure(state="disabled" if self.busy or not running else "normal")
        self.install_btn.configure(state="normal" if running and downloadable_selected and not self.busy else "disabled")
        self.remove_btn.configure(state="normal" if running and removable_selected and not self.busy else "disabled")
        self.unload_btn.configure(state="normal" if running and selected and not self.busy else "disabled")

    def start(self):
        if self.engine and self.engine.is_alive():
            self.refresh()
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex((HOST, PORT)) == 0:
                    self.set_status("Port in use", f"{HOST}:{PORT} is already occupied.", DANGER)
                    return
            self.busy = True
            self.update_buttons()
            self.set_status("Starting", "Launching local inference API…", BLUE)
            # Packaged builds do not need Uvicorn's console logging configuration.
            # Disabling it avoids PyInstaller formatter lookup failures such as
            # "ValueError: Unable to configure formatter 'default'".
            config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning", access_log=False, log_config=None)
            self.engine = uvicorn.Server(config)
            threading.Thread(target=self.run_engine, daemon=True, name="maintain-api").start()
            threading.Thread(target=self.wait_ready, daemon=True, name="maintain-api-health").start()
        except Exception as exc:
            self.engine = None
            self.busy = False
            self.set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER)
            messagebox.showerror("MAINTAIN AI", f"Local engine could not start.\n\n{exc}")

    def run_engine(self):
        try:
            self.engine.run()
        except Exception as exc:
            self.after(0, lambda e=exc: self.engine_failed(e))

    def engine_failed(self, exc):
        self.engine = None
        self.busy = False
        self.set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER)
        self.update_buttons()

    def wait_ready(self):
        last = None
        for _ in range(80):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1) as response:
                    if response.status == 200:
                        self.after(0, self.engine_ready)
                        return
            except Exception as exc:
                last = exc
                time.sleep(0.25)
        detail = "The local API did not become ready."
        if last:
            detail += f" {type(last).__name__}: {last}"
        self.after(0, lambda d=detail: self.engine_failed(RuntimeError(d)))

    def engine_ready(self):
        self.busy = False
        self.set_status("Running", "Local API ready • loading model library", ACCENT)
        self.progress_var.set("Engine ready")
        self.refresh()

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="indeterminate")
        self.progress_var.set("Engine stopped")
        self.models = []
        self.active_model = None
        self.tree.delete(*self.tree.get_children())
        self.update_stats()
        self.set_status("Stopped", "Local inference engine is not running", MUTED)
        self.selection_var.set("No model selected")
        self.selection_detail.set("Start the engine to load the local model library.")
        self.state_pill.configure(text="NOT SELECTED", bg=SURFACE_3, fg=MUTED)
        self.update_buttons()

    def refresh(self):
        if not (self.engine and self.engine.is_alive()):
            self.set_status("Stopped", "Start the local engine to load the model library", MUTED)
            return []
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=5) as response:
                data = json.load(response)
            self.models = data.get("models", [])
            self.render_models()
            self.update_stats()
            self.set_status("Running", f"Local API ready • {len(self.models)} models available", ACCENT)
            return self.models
        except Exception as exc:
            self.set_status("API error", f"Could not read model library: {type(exc).__name__}: {exc}", DANGER)
            return []

    def render_models(self):
        if not hasattr(self, "tree"):
            return
        query = self.search_var.get().strip().lower()
        selected_names = {self.tree.item(item, "values")[0] for item in self.tree.selection() if self.tree.exists(item)}
        self.tree.delete(*self.tree.get_children())
        for model in self.models:
            name = model.get("name", "")
            haystack = " ".join(str(model.get(key, "")) for key in ("name", "kind", "source_label", "description")).lower()
            if query and query not in haystack:
                continue
            installed = bool(model.get("installed"))
            downloadable = bool(model.get("downloadable"))
            state = "READY" if installed and downloadable else ("BUILT-IN" if installed else "NOT INSTALLED")
            size = f"{model.get('size_mb', 0):g} MB" if installed else "—"
            iid = name.replace(" ", "_").replace("/", "_")
            self.tree.insert("", "end", iid=iid, values=(name, model.get("kind", ""), state, size, model.get("source_label", "Local")))
            if name in selected_names:
                self.tree.selection_add(iid)
        self.on_selection()

    def on_selection(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.selection_var.set("No model selected")
            self.selection_detail.set("Select a model to see capabilities, storage and dependencies.")
            self.state_pill.configure(text="NOT SELECTED", bg=SURFACE_3, fg=MUTED)
            self.update_buttons()
            return
        names = [self.tree.item(item, "values")[0] for item in selected]
        if len(names) == 1:
            model = next((m for m in self.models if m.get("name") == names[0]), None)
            self.selection_var.set(names[0])
            if model:
                installed = bool(model.get("installed"))
                downloadable = bool(model.get("downloadable"))
                if installed and downloadable:
                    state, pill_bg, pill_fg = "READY", ACCENT_SOFT, ACCENT
                elif installed:
                    state, pill_bg, pill_fg = "BUILT-IN", BLUE_SOFT, BLUE
                else:
                    state, pill_bg, pill_fg = "NOT INSTALLED", SURFACE_3, MUTED
                self.state_pill.configure(text=state, bg=pill_bg, fg=pill_fg)
                size = f"{model.get('size_mb', 0):g} MB locally" if installed else "Not downloaded"
                self.selection_detail.set(f"{model.get('description', '')}\n\nState: {state}\nStorage: {size}\nSource: {model.get('source_label', 'Local')}\nDependencies: {model.get('dependencies', '—')}")
        else:
            self.selection_var.set(f"{len(names)} models selected")
            self.state_pill.configure(text="MULTI-SELECT", bg=BLUE_SOFT, fg=BLUE)
            self.selection_detail.set("Install Selected downloads missing downloadable models. Remove Selected deletes installed downloadable models. Built-in adapters are never deleted.")
        self.update_buttons()

    def selected_models(self):
        if not hasattr(self, "tree"):
            return []
        names = [self.tree.item(item, "values")[0] for item in self.tree.selection()]
        return [model for model in self.models if model.get("name") in names]

    def post_json(self, url):
        with urlopen(Request(url, method="POST"), timeout=10) as response:
            return json.load(response)

    def install_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and not m.get("installed")]
        if not models:
            messagebox.showinfo("Model Library", "Select a missing downloadable model first.")
            return
        names = "\n".join(f"• {m.get('name', 'model')}" for m in models)
        if messagebox.askyesno("Install Models", f"Download these models to local storage?\n\n{names}"):
            self.download_queue(models)

    def download_all(self):
        models = [m for m in self.models if m.get("downloadable") and not m.get("installed")]
        if not models:
            messagebox.showinfo("Model Library", "There are no missing downloadable models.")
            return
        if messagebox.askyesno("Download All", f"Download {len(models)} missing model(s) to local storage?"):
            self.download_queue(models)

    def download_queue(self, models):
        if self.busy:
            return
        self.busy = True
        self.update_buttons()
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        self.progress_var.set("Preparing model downloads…")
        threading.Thread(target=self.download_worker, args=(list(models),), daemon=True, name="maintain-model-downloads").start()

    def download_worker(self, models):
        failures = []
        total = len(models)
        for index, model in enumerate(models, 1):
            name = model.get("name", "model")
            try:
                self.after(0, lambda n=name, i=index: self.progress_var.set(f"Downloading {n}  •  {i}/{total}"))
                result = self.post_json(f"http://{HOST}:{PORT}/api/model-manager/{name}/download")
                job_id = result.get("job_id")
                if job_id:
                    self.wait_download_job(job_id, name, index, total)
                elif result.get("state") == "error":
                    raise RuntimeError(result.get("message", "Download failed"))
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
        self.after(0, lambda: self.download_finished(failures))

    def wait_download_job(self, job_id, name, index, total):
        while True:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager/jobs/{job_id}", timeout=5) as response:
                job = json.load(response)
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

    def download_finished(self, failures):
        self.progress.stop()
        self.progress.configure(mode="indeterminate")
        self.busy = False
        if failures:
            self.progress_var.set("Downloads finished with errors")
            messagebox.showerror("Model Installation", "Some models could not be installed:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Model installation complete")
            messagebox.showinfo("Model Installation", "The selected models are now stored locally.")
        self.refresh()
        self.update_buttons()

    def delete_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and m.get("installed")]
        if not models:
            messagebox.showinfo("Model Library", "Select an installed downloadable model to remove.")
            return
        names = "\n".join(f"• {m.get('name', 'model')}" for m in models)
        if not messagebox.askyesno("Remove Models", f"Delete these downloaded model files?\n\n{names}\n\nThis does not affect built-in adapters."):
            return
        failures = []
        for model in models:
            name = model.get("name")
            try:
                with urlopen(Request(f"http://{HOST}:{PORT}/api/model-manager/{name}", method="DELETE"), timeout=10) as response:
                    json.load(response)
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
        if failures:
            messagebox.showerror("Remove Models", "Some models could not be removed:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Selected model files removed")
        self.refresh()

    def unload_selected(self):
        models = self.selected_models()
        if not models:
            messagebox.showinfo("Memory", "Select a model first.")
            return
        failures = []
        unloaded = 0
        for model in models:
            name = model.get("name")
            try:
                with urlopen(Request(f"http://{HOST}:{PORT}/api/model-manager/{name}/unload", method="POST"), timeout=10) as response:
                    result = json.load(response)
                if result.get("unloaded"):
                    unloaded += 1
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
        if failures:
            messagebox.showerror("Unload Models", "Some models could not be unloaded:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set(f"Memory released • {unloaded} model cache(s) cleared")

    def open_docs(self):
        webbrowser.open(f"http://{HOST}:{PORT}/docs")

    def open_path(self, path):
        os.makedirs(path, exist_ok=True)
        if os.name == "nt":
            os.startfile(path)
        else:
            webbrowser.open(f"file://{path}")

    def open_data_folder(self):
        self.open_path(os.path.expanduser("~/.maintain-ai"))

    def open_models_folder(self):
        self.open_path(os.path.expanduser("~/.maintain-ai/models"))

    def diagnostics(self):
        checks = []
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=2) as response:
                checks.append(f"API health: OK  •  HTTP {response.status}")
        except Exception as exc:
            checks.append(f"API health: FAILED  •  {type(exc).__name__}: {exc}")
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=3) as response:
                data = json.load(response)
            checks.append(f"Model manager: OK  •  {len(data.get('models', []))} models")
        except Exception as exc:
            checks.append(f"Model manager: FAILED  •  {type(exc).__name__}: {exc}")
        checks.append(f"Engine: {'running' if self.engine and self.engine.is_alive() else 'stopped'}")
        checks.append(f"Data: {os.path.expanduser('~/.maintain-ai')}")
        checks.append(f"Models: {os.path.expanduser('~/.maintain-ai/models')}")
        checks.append(f"API bind: {HOST}:{PORT}")
        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def on_close(self):
        if self.engine:
            self.engine.should_exit = True
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
