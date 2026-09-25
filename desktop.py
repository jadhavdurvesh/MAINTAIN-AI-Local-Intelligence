import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.request import urlopen

HOST = "127.0.0.1"
PORT = 8000

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("920x620")
        self.configure(bg="#0b1220")
        self.proc = None
        self.status = tk.StringVar(value="Stopped")
        self._build()

    def _build(self):
        ttk.Style().configure("TButton", padding=8)
        ttk.Style().configure("Treeview", rowheight=30)
        ttk.Label(self, text="MAINTAIN AI", font=("Segoe UI", 24, "bold")).pack(pady=(24, 2))
        ttk.Label(self, text="Local Intelligence / Edge Inference", font=("Segoe UI", 12)).pack()
        ttk.Label(self, textvariable=self.status, font=("Segoe UI", 11)).pack(pady=12)
        bar = ttk.Frame(self); bar.pack(pady=8)
        ttk.Button(bar, text="Start Local Engine", command=self.start).grid(row=0, column=0, padx=6)
        ttk.Button(bar, text="Stop", command=self.stop).grid(row=0, column=1, padx=6)
        ttk.Button(bar, text="Refresh Models", command=self.refresh).grid(row=0, column=2, padx=6)
        ttk.Button(bar, text="Open API Docs", command=lambda: os.startfile(f"http://{HOST}:{PORT}/docs")).grid(row=0, column=3, padx=6)
        self.tree = ttk.Treeview(self, columns=("kind", "available", "detail"), show="headings")
        for c, w in (("kind",180),("available",100),("detail",480)):
            self.tree.heading(c, text=c.title()); self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=28, pady=22)
        ttk.Label(self, text="The local engine binds to 127.0.0.1 and is not exposed publicly by default.").pack(pady=8)

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)]
        self.proc = subprocess.Popen(cmd, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.status.set("Starting…")
        threading.Thread(target=self._wait_ready, daemon=True).start()

    def _wait_ready(self):
        for _ in range(30):
            try:
                with urlopen(f"http://{HOST}:{PORT}/api/health", timeout=1):
                    self.after(0, lambda: self.status.set("Running")); self.refresh(); return
            except Exception:
                time.sleep(0.5)
        self.after(0, lambda: self.status.set("Failed to start"))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc = None
        self.status.set("Stopped")

    def refresh(self):
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/models", timeout=2) as r:
                data = json.load(r)
            for item in self.tree.get_children(): self.tree.delete(item)
            for m in data.get("models", []):
                self.tree.insert("", "end", values=(m["kind"], "Ready" if m["available"] else "Optional", m["detail"]))
        except Exception as exc:
            self.status.set("Engine not running")

    def on_close(self):
        self.stop(); self.destroy()

if __name__ == "__main__":
    app = App(); app.protocol("WM_DELETE_WINDOW", app.on_close); app.mainloop()
