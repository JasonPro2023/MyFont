import os
import platform
import subprocess
import sys


def build():
    system = platform.system()
    app_name = "MyFont"

    # Base PyInstaller arguments
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # Suppresses terminal console window on Windows/macOS
        "--name",
        app_name,
        # Ensure local 'core' package is bundled
        "--paths",
        ".",
        # Exclude heavy unused libraries if present in the global environment
        "--exclude-module",
        "matplotlib",
        "--exclude-module",
        "scipy",
        "--exclude-module",
        "pandas",
        "--exclude-module",
        "PyQt5",
        "--exclude-module",
        "PyQt6",
        "--exclude-module",
        "PySide6",
        "main.py",
    ]

    # Single-file portable binary on Windows & Linux; .app bundle on macOS
    if system in ("Windows", "Linux"):
        cmd.insert(5, "--onefile")

    print(f"Building {app_name} for {system}...")
    subprocess.run(cmd, check=True)

    if system == "Windows":
        out = os.path.join("dist", f"{app_name}.exe")
    elif system == "Darwin":
        out = os.path.join("dist", f"{app_name}.app")
    else:
        out = os.path.join("dist", app_name)

    print(f"\nBuild complete! Portable output located at:\n  {os.path.abspath(out)}")


if __name__ == "__main__":
    build()