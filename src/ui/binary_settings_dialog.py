import customtkinter as ctk
from tkinter import filedialog
from typing import Callable
from src.binary_resolver import BinaryResolver

class BinarySettingsDialog(ctk.CTkToplevel):
    """
    5-Tier Unarchiver Binary Inspector & Configuration Modal Dialog.
    """
    def __init__(self, parent, resolver: BinaryResolver, on_update_cb: Callable[[], None]):
        super().__init__(parent)
        self.title("Binary Resolution Inspector (7-Zip & UnRAR)")
        self.geometry("580x380")
        self.resizable(False, False)
        self.configure(fg_color="#121620")

        self.resolver = resolver
        self.on_update_cb = on_update_cb

        self.transient(parent)
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Unarchiver Binary Resolution Inspector",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F0F4F8"
        )
        title_label.pack(pady=(18, 5))

        desc = ctk.CTkLabel(
            self,
            text="Resolves external 7z and UnRAR static executables for proprietary or RAR5 encrypted archives.",
            font=ctk.CTkFont(size=11),
            text_color="#8B96A5"
        )
        desc.pack(pady=(0, 15))

        # 7-Zip section card
        self._build_binary_card(
            title="7-Zip Binary (7z.exe / 7za.exe)",
            tool_key="7z",
            set_func=self._pick_7z_path
        )

        # UnRAR section card
        self._build_binary_card(
            title="UnRAR Binary (UnRAR.exe)",
            tool_key="unrar",
            set_func=self._pick_unrar_path
        )

        # Close Button
        close_btn = ctk.CTkButton(
            self,
            text="Close Inspector",
            fg_color="#1B202E",
            hover_color="#273044",
            text_color="#F0F4F8",
            width=140,
            command=self.destroy
        )
        close_btn.pack(pady=15)

    def _build_binary_card(self, title: str, tool_key: str, set_func: Callable[[], None]):
        card = ctk.CTkFrame(self, fg_color="#1B202E", border_color="#273044", border_width=1, corner_radius=8)
        card.pack(fill="x", padx=20, pady=6)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))

        lbl = ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(weight="bold", size=12), text_color="#00E5FF")
        lbl.pack(side="left")

        status = self.resolver.get_status()[tool_key]
        tier_str = status["tier"]
        path_str = status["path"] or "Not Detected (Using Pure Python Driver)"

        status_lbl = ctk.CTkLabel(
            hdr,
            text=f"Status: {tier_str}",
            font=ctk.CTkFont(size=11),
            text_color="#10B981" if status["available"] else "#F59E0B"
        )
        status_lbl.pack(side="right")

        path_lbl = ctk.CTkLabel(
            card,
            text=f"Resolved Path: {path_str}",
            font=ctk.CTkFont(family="Cascadia Code", size=10),
            text_color="#8B96A5",
            anchor="w",
            wraplength=420
        )
        path_lbl.pack(fill="x", padx=12, pady=(0, 10))

        btn = ctk.CTkButton(
            card,
            text="Browse Executable...",
            fg_color="#273044",
            hover_color="#37435F",
            text_color="#F0F4F8",
            height=24,
            width=130,
            font=ctk.CTkFont(size=11),
            command=set_func
        )
        btn.pack(anchor="e", padx=12, pady=(0, 10))

    def _pick_7z_path(self):
        file_path = filedialog.askopenfilename(
            title="Select 7z.exe or 7za.exe",
            filetypes=[("Executables", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            if self.resolver.set_manual_7z(file_path):
                self.on_update_cb()
                self.destroy()
            else:
                ctk.CTkMessagebox(title="Invalid Executable", message="Selected executable failed execution check.", icon="cancel")

    def _pick_unrar_path(self):
        file_path = filedialog.askopenfilename(
            title="Select UnRAR.exe or WinRAR.exe",
            filetypes=[("Executables", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            if self.resolver.set_manual_unrar(file_path):
                self.on_update_cb()
                self.destroy()
            else:
                ctk.CTkMessagebox(title="Invalid Executable", message="Selected executable failed execution check.", icon="cancel")
