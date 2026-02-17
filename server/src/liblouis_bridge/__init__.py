"""Liblouis bridge for cross-platform compatibility.

All platforms use the bundled ctypes bindings in liblouis_bridge.louis.
The C shared library (liblouis) must be installed separately per OS.
"""

import sys

try:
    from liblouis_bridge import louis
except ImportError as e:
    if sys.platform == "darwin":
        hint = "On macOS: brew install liblouis"
    elif sys.platform == "win32":
        hint = (
            "On Windows: download liblouis from GitHub releases "
            "(https://github.com/liblouis/liblouis/releases) "
            "and set LIBLOUIS_DIR to the install path, "
            "or install via MSYS2: pacman -S mingw-w64-x86_64-liblouis"
        )
    else:
        hint = "On Linux: sudo apt install liblouis-dev liblouis-data"
    raise ImportError(f"liblouis not found. {hint}") from e

__all__ = ["louis"]
