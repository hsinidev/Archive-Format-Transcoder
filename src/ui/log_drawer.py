import time
import customtkinter as ctk
from tkinter import filedialog

class TelemetryLogDrawer(ctk.CTkFrame):
    """
    Collapsible Telemetry Console & Execution Log Drawer.
    Displays timestamped event logs, throughput telemetry, and checksum statuses.
    """
    def __init__(self, parent, height: int = 150):
        super().__init__(parent, fg_color="#121620", border_color="#273044", border_width=1, corner_radius=8)
        self.is_expanded = True
        self.drawer_height = height

        # Header bar
        self.header_frame = ctk.CTkFrame(self, fg_color="#1B202E", height=32, corner_radius=6)
        self.header_frame.pack(fill="x", padx=4, pady=4)

        self.title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="⚡ Telemetry Execution Console Log",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFAB00"
        )
        self.title_lbl.pack(side="left", padx=10)

        # Right control buttons
        self.clear_btn = ctk.CTkButton(
            self.header_frame,
            text="Clear Log",
            fg_color="transparent",
            hover_color="#273044",
            text_color="#8B96A5",
            width=70,
            height=22,
            font=ctk.CTkFont(size=11),
            command=self.clear_logs
        )
        self.clear_btn.pack(side="right", padx=5)

        self.export_btn = ctk.CTkButton(
            self.header_frame,
            text="Export Log...",
            fg_color="transparent",
            hover_color="#273044",
            text_color="#00E5FF",
            width=80,
            height=22,
            font=ctk.CTkFont(size=11),
            command=self.export_logs
        )
        self.export_btn.pack(side="right", padx=5)

        self.toggle_btn = ctk.CTkButton(
            self.header_frame,
            text="▼ Collapse",
            fg_color="transparent",
            hover_color="#273044",
            text_color="#8B96A5",
            width=70,
            height=22,
            font=ctk.CTkFont(size=11),
            command=self.toggle_drawer
        )
        self.toggle_btn.pack(side="right", padx=5)

        # Text console box
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color="#0A0C10",
            text_color="#F0F4F8",
            font=ctk.CTkFont(family="Cascadia Code", size=11),
            border_color="#273044",
            border_width=1,
            height=height
        )
        self.textbox.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Initial timestamp line
        self.log_info("Archive Transcoder Pro v1.0.0-PROD initialized.")
        self.log_info("Zero-residual streaming telemetry engine online.")

    def toggle_drawer(self):
        if self.is_expanded:
            self.textbox.pack_forget()
            self.toggle_btn.configure(text="▲ Expand")
            self.is_expanded = False
        else:
            self.textbox.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            self.toggle_btn.configure(text="▼ Collapse")
            self.is_expanded = True

    def log(self, level: str, message: str):
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}] "
        line = f"{prefix}{message}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def log_info(self, message: str):
        self.log("INFO", message)

    def log_success(self, message: str):
        self.log("SUCCESS", message)

    def log_warning(self, message: str):
        self.log("WARN", message)

    def log_error(self, message: str):
        self.log("ERROR", message)

    def clear_logs(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self.log_info("Log console cleared.")

    def export_logs(self):
        log_content = self.textbox.get("1.0", "end")
        file_path = filedialog.asksaveasfilename(
            title="Export Telemetry Log",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                self.log_success(f"Log exported to {file_path}")
            except Exception as e:
                self.log_error(f"Failed to export log: {str(e)}")
