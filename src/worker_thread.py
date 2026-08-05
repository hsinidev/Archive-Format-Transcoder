import time
import queue
import threading
from typing import Dict, Any, Optional

from src.transcoder_engine import TranscoderEngine
from src.binary_resolver import BinaryResolver

class TranscodeTask:
    """Represents a single conversion item in the batch queue."""
    def __init__(
        self,
        task_id: str,
        input_path: str,
        output_path: str,
        target_format: str,
        compression_level: str = "Standard",
        algorithm: str = "Deflate",
        password: Optional[str] = None,
        verify_checksums: bool = True
    ):
        self.task_id = task_id
        self.input_path = input_path
        self.output_path = output_path
        self.target_format = target_format
        self.compression_level = compression_level
        self.algorithm = algorithm
        self.password = password
        self.verify_checksums = verify_checksums
        self.status = "PENDING"  # PENDING, PROCESSING, COMPLETED, FAILED

class WorkerThreadManager:
    """
    Manages background thread execution for batch archive transcoding tasks.
    Streams atomic telemetry events via thread-safe queue.Queue.
    """
    def __init__(self, event_queue: queue.Queue, binary_resolver: Optional[BinaryResolver] = None):
        self.event_queue = event_queue
        self.binary_resolver = binary_resolver or BinaryResolver()
        self.engine = TranscoderEngine(self.binary_resolver)
        
        self.task_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self.is_running = False

    def add_task(self, task: TranscodeTask):
        self.task_queue.put(task)

    def start(self):
        if not self.is_running:
            self._stop_event.clear()
            self.is_running = True
            self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._worker_thread.start()

    def stop(self):
        self._stop_event.set()
        self.is_running = False

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                task: TranscodeTask = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self._process_single_task(task)
            self.task_queue.task_done()

        self.is_running = False

    def _process_single_task(self, task: TranscodeTask):
        task.status = "PROCESSING"
        self.event_queue.put(('STATUS', task.task_id, 'PROCESSING'))

        start_time = time.time()
        last_telemetry_time = time.time()

        def progress_callback(bytes_processed: int, total_bytes: int, current_entry: str):
            nonlocal last_telemetry_time
            now = time.time()
            elapsed = now - start_time
            
            pct = ((bytes_processed / total_bytes) * 100.0) if total_bytes > 0 else 0.0
            mb_per_sec = ((bytes_processed / (1024 * 1024)) / elapsed) if elapsed > 0 else 0.0
            
            remaining_bytes = max(0, total_bytes - bytes_processed)
            bytes_per_sec = (bytes_processed / elapsed) if elapsed > 0 else 0.0
            eta_sec = (remaining_bytes / bytes_per_sec) if bytes_per_sec > 0 else 0.0

            # Emit progress & throughput throttled to avoid GUI flood (every 40ms or 25Hz)
            if now - last_telemetry_time >= 0.04 or bytes_processed == total_bytes:
                last_telemetry_time = now
                self.event_queue.put(('PROGRESS', task.task_id, bytes_processed, total_bytes, round(pct, 1)))
                self.event_queue.put(('THROUGHPUT', task.task_id, round(mb_per_sec, 2), int(eta_sec)))
                self.event_queue.put(('ENTRY', task.task_id, current_entry))

        try:
            stats = self.engine.transcode_archive(
                input_path=task.input_path,
                output_path=task.output_path,
                target_format=task.target_format,
                compression_level=task.compression_level,
                algorithm=task.algorithm,
                password=task.password,
                verify_checksums=task.verify_checksums,
                progress_cb=progress_callback
            )

            task.status = "COMPLETED"
            self.event_queue.put(('STATUS', task.task_id, 'COMPLETED'))
            self.event_queue.put(('COMPLETE', task.task_id, task.output_path, stats))

        except py7zr.PasswordRequired:
            task.status = "FAILED"
            self.event_queue.put(('STATUS', task.task_id, 'FAILED'))
            self.event_queue.put(('ERROR', task.task_id, "Encrypted archive: Password required."))

        except rarfile.PasswordRequired:
            task.status = "FAILED"
            self.event_queue.put(('STATUS', task.task_id, 'FAILED'))
            self.event_queue.put(('ERROR', task.task_id, "Encrypted RAR: Password required or invalid."))

        except Exception as e:
            task.status = "FAILED"
            self.event_queue.put(('STATUS', task.task_id, 'FAILED'))
            self.event_queue.put(('ERROR', task.task_id, str(e)))
