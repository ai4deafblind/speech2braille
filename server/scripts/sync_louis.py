"""Sync liblouis Python ctypes bindings into the bundled copy.

Auto-detects the liblouis Python bindings location:
  - macOS Homebrew (auto-detects version and Python version)
  - Linux system dist-packages
  - MSYS2 on Windows

Usage: uv run python scripts/sync_louis.py
"""

import shutil
import sys
from pathlib import Path


def find_louis_source() -> Path | None:
    """Find the louis Python package from the system liblouis installation."""
    candidates: list[Path] = []

    if sys.platform == "darwin":
        # Homebrew: /opt/homebrew/Cellar/liblouis/<version>/lib/python<ver>/site-packages/louis
        for homebrew_prefix in ("/opt/homebrew", "/usr/local"):
            cellar = Path(homebrew_prefix) / "Cellar" / "liblouis"
            if cellar.is_dir():
                # Find the latest version
                versions = sorted(cellar.iterdir(), reverse=True)
                for ver_dir in versions:
                    # Find any python version's site-packages
                    lib_dir = ver_dir / "lib"
                    if lib_dir.is_dir():
                        for pydir in sorted(lib_dir.glob("python*/site-packages/louis"), reverse=True):
                            candidates.append(pydir)

        # Also check Homebrew's lib/python directly (linked install)
        for homebrew_prefix in ("/opt/homebrew", "/usr/local"):
            lib_dir = Path(homebrew_prefix) / "lib"
            if lib_dir.is_dir():
                for pydir in sorted(lib_dir.glob("python*/site-packages/louis"), reverse=True):
                    candidates.append(pydir)

    elif sys.platform == "win32":
        # MSYS2
        msys2_louis = Path(r"C:\msys64\mingw64\lib\python3\dist-packages\louis")
        if msys2_louis.is_dir():
            candidates.append(msys2_louis)

    else:
        # Linux
        for dist_path in (
            "/usr/lib/python3/dist-packages/louis",
            "/usr/local/lib/python3/dist-packages/louis",
        ):
            p = Path(dist_path)
            if p.is_dir():
                candidates.append(p)

    # Return first valid candidate
    for c in candidates:
        init_file = c / "__init__.py"
        if init_file.is_file():
            return c

    return None


def sync_louis() -> None:
    source = find_louis_source()
    if source is None:
        print("Error: could not find liblouis Python bindings.", file=sys.stderr)
        if sys.platform == "darwin":
            print("Install with: brew install liblouis", file=sys.stderr)
        elif sys.platform == "win32":
            print("Install via MSYS2: pacman -S mingw-w64-x86_64-liblouis", file=sys.stderr)
        else:
            print("Install with: sudo apt install liblouis-dev", file=sys.stderr)
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    dest = script_dir.parent / "src" / "liblouis_bridge" / "louis"

    print(f"Source: {source}")
    print(f"Destination: {dest}")

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)

    print("Synced louis Python bindings successfully.")


if __name__ == "__main__":
    sync_louis()
