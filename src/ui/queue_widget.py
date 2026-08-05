import os
import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional

class QueueItemWidget(ctk.CTkFrame):
    """
    Individual card element inside the batch queue table.
    """
    def __init__(self, parent, task_data: Dict[str, Any], on_password_click: Callable, on_delete_click: Callable):
        super().__init__(parent, fg_color="#1B202E", border_color="#273044", border_width=1, corner_radius=6)
        self.task_data = task_data
        self.on_password_click = on_password_click
        self.on_delete_click = on_delete_click

        filename = os.path.basename(task_data["input_path"])
        file_size_mb = os.path.getsize(task_data["input_path"]) / (1024 * 1024) if os.path.exists(task_data["input_path"]) else 0.0

        # Row Layout
        # Left: File Info & Badge
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x")

        name_lbl = ctk.CTkLabel(
            top_row,
            text=filename,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#F0F4F8",
            anchor="w"
        )
        name_lbl.pack(side="left")

        # Source Format Badge
        self.fmt_badge = ctk.CTkLabel(
            top_row,
            text=task_data["source_format"],
            font=ctk.CTkFont(family="Cascadia Code", size=10, weight="bold"),
            text_color="#00E5FF",
            fg_color="#121620",
            corner_radius=4,
            width=50,
            height=18
        )
        self.fmt_badge.pack(side="left", padx=8)

        # Arrow & Target Format
        self.target_lbl = ctk.CTkLabel(
            top_row,
            text=f"➔ {task_data['target_format']}",
            font=ctk.CTkFont(family="Cascadia Code", size=10, weight="bold"),
            text_color="#FFAB00"
        )
        self.target_lbl.pack(side="left")

        # Sub row size & status
        self.sub_lbl = ctk.CTkLabel(
            info_frame,
            text=f"{file_size_mb:.2f} MB | Ready for stream conversion",
            font=ctk.CTkFont(size=10),
            text_color="#8B96A5",
            anchor="w"
        )
        self.sub_lbl.pack(fill="x", pady=(2, 0))

        # Item Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            info_frame,
            height=6,
            fg_color="#121620",
            progress_color="#FFAB00"
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", pady=(6, 2))

        # Right: Status Badge & Buttons
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=10, pady=8)

        self.status_badge = ctk.CTkLabel(
            right_frame,
            text="PENDING",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#8B96A5",
            fg_color="#121620",
            corner_radius=4,
            width=80,
            height=22
        )
        self.status_badge.pack(side="top", pady=(0, 4))

        btn_row = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_row.pack(side="bottom")

        self.pass_btn = ctk.CTkButton(
            btn_row,
            text="🔑 Password",
            fg_color="#273044",
            hover_color="#37435F",
            text_color="#F0F4F8",
            width=75,
            height=22,
            font=ctk.CTkFont(size=10),
            command=lambda: self.on_password_click(self.task_data["task_id"])
        )
        self.pass_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            btn_row,
            text="✕",
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#8B96A5",
            width=24,
            height=22,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_delete_click(self.task_data["task_id"])
        )
        del_btn.pack(side="left", padx=2)

    def update_status(self, state: str):
        color_map = {
            "PENDING": ("#8B96A5", "#121620"),
            "PROCESSING": ("#00E5FF", "#121620"),
            "COMPLETED": ("#10B981", "#121620"),
            "FAILED": ("#EF4444", "#121620")
        }
        fg, bg = color_map.get(state, ("#8B96A5", "#121620"))
        self.status_badge.configure(text=state, text_color=fg, fg_color=bg)

    def update_progress(self, pct: float, current_entry: Optional[str] = None):
        self.progress_bar.set(pct / 100.0)
        if current_entry:
            short_entry = current_entry if len(current_entry) < 35 else "..." + current_entry[-32:]
            self.sub_lbl.configure(text=f"Streaming: {short_entry} ({pct:.1f}%)")

    def set_completed_stats(self, stats: Dict[str, Any]):
        out_mb = stats.get("output_size_bytes", 0) / (1024 * 1024)
        ratio = stats.get("compression_ratio_pct", 0)
        time_sec = stats.get("elapsed_seconds", 0)
        self.sub_lbl.configure(text=f"✔ Transcoded to {out_mb:.2f} MB ({ratio}% compressed in {time_sec}s)")
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color="#10B981")


