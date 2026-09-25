import json
import os
import socket
import threading
import time
import traceback
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from urllib.request import urlopen

import uvicorn
from app.main import app as api_app

HOST = "127.0.0.1"
PORT = 8000


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("1120x760")
        self.minsize(960, 640)
        self.engine = None
        self.status = tk.StringVar(value="Stopped")
        self.detail = tk.StringVar(value="Local inference engine is not running.")
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build(self):
        style = ttk.Style()
        style.configure("TButton", padding=8)
        style.configure("Treeview", rowheight=32)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=28, pady=(24, 4))
        ttk.Label(header, text="MAINTAIN AI", font=("Segoe UI", 25, "bold")).pack()
        ttk.Label(header, text="Local Intelligence / Edge Inference", font=("Segoe UI", 12)).pack(pady=(2, 0))
        ttk.Label(header, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(pady=(12, 2))
        ttk.Label(header, textvariable=self.detail, wraplength=1000).pack()

        bar = ttk.Frame(self)
        bar.pack(pady=14)
        self.start_button = ttk.Button(bar, text="Start Local Engine", command=self.start)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = ttk.Button(bar, text="Stop", command=self.stop)
        self.stop_button.grid(row=0, column=1, padx=5)
        ttk.Button(bar, text="Refresh Models", command=self.refresh).grid(row=0, column=2, padx=5)
        ttk.Button(bar, text="Open API Docs", command=self.open_docs).grid(row=0, column=3, padx=5)
        ttk.Button(bar, text="Open Data Folder", command=self.open_data_folder).grid(row=0, column=4, padx=5)
        ttk.Button(bar, text="Diagnostics", command=self.diagnostics).grid(row=0, column=5, padx=5)

        columns = ("name", "kind", "available", "detail")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for c, w in (("name", 190), ("kind", 190), ("available", 120), ("detail", 520)):
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=28, pady=18)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=28, pady=(0, 16))
        ttk.Label(
            footer,
            text="Local engine: http://127.0.0.1:8000  •  Models are optional and are loaded only when configured.",
        ).pack(side="left")

        self.refresh_button_state()

    def refresh_button_state(self):
        running = bool(self.engine and self.engine.is_alive())
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")

    def _set_status(self, status, detail=None):
        self.status.set(status)
        if detail is not None:
            self.detail.set(detail)
        self.refresh_button_state()

    def start(self):
        if self.engine and self.engine.is_alive():
            self._set_status("Running", "Local API is ready on http://127.0.0.1:8000")
            self.refresh()
            return

        # Give the user a useful message if another process already owns port 8000.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, PORT)) == 0:
                self._set_status("Port already in use", f"{HOST}:{PORT} is already occupied. Use Diagnostics to inspect it.")
                self.refresh()
                return

        try:
            config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning")
            self.engine = uvicorn.Server(config)
            threading.Thread(target=self._run_engine, daemon=True, name="maintain-ai-engine").start()
            self._set_status("Starting…", "Starting the local FastAPI inference service. Please wait a moment.")
            threading.Thread(target=self._wait_ready, daemon=True, name="maintain-ai-readiness").start()
        except Exception as exc:
            self.engine = None
            self._set_status("Failed to start", f"{type(exc).__name__}: {exc}")
            messagebox.showerror("MAINTAIN AI — Local Engine", traceback.format_exc())

    def _run_engine(self):
        try:
            self.engine.run()
        except Exception as exc:
            self.after(0, lambda: self._set_status("Failed to start", f"{type(exc).__name__}: {exc}"))
            self.after(0, lambda: messagebox.showerror("Local Engine Error", traceback.format_exc()))

    def _wait_ready(self):
        last_error = None
        for _ in range(60):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1) as response:
                    if response.status == 200:
                        self.after(0, lambda: self._set_status("Running", "Local API is ready. Refreshing model availability…"))
                        self.after(0, self.refresh)
                        return
            except Exception as exc:
                last_error = exc
                time.sleep(0.25)

        detail = "The local engine did not become ready."
        if last_error:
            detail += f" Last error: {type(last_error).__name__}: {last_error}"
        self.after(0, lambda: self._set_status("Failed to start", detail))
        self.after(0, self.diagnostics)

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self._set_status("Stopped", "Local inference engine is not running.")

    def refresh(self):
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=5) as r:
                data = json.load(r)
            for item in self.tree.get_children():
                self.tree.delete(item)
            models = data.get("models", [])
            for model in models:
                available = bool(model.get("available"))
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        model.get("name", ""),
                        model.get("kind", ""),
                        "Ready" if available else "Optional / Not installed",
                        model.get("detail", ""),
                    ),
                )
            if self.engine and self.engine.is_alive():
                self._set_status("Running", f"Local API ready • {len(models)} model adapters detected")
            return models
        except Exception as exc:
            self._set_status("Engine not running", f"Could not read model status: {type(exc).__name__}: {exc}")
            return []

    def diagnostics(self):
        checks = []
        # Port check
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            port_open = sock.connect_ex((HOST, PORT)) == 0
        checks.append(f"API port {HOST}:{PORT}: {'OPEN' if port_open else 'not listening'}")

        # Health check
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=2) as r:
                checks.append(f"Health endpoint: HTTP {r.status}")
        except Exception as exc:
            checks.append(f"Health endpoint: FAILED ({type(exc).__name__}: {exc})")

        # Model manager check
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager", timeout=3) as r:
                data = json.load(r)
            models = data.get("models", [])
            ready = sum(1 for m in models if m.get("available"))
            checks.append(f"Model manager: OK ({ready}/{len(models)} adapters ready)")
        except Exception as exc:
            checks.append(f"Model manager: FAILED ({type(exc).__name__}: {exc})")

        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def open_docs(self):
        if not (self.engine and self.engine.is_alive()):
            self.start()
            self.after(1200, self.open_docs)
            return
        webbrowser.open(f"http://{HOST}:{PORT}/docs")

    def open_data_folder(self):
        folder = os.path.join(os.path.expanduser("~"), ".maintain-ai")
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def on_close(self):
        self.stop()
        self.destroy()


if __name__ == "__main__":
    ui = App()
    ui.mainloop()
