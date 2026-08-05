import os
import queue
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional, List, Dict, Any

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = object

from src.binary_resolver import BinaryResolver
from src.worker_thread import WorkerThreadManager, TranscodeTask
from src.transcoder_engine import TranscoderEngine
from src.ui.settings_sidebar import SettingsSidebar
from src.ui.queue_widget import BatchQueueWidget
from src.ui.log_drawer import TelemetryLogDrawer
from src.ui.password_dialog import PasswordDialog
from src.ui.binary_settings_dialog import BinarySettingsDialog

class MainWindow(ctk.CTk if not DND_AVAILABLE else ctk.CTk):
    """
    Main CustomTkinter Window with 25Hz Inter-Thread Queue Polling & Streaming Metrics.
    """
    def __init__(self):
        super().__init__()

        # Enable TkinterDnD wrapper if available
        if DND_AVAILABLE:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:
                pass

        self.title("Archive Transcoder Pro v1.0.0-PROD (ZIP / 7Z / RAR / TAR)")
        self.geometry("1100x720")
        self.minsize(980, 640)

        # Titanium Forge Theme Setup
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0A0C10")

        # Core Components Initialization
        self.event_queue = queue.Queue()
        self.binary_resolver = BinaryResolver()
        self.worker_manager = WorkerThreadManager(self.event_queue, self.binary_resolver)
        self.engine = TranscoderEngine(self.binary_resolver)

        self.active_tasks_count = 0
        self.is_processing_batch = False

        # Build GUI Layout
        self._build_header_bar()
        self._build_main_layout()

        # Register Drop Zone if TkinterDnD available
        self._setup_drag_and_drop()

        # Start Inter-thread Polling Loop at 25 Hz (40ms interval)
        self.after(40, self._poll_event_queue)

        # Log system status
        bstatus = self.binary_resolver.get_status()
        self.log_drawer.log_info(f"7-Zip Binary: {bstatus['7z']['tier']}")
        self.log_drawer.log_info(f"UnRAR Binary: {bstatus['unrar']['tier']}")

    def _build_header_bar(self):
        hdr = ctk.CTkFrame(self, fg_color="#121620", height=50, border_color="#273044", border_width=1, corner_radius=0)
        hdr.pack(fill="x", side="top")

        # Left Branding
        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=8)

        app_title = ctk.CTkLabel(
            title_box,
            text="ARCHIVE TRANSCODER PRO",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F0F4F8"
        )
        app_title.pack(side="left")

        ver_badge = ctk.CTkLabel(
            title_box,
            text="v1.0.0-PROD",
            font=ctk.CTkFont(family="Cascadia Code", size=10, weight="bold"),
            text_color="#FFAB00",
            fg_color="#1B202E",
            corner_radius=4,
            width=80,
            height=20
        )
        ver_badge.pack(side="left", padx=10)

        # Right Telemetry Speed & Status Badge
        self.status_lbl = ctk.CTkLabel(
            hdr,
            text="SYSTEM READY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#10B981",
            fg_color="#1B202E",
            corner_radius=6,
            width=110,
            height=26
        )
        self.status_lbl.pack(side="right", padx=15, pady=8)

        self.throughput_lbl = ctk.CTkLabel(
            hdr,
            text="Speed: 0.00 MB/s | ETA: --:--",
            font=ctk.CTkFont(family="Cascadia Code", size=11),
            text_color="#00E5FF"
        )
        self.throughput_lbl.pack(side="right", padx=15, pady=8)

        add_file_btn = ctk.CTkButton(
            hdr,
            text="+ Add Archives...",
            fg_color="#273044",
            hover_color="#37435F",
            text_color="#F0F4F8",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_add_files_click
        )
        add_file_btn.pack(side="right", padx=10)

    def _build_main_layout(self):
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Compression Settings Sidebar
        self.sidebar = SettingsSidebar(
            main_content,
            on_start_batch_cb=self._start_batch_transcode,
            on_open_binary_dialog_cb=self._open_binary_inspector
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))

        # Right: Queue Table + Log Console
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)

        self.queue_widget = BatchQueueWidget(
            right_panel,
            on_password_req_cb=self._open_password_dialog,
            on_queue_change_cb=self._on_queue_changed
        )
        self.queue_widget.pack(fill="both", expand=True, pady=(0, 10))

        self.log_drawer = TelemetryLogDrawer(right_panel, height=140)
        self.log_drawer.pack(fill="x", side="bottom")

    def _setup_drag_and_drop(self):
        if DND_AVAILABLE:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self._on_files_dropped)
                self.log_drawer.log_info("Native Drag & Drop OS file listener active.")
            except Exception:
                pass

    def _on_files_dropped(self, event):
        raw_data = event.data
        files = self._parse_dropped_files(raw_data)
        self._add_files_to_queue(files)

    def _parse_dropped_files(self, raw_str: str) -> List[str]:
        # Handle curly braces or quoted paths in Windows drag and drop
        result = []
        in_curly = False
        current = ""
        for char in raw_str:
            if char == '{':
                in_curly = True
            elif char == '}':
                in_curly = False
                if current:
                    result.append(current.strip())
                    current = ""
            elif char == ' ' and not in_curly:
                if current:
                    result.append(current.strip())
                    current = ""
            else:
                current += char
        if current:
            result.append(current.strip())
        return result

    def _on_add_files_click(self):
        files = filedialog.askopenfilenames(
            title="Select Archive Files to Transcode",
            filetypes=[
                ("All Archive Formats", "*.zip;*.7z;*.rar;*.tar;*.gz;*.tgz;*.bz2;*.tbz2;*.xz;*.txz"),
                ("ZIP Archives", "*.zip"),
                ("7-Zip Archives", "*.7z"),
                ("RAR Archives", "*.rar"),
                ("TAR Archives", "*.tar;*.gz;*.tgz;*.bz2;*.tbz2;*.xz;*.txz"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self._add_files_to_queue(list(files))

    def _add_files_to_queue(self, files: List[str]):
        settings = self.sidebar.get_settings()
        target_fmt = settings["target_format"]

        valid_count = 0
        for f in files:
            if os.path.isfile(f):
                source_fmt = self.engine.get_archive_type(f)
                if source_fmt != "UNKNOWN":
                    self.queue_widget.add_archive_file(f, target_fmt, source_fmt)
                    valid_count += 1
                    self.log_drawer.log_info(f"Queued target: '{os.path.basename(f)}' ({source_fmt} ➔ {target_fmt})")
                else:
                    self.log_drawer.log_warning(f"Skipped unsupported archive format: '{os.path.basename(f)}'")

    def _on_queue_changed(self):
        # Update target format across queue if user changes dropdown
        settings = self.sidebar.get_settings()
        self.queue_widget.update_task_target_format(settings["target_format"])

    def _start_batch_transcode(self):
        if not self.queue_widget.tasks:
            self.log_drawer.log_warning("No archives in queue. Drag files into window to begin.")
            return

        if self.is_processing_batch:
            self.log_drawer.log_warning("Batch transcoding already in progress...")
            return

        settings = self.sidebar.get_settings()
        output_dir = settings["output_directory"]

        ext_map = {
            "ZIP": ".zip",
            "7Z": ".7z",
            "TAR.GZ": ".tar.gz",
            "TAR.BZ2": ".tar.bz2",
            "TAR.XZ": ".tar.xz",
            "TAR": ".tar"
        }
        target_ext = ext_map.get(settings["target_format"], ".zip")

        self.is_processing_batch = True
        self.status_lbl.configure(text="STREAMING...", text_color="#FFAB00")
        self.sidebar.start_btn.configure(state="disabled", text="⚡ TRANSCODING IN PROGRESS...")

        self.worker_manager.start()

        for task_id, task_data in self.queue_widget.tasks.items():
            input_path = task_data["input_path"]
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            if base_name.lower().endswith(".tar"):
                base_name = os.path.splitext(base_name)[0]
            
            output_path = os.path.join(output_dir, f"{base_name}_transcoded{target_ext}")

            # Use task-specific password if set, else global passphrase
            pwd = task_data["password"] or settings["password"]

            task = TranscodeTask(
                task_id=task_id,
                input_path=input_path,
                output_path=output_path,
                target_format=settings["target_format"],
                compression_level=settings["compression_level"],
                algorithm=settings["algorithm"],
                password=pwd,
                verify_checksums=settings["verify_checksums"]
            )
            self.worker_manager.add_task(task)
            self.log_drawer.log_info(f"Queued stream transcode job {task_id} for '{base_name}'")

    def _open_password_dialog(self, task_id: str, filename: str, current_pass: str):
        def apply_cb(pwd: str):
            self.queue_widget.update_task_password(task_id, pwd)
            self.log_drawer.log_info(f"Updated passphrase credentials for '{filename}'")

        dlg = PasswordDialog(self, filename=filename, on_submit=apply_cb, initial_password=current_pass)

    def _open_binary_inspector(self):
        def update_cb():
            bstatus = self.binary_resolver.get_status()
            self.log_drawer.log_success(f"Updated binary path resolution: 7z={bstatus['7z']['tier']}, unrar={bstatus['unrar']['tier']}")

        dlg = BinarySettingsDialog(self, resolver=self.binary_resolver, on_update_cb=update_cb)

    def _poll_event_queue(self):
        """
        25 Hz Inter-Thread Event Queue Poller (40ms interval).
        """
        try:
            while True:
                event = self.event_queue.get_nowait()
                event_type = event[0]

                if event_type == 'STATUS':
                    _, task_id, state = event
                    if task_id in self.queue_widget.item_widgets:
                        self.queue_widget.item_widgets[task_id].update_status(state)

                elif event_type == 'PROGRESS':
                    _, task_id, bytes_p, total_b, pct = event
                    if task_id in self.queue_widget.item_widgets:
                        self.queue_widget.item_widgets[task_id].update_progress(pct)

                elif event_type == 'ENTRY':
                    _, task_id, current_entry = event
                    if task_id in self.queue_widget.item_widgets:
                        item = self.queue_widget.item_widgets[task_id]
                        item.update_progress(item.progress_bar.get() * 100, current_entry)

                elif event_type == 'THROUGHPUT':
                    _, task_id, mb_s, eta_s = event
                    m, s = divmod(max(0, eta_s), 60)
                    self.throughput_lbl.configure(text=f"Speed: {mb_s:.2f} MB/s | ETA: {m:02d}:{s:02d}")

                elif event_type == 'COMPLETE':
                    _, task_id, out_path, stats = event
                    if task_id in self.queue_widget.item_widgets:
                        self.queue_widget.item_widgets[task_id].update_status('COMPLETED')
                        self.queue_widget.item_widgets[task_id].set_completed_stats(stats)
                    self.log_drawer.log_success(
                        f"Completed '{os.path.basename(out_path)}' ({stats['file_count']} files, "
                        f"{stats['output_size_bytes']/(1024*1024):.2f} MB, {stats['compression_ratio_pct']}% ratio in {stats['elapsed_seconds']}s)"
                    )
                    self._check_batch_completion()

                elif event_type == 'ERROR':
                    _, task_id, err_msg = event
                    if task_id in self.queue_widget.item_widgets:
                        self.queue_widget.item_widgets[task_id].update_status('FAILED')
                    self.log_drawer.log_error(f"Task {task_id} failed: {err_msg}")
                    self._check_batch_completion()

                self.event_queue.task_done()

        except queue.Empty:
            pass
        finally:
            self.after(40, self._poll_event_queue)

    def _check_batch_completion(self):
        # Check if all tasks in queue have completed or failed
        all_finished = True
        for widget in self.queue_widget.item_widgets.values():
            if widget.status_badge.cget("text") in ("PENDING", "PROCESSING"):
                all_finished = False
                break

        if all_finished and self.is_processing_batch:
            self.is_processing_batch = False
            self.status_lbl.configure(text="SYSTEM READY", text_color="#10B981")
            self.throughput_lbl.configure(text="Speed: 0.00 MB/s | ETA: 00:00")
            self.sidebar.start_btn.configure(state="normal", text="⚡ START BATCH TRANSCODE")
            self.log_drawer.log_success("All batch stream transcoding tasks finished.")