class BatchQueueWidget(ctk.CTkFrame):
    """
    Queue table container widget supporting Drag & Drop drops and item controls.
    """
    def __init__(self, parent, on_password_req_cb: Callable, on_queue_change_cb: Callable):
        super().__init__(parent, fg_color="#121620", border_color="#273044", border_width=1, corner_radius=8)
        self.on_password_req_cb = on_password_req_cb
        self.on_queue_change_cb = on_queue_change_cb

        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.item_widgets: Dict[str, QueueItemWidget] = {}

        # Header Bar
        hdr_frame = ctk.CTkFrame(self, fg_color="#1B202E", height=36, corner_radius=6)
        hdr_frame.pack(fill="x", padx=8, pady=8)

        hdr_lbl = ctk.CTkLabel(
            hdr_frame,
            text="📁 Archive Conversion Queue",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F0F4F8"
        )
        hdr_lbl.pack(side="left", padx=10)

        self.count_lbl = ctk.CTkLabel(
            hdr_frame,
            text="0 Archives Queued",
            font=ctk.CTkFont(size=11),
            text_color="#8B96A5"
        )
        self.count_lbl.pack(side="left", padx=10)

        clear_all_btn = ctk.CTkButton(
            hdr_frame,
            text="Clear Queue",
            fg_color="transparent",
            hover_color="#273044",
            text_color="#EF4444",
            width=80,
            height=24,
            font=ctk.CTkFont(size=11),
            command=self.clear_queue
        )
        clear_all_btn.pack(side="right", padx=5)

        # Drop Zone / Queue scroll container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Empty queue placeholder prompt
        self.placeholder = ctk.CTkLabel(
            self.scroll_frame,
            text="Drag & Drop Archives Here (.zip, .7z, .rar, .tar.gz, .tar.xz)\nor click sidebar settings to begin batch stream transcoding",
            font=ctk.CTkFont(size=12),
            text_color="#8B96A5",
            justify="center"
        )
        self.placeholder.pack(expand=True, pady=60)

    def add_archive_file(self, file_path: str, target_format: str, source_format: str) -> str:
        task_id = f"task_{len(self.tasks) + 1}_{int(os.path.basename(file_path).__hash__() & 0xffff)}"
        task_data = {
            "task_id": task_id,
            "input_path": file_path,
            "target_format": target_format,
            "source_format": source_format,
            "password": None
        }

        self.placeholder.pack_forget()
        self.tasks[task_id] = task_data

        widget = QueueItemWidget(
            self.scroll_frame,
            task_data=task_data,
            on_password_click=self._on_item_password,
            on_delete_click=self.remove_task
        )
        widget.pack(fill="x", pady=4)
        self.item_widgets[task_id] = widget

        self._update_counter()
        self.on_queue_change_cb()
        return task_id

    def remove_task(self, task_id: str):
        if task_id in self.item_widgets:
            self.item_widgets[task_id].pack_forget()
            del self.item_widgets[task_id]
        if task_id in self.tasks:
            del self.tasks[task_id]

        if not self.tasks:
            self.placeholder.pack(expand=True, pady=60)

        self._update_counter()
        self.on_queue_change_cb()

    def clear_queue(self):
        for widget in self.item_widgets.values():
            widget.pack_forget()
        self.item_widgets.clear()
        self.tasks.clear()
        self.placeholder.pack(expand=True, pady=60)
        self._update_counter()
        self.on_queue_change_cb()

    def update_task_target_format(self, target_format: str):
        for task_id, task_data in self.tasks.items():
            task_data["target_format"] = target_format
            if task_id in self.item_widgets:
                self.item_widgets[task_id].target_lbl.configure(text=f"➔ {target_format}")

    def update_task_password(self, task_id: str, password: str):
        if task_id in self.tasks:
            self.tasks[task_id]["password"] = password
            if task_id in self.item_widgets:
                self.item_widgets[task_id].pass_btn.configure(fg_color="#FFAB00", text_color="#0A0C10")

    def _on_item_password(self, task_id: str):
        if task_id in self.tasks:
            self.on_password_req_cb(task_id, os.path.basename(self.tasks[task_id]["input_path"]), self.tasks[task_id]["password"] or "")

    def _update_counter(self):
        self.count_lbl.configure(text=f"{len(self.tasks)} Archive(s) Queued")
