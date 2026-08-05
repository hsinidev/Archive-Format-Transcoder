import customtkinter as ctk
from typing import Optional, Callable

class PasswordDialog(ctk.CTkToplevel):
    """
    AES-256 Password Prompt Inspector modal dialog for encrypted archive items.
    """
    def __init__(self, parent, filename: str, on_submit: Callable[[str], None], initial_password: str = ""):
        super().__init__(parent)
        self.title("Encryption Passphrase Inspector")
        self.geometry("450x260")
        self.resizable(False, False)

        # Titanium Forge Palette
        self.configure(fg_color="#121620")

        self.on_submit = on_submit
        self.result_password: Optional[str] = None

        # Modal grabs
        self.transient(parent)
        self.grab_set()

        # Build UI
        title_label = ctk.CTkLabel(
            self,
            text="AES-256 Passphrase Prompt",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F0F4F8"
        )
        title_label.pack(pady=(18, 5))

        file_label = ctk.CTkLabel(
            self,
            text=f"Target Archive: {filename}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#00E5FF",
            wraplength=400
        )
        file_label.pack(pady=(0, 15))

        # Entry card frame
        card = ctk.CTkFrame(self, fg_color="#1B202E", border_color="#273044", border_width=1, corner_radius=8)
        card.pack(fill="x", padx=20, pady=5)

        entry_lbl = ctk.CTkLabel(card, text="Passphrase:", font=ctk.CTkFont(size=12), text_color="#8B96A5")
        entry_lbl.pack(anchor="w", padx=15, pady=(10, 2))

        self.entry = ctk.CTkEntry(
            card,
            show="•",
            placeholder_text="Enter AES-256 passphrase...",
            fg_color="#0A0C10",
            border_color="#273044",
            text_color="#F0F4F8",
            width=380
        )
        self.entry.pack(padx=15, pady=(0, 10))
        if initial_password:
            self.entry.insert(0, initial_password)

        self.show_pass_var = ctk.BooleanVar(value=False)
        show_cb = ctk.CTkCheckBox(
            card,
            text="Show Passphrase",
            variable=self.show_pass_var,
            command=self._toggle_show,
            font=ctk.CTkFont(size=11),
            text_color="#8B96A5",
            fg_color="#FFAB00",
            hover_color="#D99200"
        )
        show_cb.pack(anchor="w", padx=15, pady=(0, 12))

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(15, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#1B202E",
            hover_color="#273044",
            text_color="#8B96A5",
            width=100,
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Apply Passphrase",
            fg_color="#FFAB00",
            hover_color="#D99200",
            text_color="#0A0C10",
            font=ctk.CTkFont(weight="bold"),
            width=140,
            command=self._on_apply
        )
        save_btn.pack(side="right")

    def _toggle_show(self):
        if self.show_pass_var.get():
            self.entry.configure(show="")
        else:
            self.entry.configure(show="•")

    def _on_apply(self):
        pwd = self.entry.get()
        if self.on_submit:
            self.on_submit(pwd)
        self.destroy()
