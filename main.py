import os
import sys
import customtkinter as ctk

# Add workspace directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import MainWindow

def main():
    # Configure CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = MainWindow()

    # Apply Icon Asset if available
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    if os.path.exists(icon_path):
        try:
            app.iconbitmap(icon_path)
        except Exception:
            pass

    app.mainloop()

if __name__ == "__main__":
    main()
