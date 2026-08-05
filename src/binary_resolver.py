import os
import sys
import shutil
import subprocess
from typing import Dict, Optional, Tuple

class BinaryResolver:
    """
    5-Tier Dynamic Binary Resolver for 7-Zip (7z.exe/7za.exe) and UnRAR (unrar.exe).
    Resolution Order:
      1. sys._MEIPASS (PyInstaller frozen bundle runtime root)
      2. Application root directory / 'bin' subfolder (bin/7z/7z.exe, bin/unrar/unrar.exe)
      3. Local AppData & Program Files 7-Zip & WinRAR standard install paths
      4. System environment PATH (shutil.which)
      5. User interactive manual selection override
    """
    def __init__(self, custom_7z_path: Optional[str] = None, custom_unrar_path: Optional[str] = None):
        self._manual_7z_path: Optional[str] = custom_7z_path
        self._manual_unrar_path: Optional[str] = custom_unrar_path
        
        self.resolved_7z: Optional[str] = None
        self.resolved_unrar: Optional[str] = None
        self.tier_7z: str = "Unresolved"
        self.tier_unrar: str = "Unresolved"
        
        self.refresh_paths()

    def set_manual_7z(self, path: str) -> bool:
        if os.path.isfile(path) and self._test_executable(path):
            self._manual_7z_path = path
            self.refresh_paths()
            return True
        return False

    def set_manual_unrar(self, path: str) -> bool:
        if os.path.isfile(path) and self._test_executable(path):
            self._manual_unrar_path = path
            self.refresh_paths()
            return True
        return False

    def refresh_paths(self) -> None:
        self.resolved_7z, self.tier_7z = self._resolve_7z()
        self.resolved_unrar, self.tier_unrar = self._resolve_unrar()

    def _resolve_7z(self) -> Tuple[Optional[str], str]:
        # Tier 5: Manual override
        if self._manual_7z_path and os.path.isfile(self._manual_7z_path):
            return self._manual_7z_path, "Tier 5 (Manual Selection)"

        # Tier 1: PyInstaller Frozen Bundle
        if hasattr(sys, '_MEIPASS'):
            meipass = getattr(sys, '_MEIPASS')
            candidates = [
                os.path.join(meipass, "bin", "7z", "7z.exe"),
                os.path.join(meipass, "bin", "7z", "7za.exe"),
                os.path.join(meipass, "7z.exe"),
                os.path.join(meipass, "7za.exe")
            ]
            for c in candidates:
                if os.path.isfile(c):
                    return c, "Tier 1 (PyInstaller Bundle)"

        # Tier 2: Application Root / bin Subfolder
        app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        bin_candidates = [
            os.path.join(app_root, "bin", "7z", "7z.exe"),
            os.path.join(app_root, "bin", "7z", "7za.exe"),
            os.path.join(app_root, "bin", "7z.exe"),
            os.path.join(app_root, "bin", "7za.exe")
        ]
        for c in bin_candidates:
            if os.path.isfile(c):
                return c, "Tier 2 (App Bin Directory)"

        # Tier 3: Program Files & Local AppData
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        standard_paths = [
            os.path.join(program_files, "7-Zip", "7z.exe"),
            os.path.join(program_files_x86, "7-Zip", "7z.exe"),
            os.path.join(program_files, "7-Zip", "7za.exe"),
            os.path.join(local_appdata, "Programs", "7-Zip", "7z.exe"),
            "C:\\Program Files\\7-Zip\\7z.exe",
            "C:\\Program Files (x86)\\7-Zip\\7z.exe"
        ]
        for c in standard_paths:
            if os.path.isfile(c):
                return c, "Tier 3 (System Program Files)"

        # Tier 4: System PATH
        which_7z = shutil.which("7z") or shutil.which("7za") or shutil.which("7z.exe")
        if which_7z and os.path.isfile(which_7z):
            return which_7z, "Tier 4 (System PATH)"

        return None, "Unresolved (Using Pure Python py7zr)"

    def _resolve_unrar(self) -> Tuple[Optional[str], str]:
        # Tier 5: Manual override
        if self._manual_unrar_path and os.path.isfile(self._manual_unrar_path):
            return self._manual_unrar_path, "Tier 5 (Manual Selection)"

        # Tier 1: PyInstaller Frozen Bundle
        if hasattr(sys, '_MEIPASS'):
            meipass = getattr(sys, '_MEIPASS')
            candidates = [
                os.path.join(meipass, "bin", "unrar", "unrar.exe"),
                os.path.join(meipass, "unrar.exe")
            ]
            for c in candidates:
                if os.path.isfile(c):
                    return c, "Tier 1 (PyInstaller Bundle)"

        # Tier 2: Application Root / bin Subfolder
        app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        bin_candidates = [
            os.path.join(app_root, "bin", "unrar", "unrar.exe"),
            os.path.join(app_root, "bin", "unrar.exe")
        ]
        for c in bin_candidates:
            if os.path.isfile(c):
                return c, "Tier 2 (App Bin Directory)"

        # Tier 3: Program Files & WinRAR Install
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        standard_paths = [
            os.path.join(program_files, "WinRAR", "UnRAR.exe"),
            os.path.join(program_files, "WinRAR", "WinRAR.exe"),
            os.path.join(program_files_x86, "WinRAR", "UnRAR.exe"),
            os.path.join(local_appdata, "Programs", "WinRAR", "UnRAR.exe"),
            "C:\\Program Files\\WinRAR\\UnRAR.exe"
        ]
        for c in standard_paths:
            if os.path.isfile(c):
                return c, "Tier 3 (System Program Files)"

        # Tier 4: System PATH
        which_unrar = shutil.which("unrar") or shutil.which("UnRAR.exe") or shutil.which("unrar.exe")
        if which_unrar and os.path.isfile(which_unrar):
            return which_unrar, "Tier 4 (System PATH)"

        return None, "Unresolved (Using Pure Python rarfile)"

    def _test_executable(self, path: str) -> bool:
        try:
            res = subprocess.run([path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {
            "7z": {
                "path": self.resolved_7z,
                "tier": self.tier_7z,
                "available": self.resolved_7z is not None
            },
            "unrar": {
                "path": self.resolved_unrar,
                "tier": self.tier_unrar,
                "available": self.resolved_unrar is not None
            }
        }
