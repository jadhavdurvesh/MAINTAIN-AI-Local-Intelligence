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
        self.busy = False
        self.status_var = tk.StringVar(value="Starting")
        self.detail_var = tk.StringVar(value="Preparing local inference API…")
        self.selection_var = tk.StringVar(value="No model selected")
        self.selection_detail = tk.StringVar(value="Select a model to view details.")
        self.progress_var = tk.StringVar(value="Idle")
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(250, self.start)

    def label(self, parent, text=None, size=10, color=TEXT, weight="normal", **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color, font=("Segoe UI", size, weight), **kwargs)

    def build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8), background=PANEL_2, foreground=TEXT)
        style.map("TButton", background=[("active", "#203142"), ("disabled", "#151d25")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=42, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, font=("Segoe UI", 9, "bold"), padding=10)
        style.map("Treeview", background=[("selected", "#183c37")], foreground=[("selected", "#ffffff")])
        style.configure("Horizontal.TProgressbar", troughcolor="#16212b", background=ACCENT)

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 12))
        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        self.label(left, "MAINTAIN AI", 28, TEXT, "bold").pack(anchor="w")
        self.label(left, "LOCAL INTELLIGENCE  •  EDGE INFERENCE  •  ASSET / WORKFORCE AI", 9, MUTED, "bold").pack(anchor="w", pady=(3, 0))
        status = tk.Frame(header, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        status.pack(side="right", ipadx=14, ipady=9)
        self.status_label = self.label(status, "● Starting", 11, ACCENT, "bold")
        self.status_label.pack(anchor="e")
        self.label(status, None, 9, MUTED, textvariable=self.detail_var).pack(anchor="e", pady=(2, 0))

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=30, pady=(0, 12))
        self.start_btn = ttk.Button(toolbar, text="Start Engine", command=self.start)
        self.start_btn.pack(side="left", padx=(0, 7))
        self.stop_btn = ttk.Button(toolbar, text="Stop", command=self.stop)
        self.stop_btn.pack(side="left", padx=7)
        ttk.Button(toolbar, text="Refresh Models", command=self.refresh).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Download All", command=self.download_all).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=7)
        ttk.Button(toolbar, text="API Docs", command=self.open_docs).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Data Folder", command=self.open_data_folder).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Diagnostics", command=self.diagnostics).pack(side="left", padx=7)

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=30)
        library = tk.Frame(content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        library.pack(side="left", fill="both", expand=True)
        title = tk.Frame(library, bg=PANEL)
        title.pack(fill="x", padx=18, pady=(16, 8))
        self.label(title, "LOCAL MODEL LIBRARY", 12, TEXT, "bold").pack(side="left")
        self.label(title, "Select a row to install, use, or remove a model", 9, MUTED).pack(side="right")
        wrap = tk.Frame(library, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        cols = ("name", "kind", "state", "size", "source")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="extended")
        for c, w in {"name": 190, "kind": 150, "state": 120, "size": 100, "source": 260}.items():
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection)
        self.tree.bind("<Double-1>", lambda _e: self.install_selected())

        details = tk.Frame(content, bg=PANEL, width=340, highlightbackground=BORDER, highlightthickness=1)
        details.pack(side="right", fill="y", padx=(14, 0))
        details.pack_propagate(False)
        self.label(details, "MODEL DETAILS", 12, TEXT, "bold").pack(anchor="w", padx=18, pady=(18, 4))
        self.label(details, "Selected", 9, MUTED, "bold").pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(details, textvariable=self.selection_var, bg=PANEL, fg=ACCENT, font=("Segoe UI", 16, "bold"), wraplength=295, justify="left").pack(anchor="w", padx=18)
        tk.Label(details, textvariable=self.selection_detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 10), wraplength=295, justify="left").pack(anchor="w", padx=18, pady=(8, 14))
        self.install_btn = ttk.Button(details, text="Install Selected", command=self.install_selected)
        self.install_btn.pack(fill="x", padx=18, pady=5)
        self.remove_btn = ttk.Button(details, text="Remove Selected", command=self.delete_selected)
        self.remove_btn.pack(fill="x", padx=18, pady=5)
        ttk.Button(details, text="Open Models Folder", command=self.open_models_folder).pack(fill="x", padx=18, pady=5)
        self.label(details, "LOCAL-FIRST", 9, MUTED, "bold").pack(anchor="w", padx=18, pady=(28, 5))
        self.label(details, "These models run on this computer. The desktop manager does not train models; it downloads and prepares pretrained models for local inference. Installed downloadable models can be removed at any time.", 9, MUTED, wraplength=295, justify="left").pack(anchor="w", padx=18)

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=30, pady=(10, 20))
        self.label(footer, None, 9, MUTED, textvariable=self.progress_var).pack(anchor="w", pady=(0, 5))
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x")
        self.label(footer, "Local API: http://127.0.0.1:8000   •   Data: ~/.maintain-ai   •   Models: ~/.maintain-ai/models", 8, MUTED).pack(anchor="w", pady=(7, 0))
        self.update_buttons()

    def set_status(self, status, detail, color=ACCENT):
        self.status_var.set(status)
        self.detail_var.set(detail)
        self.status_label.configure(text=f"● {status}", fg=color)
        self.update_buttons()

    def update_buttons(self):
        running = bool(self.engine and self.engine.is_alive())
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        selected = bool(self.tree.selection()) if hasattr(self, "tree") else False
        state = "normal" if running and selected and not self.busy else "disabled"
        self.install_btn.configure(state=state)
        self.remove_btn.configure(state=state)

    def start(self):
        if self.engine and self.engine.is_alive():
            self.refresh()
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((HOST, PORT)) == 0:
                    self.set_status("Port in use", f"{HOST}:{PORT} is already occupied.", DANGER)
                    return
            self.set_status("Starting", "Launching local inference API…", ACCENT_2)
            config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning")
            self.engine = uvicorn.Server(config)
            threading.Thread(target=self.run_engine, daemon=True).start()
            threading.Thread(target=self.wait_ready, daemon=True).start()
        except Exception as exc:
            self.engine = None
            self.set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER)
            messagebox.showerror("Local Engine", str(exc))

    def run_engine(self):
        try:
            self.engine.run()
        except Exception as exc:
            self.after(0, lambda: self.set_status("Start failed", f"{type(exc).__name__}: {exc}", DANGER))

    def wait_ready(self):
        last = None
        for _ in range(80):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1) as r:
                    if r.status == 200:
                        self.after(0, lambda: self.set_status("Running", "Local API ready • loading model library", ACCENT))
                        self.after(0, self.refresh)
                        return
            except Exception as exc:
                last = exc
                time.sleep(0.25)
        detail = "The local API did not become ready."
        if last:
            detail += f" {type(last).__name__}: {last}"
        self.after(0, lambda: self.set_status("Start failed", detail, DANGER))
        self.after(0, self.diagnostics)

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self.progress.stop()
        self.progress_var.set("Engine stopped")
        self.models = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.set_status("Stopped", "Local inference engine is not running", MUTED)

    def refresh(self):
        if not (self.engine and self.engine.is_alive()):
            self.set_status("Stopped", "Start the local engine to load the model library", MUTED)
            return []
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=5) as r:
                data = json.load(r)
            self.models = data.get("models", [])
            selected = {self.tree.item(i, "values")[0] for i in self.tree.selection() if self.tree.exists(i)}
            self.tree.delete(*self.tree.get_children())
            for m in self.models:
                installed = bool(m.get("installed"))
                downloadable = bool(m.get("downloadable"))
                state = "READY" if installed and downloadable else ("BUILT-IN" if installed else "NOT INSTALLED")
                size = f"{m.get('size_mb', 0):g} MB" if installed else "—"
                name = m.get("name", "")
                self.tree.insert("", "end", iid=name, values=(name, m.get("kind", ""), state, size, m.get("source_label", "")))
            for name in selected:
                if self.tree.exists(name):
                    self.tree.selection_add(name)
            self.on_selection()
            self.set_status("Running", f"Local API ready • {len(self.models)} models available", ACCENT)
            return self.models
        except Exception as exc:
            self.set_status("API error", f"Could not read model library: {type(exc).__name__}: {exc}", DANGER)
            return []

    def on_selection(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.selection_var.set("No model selected")
            self.selection_detail.set("Select one or more model rows. Choose Install Selected to download missing models.")
            self.update_buttons()
            return
        names = [self.tree.item(i, "values")[0] for i in selected]
        if len(names) == 1:
            m = next((x for x in self.models if x.get("name") == names[0]), None)
            self.selection_var.set(names[0])
            if m:
                state = "Built-in" if not m.get("downloadable") else ("Installed locally" if m.get("installed") else "Not installed")
                self.selection_detail.set(f"{m.get('description', '')}\n\nState: {state}\nSource: {m.get('source_label', 'Local')}\nDependencies: {m.get('dependencies', '—')}")
        else:
            self.selection_var.set(f"{len(names)} models selected")
            self.selection_detail.set("Install Selected will queue all downloadable, missing models. Built-in models are skipped.")
        self.update_buttons()

    def selected_models(self):
        names = [self.tree.item(i, "values")[0] for i in self.tree.selection()]
        return [m for m in self.models if m.get("name") in names]

    def post(self, url):
        with urlopen(Request(url, method="POST"), timeout=10) as r:
            return json.load(r)

    def install_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and not m.get("installed")]
        if not models:
            messagebox.showinfo("Model Library", "Select a missing downloadable model first.")
            return
        names = ", ".join(m.get("name", "model") for m in models)
        if messagebox.askyesno("Install Models", f"Download and install these local models?\n\n{names}"):
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
        self.progress.start(12)
        self.progress_var.set("Preparing downloads…")
        threading.Thread(target=self.download_worker, args=(list(models),), daemon=True).start()

    def download_worker(self, models):
        failures = []
        total = len(models)
        for i, m in enumerate(models, 1):
            name = m.get("name", "model")
            self.after(0, lambda n=name, i=i: self.progress_var.set(f"Downloading {n}… ({i}/{total})"))
            try:
                self.post(f"http://{HOST}:{PORT}/api/model-manager/{name}/download")
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
        self.after(0, lambda: self.download_finished(failures))

    def download_finished(self, failures):
        self.progress.stop()
        self.busy = False
        if failures:
            self.progress_var.set("Downloads finished with errors")
            messagebox.showerror("Model Installation", "Some models could not be installed:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Model installation complete")
            messagebox.showinfo("Model Installation", "Selected models are installed locally.")
        self.refresh()
        self.update_buttons()

    def delete_selected(self):
        models = [m for m in self.selected_models() if m.get("downloadable") and m.get("installed")]
        if not models:
            messagebox.showinfo("Model Library", "Select an installed downloadable model to remove.")
            return
        names = ", ".join(m.get("name", "model") for m in models)
        if not messagebox.askyesno("Remove Models", f"Remove these downloaded model files?\n\n{names}"):
            return
        failures = []
        for m in models:
            try:
                with urlopen(Request(f"http://{HOST}:{PORT}/api/model-manager/{m.get('name')}", method="DELETE"), timeout=10) as r:
                    json.load(r)
            except Exception as exc:
                failures.append(f"{m.get('name')}: {type(exc).__name__}: {exc}")
        if failures:
            messagebox.showerror("Remove Models", "Some models could not be removed:\n\n" + "\n".join(failures))
        else:
            self.progress_var.set("Selected model files removed")
        self.refresh()

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
            with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=2) as r:
                checks.append(f"API health: HTTP {r.status}")
        except Exception as exc:
            checks.append(f"API health: FAILED ({type(exc).__name__}: {exc})")
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=3) as r:
                data = json.load(r)
            checks.append(f"Model manager: OK ({len(data.get('models', []))} models)")
        except Exception as exc:
            checks.append(f"Model manager: FAILED ({type(exc).__name__}: {exc})")
        checks.append(f"Engine thread: {'running' if self.engine and self.engine.is_alive() else 'stopped'}")
        checks.append(f"Data directory: {os.path.expanduser('~/.maintain-ai')}")
        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def on_close(self):
        if self.engine:
            self.engine.should_exit = True
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
