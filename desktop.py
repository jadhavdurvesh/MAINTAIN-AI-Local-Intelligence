import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk
from urllib.request import urlopen

import uvicorn
from app.main import app as api_app

HOST = "127.0.0.1"
PORT = 8000

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("920x620")
        self.engine = None
        self.status = tk.StringVar(value="Stopped")
        self._build()

    def _build(self):
        style = ttk.Style()
        style.configure("TButton", padding=8)
        style.configure("Treeview", rowheight=30)
        ttk.Label(self, text="MAINTAIN AI", font=("Segoe UI", 24, "bold")).pack(pady=(24, 2))
        ttk.Label(self, text="Local Intelligence / Edge Inference", font=("Segoe UI", 12)).pack()
        ttk.Label(self, textvariable=self.status, font=("Segoe UI", 11)).pack(pady=12)
        bar = ttk.Frame(self); bar.pack(pady=8)
        ttk.Button(bar, text="Start Local Engine", command=self.start).grid(row=0, column=0, padx=6)
        ttk.Button(bar, text="Stop", command=self.stop).grid(row=0, column=1, padx=6)
        ttk.Button(bar, text="Refresh Models", command=self.refresh).grid(row=0, column=2, padx=6)
        ttk.Button(bar, text="Open API Docs", command=self.open_docs).grid(row=0, column=3, padx=6)
        self.tree = ttk.Treeview(self, columns=("kind", "available", "detail"), show="headings")
        for c, w in (("kind",180),("available",100),("detail",480)):
            self.tree.heading(c, text=c.title()); self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=28, pady=22)
        ttk.Label(self, text="The local engine binds to 127.0.0.1 and is not exposed publicly by default.").pack(pady=8)

    def start(self):
        if self.engine and self.engine.is_alive():
            return
        config = uvicorn.Config(api_app, host=HOST, port=PORT, log_level="warning")
        self.engine = uvicorn.Server(config)
        threading.Thread(target=self.engine.run, daemon=True).start()
        self.status.set("Starting…")
        threading.Thread(target=self._wait_ready, daemon=True).start()

    def _wait_ready(self):
        for _ in range(40):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1):
                    self.after(0, lambda: self.status.set("Running")); self.refresh(); return
            except Exception:
                time.sleep(0.25)
        self.after(0, lambda: self.status.set("Failed to start"))

    def stop(self):
        if self.engine:
            self.engine.should_exit = True
            self.engine = None
        self.status.set("Stopped")

    def refresh(self):
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/models", timeout=2) as r:
                data = json.load(r)
            for item in self.tree.get_children(): self.tree.delete(item)
            for m in data.get("models", []):
                self.tree.insert("", "end", values=(m["kind"], "Ready" if m["available"] else "Optional", m["detail"]))
        except Exception:
            self.status.set("Engine not running")

    def open_docs(self):
        os.startfile(f"http://{HOST}:{PORT}/docs")

    def on_close(self):
        self.stop(); self.destroy()

if __name__ == "__main__":
    ui = App(); ui.protocol("WM_DELETE_WINDOW", ui.on_close); ui.mainloop()
