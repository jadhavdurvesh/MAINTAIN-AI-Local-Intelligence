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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAINTAIN AI — Local Intelligence")
        self.geometry("1280x800")
        self.minsize(1050, 700)
        self.engine = None
        self.status = tk.StringVar(value="Stopped")
        self.detail = tk.StringVar(value="Local inference engine is not running.")
        self.models = []
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build(self):
        style = ttk.Style()
        style.configure("TButton", padding=7)
        style.configure("Treeview", rowheight=34)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=28, pady=(22, 4))
        ttk.Label(header, text="MAINTAIN AI", font=("Segoe UI", 25, "bold")).pack()
        ttk.Label(header, text="Local Intelligence / Edge Inference", font=("Segoe UI", 12)).pack(pady=(2, 0))
        ttk.Label(header, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(pady=(12, 2))
        ttk.Label(header, textvariable=self.detail, wraplength=1180).pack()

        bar = ttk.Frame(self)
        bar.pack(pady=12)
        self.start_button = ttk.Button(bar, text="Start Local Engine", command=self.start)
        self.start_button.grid(row=0, column=0, padx=4)
        self.stop_button = ttk.Button(bar, text="Stop", command=self.stop)
        self.stop_button.grid(row=0, column=1, padx=4)
        ttk.Button(bar, text="Refresh Models", command=self.refresh).grid(row=0, column=2, padx=4)
        ttk.Button(bar, text="Download Selected", command=self.download_selected).grid(row=0, column=3, padx=4)
        ttk.Button(bar, text="Download All", command=self.download_all).grid(row=0, column=4, padx=4)
        ttk.Button(bar, text="Delete Selected", command=self.delete_selected).grid(row=0, column=5, padx=4)
        ttk.Button(bar, text="Open API Docs", command=self.open_docs).grid(row=0, column=6, padx=4)
        ttk.Button(bar, text="Open Data Folder", command=self.open_data_folder).grid(row=0, column=7, padx=4)
        ttk.Button(bar, text="Diagnostics", command=self.diagnostics).grid(row=0, column=8, padx=4)

        columns = ("name", "kind", "state", "size", "source", "detail")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        widths = {"name": 190, "kind": 170, "state": 150, "size": 100, "source": 180, "detail": 470}
        for c in columns:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=28, pady=14)
        self.tree.bind("<Double-1>", lambda _e: self.download_selected())

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=28, pady=(0, 6))
        ttk.Label(self, text="Select a model and use Download Selected. Built-in adapters require no download; downloaded models can be removed with Delete Selected.").pack(anchor="w", padx=28, pady=(0, 10))
        ttk.Label(self, text="Local engine: http://127.0.0.1:8000  •  Data/models: ~/.maintain-ai").pack(anchor="w", padx=28, pady=(0, 16))

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
                        self.after(0, lambda: self._set_status("Running", "Local API is ready. Loading model manager…"))
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
            self.models = data.get("models", [])
            for item in self.tree.get_children():
                self.tree.delete(item)
            for model in self.models:
                installed = bool(model.get("installed"))
                state = "Installed" if installed else ("Built-in" if not model.get("downloadable") else "Not installed")
                size = f"{model.get('size_mb', 0)} MB" if installed else "—"
                source = model.get("source_label", "")
                self.tree.insert("", "end", iid=model.get("name"), values=(model.get("name", ""), model.get("kind", ""), state, size, source, model.get("description", "")))
            if self.engine and self.engine.is_alive():
                self._set_status("Running", f"Local API ready • {len(self.models)} model adapters available")
            return self.models
        except Exception as exc:
            self._set_status("Engine not running", f"Could not read model status: {type(exc).__name__}: {exc}")
            return []

    def _selected_name(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Model Manager", "Select a model first.")
            return None
        return self.tree.item(selected[0], "values")[0]

    def _post(self, url):
        request = Request(url, method="POST")
        with urlopen(request, timeout=10) as r:
            return json.load(r)

    def download_selected(self):
        name = self._selected_name()
        if not name:
            return
        model = next((m for m in self.models if m.get("name") == name), None)
        if not model or not model.get("downloadable"):
            messagebox.showinfo("Model Manager", f"{name} is built into MAINTAIN AI; no download is required.")
            return
        try:
            job = self._post(f"http://{HOST}:{PORT}/api/model-manager/{name}/download")
            job_id = job.get("job_id")
            self.progress.start(12)
            self._set_status("Downloading…", f"Downloading {name}. You can keep this window open while it completes.")
            self._poll_job(job_id, name)
        except Exception as exc:
            self.progress.stop()
            messagebox.showerror("Model Download", str(exc))

    def download_all(self):
        downloadable = [m for m in self.models if m.get("downloadable") and not m.get("installed")]
        if not downloadable:
            messagebox.showinfo("Model Manager", "All downloadable models are already installed. Built-in adapters need no download.")
            return
        self.progress.start(12)
        self._set_status("Downloading…", f"Starting {len(downloadable)} model downloads sequentially.")
        self._download_queue = [m["name"] for m in downloadable]
        self._download_next()

    def _download_next(self):
        if not getattr(self, "_download_queue", None):
            self.progress.stop()
            self.refresh()
            self._set_status("Running", "All requested model downloads completed.")
            return
        name = self._download_queue.pop(0)
        try:
            job = self._post(f"http://{HOST}:{PORT}/api/model-manager/{name}/download")
            self._poll_job(job.get("job_id"), name, queue_mode=True)
        except Exception as exc:
            self.progress.stop()
            messagebox.showerror("Model Download", f"{name}: {exc}")

    def _poll_job(self, job_id, name, queue_mode=False):
        if not job_id:
            self.progress.stop()
            return
        try:
            with urlopen(f"http://{HOST}:{PORT}/api/model-manager/jobs/{job_id}", timeout=5) as r:
                job = json.load(r)
            state = job.get("state")
            if state in {"queued", "running"}:
                self.detail.set(f"{name}: {job.get('message', 'working…')}")
                self.after(800, lambda: self._poll_job(job_id, name, queue_mode))
                return
            self.refresh()
            if state == "done":
                if queue_mode:
                    self.after(200, self._download_next)
                else:
                    self.progress.stop()
                    self._set_status("Running", f"{name} is installed and ready to load.")
            else:
                self.progress.stop()
                messagebox.showerror("Model Download", f"{name} failed: {job.get('message', 'unknown error')}")
        except Exception as exc:
            self.progress.stop()
            messagebox.showerror("Model Download", str(exc))

    def delete_selected(self):
        name = self._selected_name()
        if not name:
            return
        model = next((m for m in self.models if m.get("name") == name), None)
        if not model or not model.get("downloadable"):
            messagebox.showinfo("Model Manager", f"{name} is built in and cannot be deleted.")
            return
        if not model.get("installed"):
            messagebox.showinfo("Model Manager", f"{name} is not installed.")
            return
        if not messagebox.askyesno("Delete local model", f"Delete the downloaded {name} model from this computer?\n\nThis does not delete the model online."):
            return
        try:
            self._delete(f"http://{HOST}:{PORT}/api/model-manager/{name}")
            self.refresh()
            self._set_status("Running", f"Deleted local copy of {name}.")
        except Exception as exc:
            messagebox.showerror("Delete Model", str(exc))

    def _delete(self, url):
        request = Request(url, method="DELETE")
        with urlopen(request, timeout=10) as r:
            return json.load(r)

    def diagnostics(self):
        checks = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            port_open = sock.connect_ex((HOST, PORT)) == 0
        checks.append(f"API port {HOST}:{PORT}: {'OPEN' if port_open else 'not listening'}")
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
            checks.append(f"Model manager: OK ({ready}/{len(models)} models installed/available)")
            checks.extend(f"- {m['name']}: {'installed' if m.get('installed') else 'not installed'}" for m in models)
        except Exception as exc:
            checks.append(f"Model manager: FAILED ({type(exc).__name__}: {exc})")
        messagebox.showinfo("MAINTAIN AI Diagnostics", "\n".join(checks))

    def open_docs(self):
        if not (self.engine and self.engine.is_alive()):
            self.start()
            self.after(1500, self.open_docs)
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
