import json
import os
import socket
import threading
import time
import traceback
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from urllib.request import Request, urlopen

import uvicorn
from app.main import app as api_app

HOST = "127.0.0.1"
PORT = 8000
BG = "#0b1117"
PANEL = "#111a23"
PANEL_2 = "#17222d"
BORDER = "#263544"
TEXT = "#e8eef5"
MUTED = "#8ea0b2"
ACCENT = "#31c48d"
ACCENT_2 = "#2f81f7"
DANGER = "#ef6262"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("1380x860")
        self.minsize(1120, 720)
        self.configure(bg=BG)
        self.engine = None
        self.models = []
        self._download_queue = []
        self._busy = False
        self.status = tk.StringVar(value="Starting local intelligence")
        self.detail = tk.StringVar(value="Preparing the local API…")
        self.selected_model = tk.StringVar(value="No model selected")
        self.selected_detail = tk.StringVar(value="Click a model row to select it.")
        self.progress_text = tk.StringVar(value="Idle")
        self._configure_styles()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(350, self.start)

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8), background=PANEL_2, foreground=TEXT, bordercolor=BORDER)
        style.map("TButton", background=[("active", "#203142"), ("disabled", "#151d25")], foreground=[("disabled", "#5e6b78")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=42, bordercolor=BORDER, relief="flat", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, font=("Segoe UI", 9, "bold"), padding=10)
        style.map("Treeview", background=[("selected", "#183c37")], foreground=[("selected", "#ffffff")])
        style.configure("Horizontal.TProgressbar", troughcolor="#16212b", background=ACCENT, bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)

    def _label(self, parent, text, size=10, color=TEXT, weight="normal", **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color, font=("Segoe UI", size, weight), **kwargs)

    def _build(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 12))
        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        self._label(left, "MAINTAIN AI", 27, TEXT, "bold").pack(anchor="w")
        self._label(left, "LOCAL INTELLIGENCE  •  EDGE INFERENCE  •  WORKFORCE / ASSET AI", 9, MUTED, "bold").pack(anchor="w", pady=(3, 0))
        status_box = tk.Frame(header, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        status_box.pack(side="right", ipadx=14, ipady=9)
        self.status_label = self._label(status_box, "●  Starting", 11, ACCENT, "bold")
        self.status_label.pack(anchor="e")
        self._label(status_box, textvariable=self.detail, 9, MUTED).pack(anchor="e", pady=(2, 0))

        # Toolbar
        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=30, pady=(0, 12))
        self.start_button = ttk.Button(toolbar, text="Start Engine", command=self.start)
        self.start_button.pack(side="left", padx=(0, 7))
        self.stop_button = ttk.Button(toolbar, text="Stop", command=self.stop)
        self.stop_button.pack(side="left", padx=7)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="left", padx=7)
        ttk.Button(toolbar, text="API Docs", command=self.open_docs).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Data Folder", command=self.open_data_folder).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Diagnostics", command=self.diagnostics).pack(side="left", padx=7)

        # Main content
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=30)

        # Model manager panel
        manager = tk.Frame(content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        manager.pack(side="left", fill="both", expand=True)
        title_row = tk.Frame(manager, bg=PANEL)
        title_row.pack(fill="x", padx=18, pady=(16, 8))
        self._label(title_row, "LOCAL MODEL LIBRARY", 12, TEXT, "bold").pack(side="left")
        self._label(title_row, "Select a row, then install or remove the local model", 9, MUTED).pack(side="right")

        table_wrap = tk.Frame(manager, bg=PANEL)
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        columns = ("name", "kind", "state", "size", "source")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", selectmode="extended")
        widths = {"name": 190, "kind": 160, "state": 120, "size": 100, "source": 260}
        for c in columns:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection)
        self.tree.bind("<Double-1>", lambda _e: self.install_selected())

        # Details panel
        details = tk.Frame(content, bg=PANEL, width=330, highlightbackground=BORDER, highlightthickness=1)
        details.pack(side="right", fill="y", padx=(14, 0))
        details.pack_propagate(False)
        self._label(details, "MODEL DETAILS", 12, TEXT, "bold").pack(anchor="w", padx=18, pady=(18, 4))
        self._label(details, "Selected", 9, MUTED, "bold").pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(details, textvariable=self.selected_model, bg=PANEL, fg=ACCENT, font=("Segoe UI", 16, "bold"), wraplength=285, justify="left").pack(anchor="w", padx=18)
        tk.Label(details, textvariable=self.selected_detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 10), wraplength=285, justify="left").pack(anchor="w", padx=18, pady=(8, 14))

        self.install_button = ttk.Button(details, text="Install Selected", command=self.install_selected)
        self.install_button.pack(fill="x", padx=18, pady=5)
        self.delete_button = ttk.Button(details, text="Remove Selected", command=self.delete_selected)
        self.delete_button.pack(fill="x", padx=18, pady=5)
        ttk.Button(details, text="Download All Models", command=self.download_all).pack(fill="x", padx=18, pady=5)
        ttk.Button(details, text="Open Model Folder", command=self.open_models_folder).pack(fill="x", padx=18, pady=5)

        self._label(details, "WHAT THIS MEANS", 9, MUTED, "bold").pack(anchor="w", padx=18, pady=(26, 5))
        self._label(details, "Built-in models are lightweight and already available. Downloadable models are stored locally and can be removed at any time.\n\nNo training is performed by this desktop manager; it prepares pretrained models for local inference.", 9, MUTED, wraplength=285, justify="left").pack(anchor="w", padx=18)

        # Bottom status / progress
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=30, pady=(10, 20))
        self._label(footer, textvariable=self.progress_text, 9, MUTED).pack(anchor="w", pady=(0, 5))
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x")
        self._label(footer, "Local API: http://127.0.0.1:8000    •    Local data: ~/.maintain-ai    •    Models: ~/.maintain-ai/models", 8, MUTED).pack(anchor="w", pady=(7, 0))
        self.refresh_button_state()

    def _set_status(self, status, detail=None, color=ACCENT):
        self.status.set(status)
        if detail is not None:
            self.detail.set(detail)
        self.status_label.configure(text=f"●  {status}", fg=color)
        self.refresh_button_state()

    def refresh_button_state(self):
        running = bool(self.engine and self.engine.is_alive())
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        has_selection = bool(self.tree.selection()) if hasattr(self, "tree") else False
        self.install_button.configure(state="normal" if running and has_selection and not self._busy else "disabled")
        self.delete_button.configure(state="normal" if running and has_selection and not self._busy else "disabled")

    def start(self):
        if self.engine and self.engine.is_alive():
            self._set_status("Running", "Local API is ready", ACCENT)
            self.refresh()
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, PORT)) == 0:
                self._set_status("Port in use", f"{HOST}:{PORT} is occupied by another process", DANGER)
                self.refresh()
                return
        try:
            config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning")
            self.engine = uvicorn.Server(config)
            threading.Thread(target=self._run_engine, daemon=True, name="maintain-ai-engine").start()
            self._set_status("Starting", "Launching the local inference API…", ACCENT_2)
            threading.Thread(target=self._wait_ready, daemon=True, name="maintain-ai-readiness").start()
        except Exception as exc:
            self.engine = None
            self._set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER)
            messagebox.showerror("Local Engine", traceback.format_exc())

    def _run_engine(self):
        try:
            self.engine.run()
        except Exception as exc:
            self.after(0, lambda: self._set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER))

    def _wait_ready(self):
        last_error = None
        for _ in range(80):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1) as response:
                    if response.status == 200:
                        self.after(0, lambda: self._set_status("Running", "Local API ready • loading model library", ACCENT))
                        self.after(0, self.refresh)
                        return
            except Exception as exc:
                last_error = exc
                time.sleep(0.25)
        detail = "The local API did not become ready."
        if last_error:
            detail += f" {type(last_error).__name__}: {last_error}"
        self.after(0, lambda: self._set_status("Start failed", detail, DANGER))
        self.after(0, self.diagnostics)

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self.progress.stop()
        self.progress_text.set("Engine stopped")
        self._set_status("Stopped", "Local inference engine is not running", MUTED)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.models = []
        self.refresh_button_state()

    def refresh(self):
        if not (self.engine and self.engine.is_alive()):
            self._set_status("Stopped", "Start the local engine to load the model library", MUTED)
            self.refresh_button_state()
            return []
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=5) as r:
                data = json.load(r)
            self.models = data.get("models", [])
            selected_names = {self.tree.item(i, "values")[0] for i in self.tree.selection() if self.tree.exists(i)}
            for item in self.tree.get_children():
                self.tree.delete(item)
            for model in self.models:
                installed = bool(model.get("installed"))
                state = "READY" if installed and model.get("downloadable") else ("BUILT-IN" if installed else "NOT INSTALLED")
                size = f"{model.get('size_mb', 0):g} MB" if installed else "—"
                self.tree.insert("", "end", iid=model.get("name"), values=(model.get("name", ""), model.get("kind", ""), state, size, model.get("source_label", "")))
            for name in selected_names:
                if self.tree.exists(name):
                    self.tree.selection_add(name)
            self._on_selection()
            self._set_status("Running", f"Local API ready • {len(self.models)} models available", ACCENT)
            return self.models
        except Exception as exc:
            self._set_status("API error", f"Could not read model library: {type(exc).__name__}: {exc}", DANGER)
            return []

    def _on_selection(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_model.set("No model selected")
            self.selected_detail.set("Select one or more model rows. Use Install Selected to download the highlighted model(s).")
            self.refresh_button_state()
            return
        names = [self.tree.item(i, "values")[0] for i in selected]
        if len(names) == 1:
            model = next((m for m in self.models if m.get("name") == names[0]), None)
            self.selected_model.set(names[0])
            if model:
                state = "Built-in" if not model.get("downloadable") else ("Installed locally" if model.get("installed") else "Not installed")
                self.selected_detail.set(f"{model.get('description', '')}\n\nState: {state}\nSource: {model.get('source_label', 'Local')}\nDependencies: {model.get('dependencies', '—')}")
        else:
            self.selected_model.set(f"{len(names)} models selected")
            self.selected_detail.set("Multiple models are selected. Install Selected will queue all downloadable, missing models. Built-in models are skipped.")
        self.refresh_button_state()

    def _selected_models(self):
        names = [self.tree.item(i, "values")[0] for i in self.tree.selection()]
        return [m for m in self.models if m.get("name") in names]

    def _post(self, url):
        request = Request(url, method="POST")
        with urlopen(request, timeout=10) as r:
            return json.load(r)

    def install_selected(self):
        models = self._selected_models()
        if not models:
            messagebox.showinfo("Model Library", "Select a model row first.")
            return
        downloadable = [m for m in models if m.get("downloadable") and not m.get("installed")]
        built_in = [m for m in models if not m.get("downloadable")]
        if not downloadable:
            messagebox.showinfo("Model Library", "The selected model is already available locally or is built in; no download is needed.")
            return
        self._busy = True
        self.refresh_button_state()
        self._download_queue = [m["name"] for m in downloadable]
        self.progress.start(10)
        self._download_next()

    def download_all(self):
        downloadable = [m for m in self.models if m.get("downloadable") and not m.get("installed")]
        if not downloadable:
            messagebox.showinfo("Model Library", "All downloadable models are already installed. Built-in models require no download.")
            return
        self._busy = True
        self.refresh_button_state()
        self._download_queue = [m["name"] for m in downloadable]
        self.progress.start(10)
        self._download_next()

    def _download_next(self):
        if not self._download_queue:
            self.progress.stop()
            self.progress_text.set("All requested downloads complete")
            self._busy = False
            self.refresh()
            self.refresh_button_state()
            return
        name = self._download_queue.pop(0)
        try:
            job = self._post(f"http://{HOST}:{PORT}/api/model-manager/{name}/download")
            job_id = job.get("job_id")
            self.progress_text.set(f"Downloading {name}…")
            self._poll_job(job_id, name)
        except Exception as exc:
            self._busy = False
            self.progress.stop()
            self.progress_text.set("Download failed")
            self.refresh_button_state()
            messagebox.showerror("Model Download", f"{name}\n\n{exc}")

    def _poll_job(self, job_id, name):
        if not job_id:
            self._download_next()
            return
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager/jobs/{job_id}", timeout=5) as r:
                job = json.load(r)
            state = job.get("state")
            self.detail.set(f"{name}: {job.get('message', 'working…')}")
            if state in {"queued", "running"}:
                self.progress_text.set(f"Downloading {name}… {job.get('message', 'working')}")
                self.after(700, lambda: self._poll_job(job_id, name))
                return
            if state == "done":
                self.progress_text.set(f"{name} installed")
                self.refresh()
                self.after(250, self._download_next)
                return
            self._busy = False
            self.progress.stop()
            self.progress_text.set(f"{name} download failed")
            self.refresh_button_state()
            messagebox.showerror("Model Download", f"{name} failed:\n\n{job.get('message', 'Unknown error')}")
        except Exception as exc:
            self._busy = False
            self.progress.stop()
            self.progress_text.set("Download status unavailable")
            self.refresh_button_state()
            messagebox.showerror("Model Download", str(exc))

    def delete_selected(self):
        models = self._selected_models()
        if not models:
            messagebox.showinfo("Model Library", "Select a model row first.")
            return
        downloadable = [m for m in models if m.get("downloadable") and m.get("installed")]
        if not downloadable:
            messagebox.showinfo("Model Library", "Built-in models cannot be removed, and no selected downloadable model is installed.")
            return
        names = ", ".join(m["name"] for m in downloadable)
        if not messagebox.askyesno("Remove local models", f"Remove these local model files?\n\n{names}\n\nThis only deletes the copy on this computer."):
            return
        errors = []
        for model in downloadable:
            try:
                self._delete(f"http://{HOST}:{PORT}/api/model-manager/{model['name']}")
            except Exception as exc:
                errors.append(f"{model['name']}: {exc}")
        self.refresh()
        self.progress_text.set("Selected local models removed" if not errors else "Some removals failed")
        if errors:
            messagebox.showerror("Remove Models", "\n".join(errors))

    def _delete(self, url):
        request = Request(url, method="DELETE")
        with urlopen(request, timeout=10) as r:
            return json.load(r)

    def diagnostics(self):
        if not (self.engine and self.engine.is_alive()):
            messagebox.showinfo("MAINTAIN AI Diagnostics", "Local engine is stopped.\n\nStart the engine first, then run Diagnostics again.")
            return
        checks = [f"API port {HOST}:{PORT}: listening"]
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=2) as r:
                checks.append(f"Health endpoint: HTTP {r.status}")
        except Exception as exc:
            checks.append(f"Health endpoint: FAILED ({type(exc).__name__}: {exc})")
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=3) as r:
                data = json.load(r)
            models = data.get("models", [])
            ready = sum(1 for m in models if m.get("installed"))
            checks.append(f"Model manager: OK ({ready}/{len(models)} ready)")
            for m in models:
                checks.append(f"  • {m['name']}: {'ready' if m.get('installed') else 'not installed'}")
        except Exception as exc:
            checks.append(f"Model manager: FAILED ({type(exc).__name__}: {exc})")
        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def open_docs(self):
        if not (self.engine and self.engine.is_alive()):
            self.start()
            self.after(1800, self.open_docs)
            return
        webbrowser.open(f"http://{HOST}:{PORT}/docs")

    def open_data_folder(self):
        folder = os.path.join(os.path.expanduser("~"), ".maintain-ai")
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def open_models_folder(self):
        folder = os.path.join(os.path.expanduser("~"), ".maintain-ai", "models")
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def on_close(self):
        if self.engine:
            self.engine.should_exit = True
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
