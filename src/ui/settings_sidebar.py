import os
import customtkinter as ctk
from tkinter import filedialog
from typing import Dict, Any, Callable

class SettingsSidebar(ctk.CTkFrame):
    """
    Compression Parameters & Target Transcoding Settings Sidebar Panel.
    """
    def __init__(self, parent, on_start_batch_cb: Callable[[], None], on_open_binary_dialog_cb: Callable[[], None]):
        super().__init__(parent, fg_color="#121620", border_color="#273044", border_width=1, corner_radius=8, width=320)
        self.on_start_batch_cb = on_start_batch_cb
        self.on_open_binary_dialog_cb = on_open_binary_dialog_cb

        # Default Output Path
        default_out = os.path.join(os.path.expanduser("~"), "Desktop", "Transcoded_Archives")

        # Scrollable container for parameters
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Title
        hdr_lbl = ctk.CTkLabel(
            self.container,
            text="Transcode Parameters",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#F0F4F8"
        )
        hdr_lbl.pack(anchor="w", pady=(0, 10))

        # 1. Target Format Picker
        self._build_section_header("1. Target Output Format")
        self.target_format_var = ctk.StringVar(value="7Z")
        self.format_menu = ctk.CTkOptionMenu(
            self.container,
            values=["ZIP", "7Z", "TAR.GZ", "TAR.BZ2", "TAR.XZ", "TAR"],
            variable=self.target_format_var,
            fg_color="#1B202E",
            button_color="#273044",
            button_hover_color="#00E5FF",
            dropdown_fg_color="#1B202E",
            text_color="#00E5FF",
            font=ctk.CTkFont(weight="bold")
        )
        self.format_menu.pack(fill="x", pady=(0, 15))

        # 2. Compression Level Solver
        self._build_section_header("2. Compression Level & Preset")
        self.level_var = ctk.StringVar(value="Standard")
        self.level_menu = ctk.CTkOptionMenu(
            self.container,
            values=["Store (0)", "Fast (1-3)", "Standard (5)", "High (7)", "Ultra (9)"],
            command=self._on_level_menu_change,
            fg_color="#1B202E",
            button_color="#273044",
            button_hover_color="#FFAB00",
            dropdown_fg_color="#1B202E",
            text_color="#FFAB00",
            font=ctk.CTkFont(weight="bold")
        )
        self.level_menu.pack(fill="x", pady=(0, 5))

        self.level_slider = ctk.CTkSlider(
            self.container,
            from_=0,
            to=4,
            number_of_steps=4,
            command=self._on_slider_change,
            button_color="#FFAB00",
            button_hover_color="#D99200",
            progress_color="#FFAB00"
        )
        self.level_slider.set(2)  # Standard
        self.level_slider.pack(fill="x", pady=(0, 15))

        # 3. Compression Algorithm Solver
        self._build_section_header("3. Compression Algorithm Switch")
        self.algo_var = ctk.StringVar(value="LZMA2")
        self.algo_menu = ctk.CTkOptionMenu(
            self.container,
            values=["Deflate", "LZMA2", "Bzip2", "Zstandard", "Store"],
            variable=self.algo_var,
            fg_color="#1B202E",
            button_color="#273044",
            button_hover_color="#00E5FF",
            dropdown_fg_color="#1B202E",
            text_color="#F0F4F8"
        )
        self.algo_menu.pack(fill="x", pady=(0, 15))

        # 4. Encryption & Password Preservation
        self._build_section_header("4. Encryption & AES-256 Passphrase")
        self.pass_entry = ctk.CTkEntry(
            self.container,
            show="•",
            placeholder_text="Global AES-256 passphrase...",
            fg_color="#0A0C10",
            border_color="#273044",
            text_color="#F0F4F8"
        )
        self.pass_entry.pack(fill="x", pady=(0, 15))

        # 5. Output Directory Picker
        self._build_section_header("5. Target Destination Directory")
        self.out_dir_entry = ctk.CTkEntry(
            self.container,
            fg_color="#0A0C10",
            border_color="#273044",
            text_color="#8B96A5",
            font=ctk.CTkFont(family="Cascadia Code", size=10)
        )
        self.out_dir_entry.insert(0, default_out)
        self.out_dir_entry.pack(fill="x", pady=(0, 5))

        browse_btn = ctk.CTkButton(
            self.container,
            text="Browse Destination...",
            fg_color="#1B202E",
            hover_color="#273044",
            text_color="#00E5FF",
            height=26,
            command=self._browse_output_dir
        )
        browse_btn.pack(fill="x", pady=(0, 15))

        # 6. Pre/Post Integrity Checksum Verification
        self._build_section_header("6. Payload Integrity Verification")
        self.checksum_var = ctk.BooleanVar(value=True)
        self.checksum_cb = ctk.CTkCheckBox(
            self.container,
            text="Pre/Post CRC32 & SHA-256 Verification",
            variable=self.checksum_var,
            font=ctk.CTkFont(size=11),
            text_color="#8B96A5",
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.checksum_cb.pack(anchor="w", pady=(0, 15))

        # 7. Unarchiver Binary Status Inspector Button
        bin_btn = ctk.CTkButton(
            self.container,
            text="🔍 Unarchiver Binaries Inspector",
            fg_color="#1B202E",
            hover_color="#273044",
            text_color="#8B96A5",
            border_color="#273044",
            border_width=1,
            height=28,
            command=self.on_open_binary_dialog_cb
        )
        bin_btn.pack(fill="x", pady=(0, 20))

        # 8. Main Start CTA Button
        self.start_btn = ctk.CTkButton(
            self,
            text="⚡ START BATCH TRANSCODE",
            fg_color="#FFAB00",
            hover_color="#D99200",
            text_color="#0A0C10",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42,
            corner_radius=8,
            command=self.on_start_batch_cb
        )
        self.start_btn.pack(fill="x", padx=15, pady=15)

    def _build_section_header(self, text: str):
        lbl = ctk.CTkLabel(
            self.container,
            text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8B96A5"
        )
        lbl.pack(anchor="w", pady=(0, 4))

    def _on_level_menu_change(self, choice: str):
        mapping = {
            "Store (0)": 0,
            "Fast (1-3)": 1,
            "Standard (5)": 2,
            "High (7)": 3,
            "Ultra (9)": 4
        }
        self.level_slider.set(mapping.get(choice, 2))

    def _on_slider_change(self, val: float):
        mapping = ["Store", "Fast", "Standard", "High", "Ultra"]
        idx = int(round(val))
        display_names = ["Store (0)", "Fast (1-3)", "Standard (5)", "High (7)", "Ultra (9)"]
        self.level_menu.set(display_names[idx])

    def _browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="Select Destination Directory")
        if dir_path:
            self.out_dir_entry.delete(0, "end")
            self.out_dir_entry.insert(0, dir_path)

    def get_settings(self) -> Dict[str, Any]:
        display_to_level = {
            "Store (0)": "Store",
            "Fast (1-3)": "Fast",
            "Standard (5)": "Standard",
            "High (7)": "High",
            "Ultra (9)": "Ultra"
        }
        return {
            "target_format": self.target_format_var.get(),
            "compression_level": display_to_level.get(self.level_menu.get(), "Standard"),
            "algorithm": self.algo_var.get(),
            "password": self.pass_entry.get() if self.pass_entry.get().strip() else None,
            "output_directory": self.out_dir_entry.get().strip(),
            "verify_checksums": self.checksum_var.get()
        }
