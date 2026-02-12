"""Liblouis bridge for cross-platform compatibility."""

import sys
import os

# On Linux, prefer system louis (python3-louis) over bundled copy
# On macOS, use bundled copy with Homebrew's liblouis
if sys.platform.startswith("linux"):
    # Add system dist-packages to path if needed for python3-louis
    if "/usr/lib/python3/dist-packages" not in sys.path:
        sys.path.insert(0, "/usr/lib/python3/dist-packages")
    try:
        import louis
    except ImportError as e:
        raise ImportError(
            "liblouis Python bindings not found. "
            "On Linux: apt install python3-louis or dnf install python3-louis"
        ) from e
else:
    # macOS: Use local bundled copy (requires brew install liblouis)
    try:
        from liblouis_bridge import louis
    except ImportError as e:
        raise ImportError(
            "liblouis Python bindings not found. "
            "On macOS: brew install liblouis (louis package included in src/liblouis_bridge/)"
        ) from e

__all__ = ["louis"]
