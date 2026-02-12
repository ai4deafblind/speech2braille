"""Liblouis bridge for cross-platform compatibility."""

import sys
import os

# Try local copy first (macOS Homebrew)
try:
    from liblouis_bridge import louis
except ImportError:
    # Fallback to system louis (Linux python3-louis)
    try:
        import louis
    except ImportError as e:
        raise ImportError(
            "liblouis Python bindings not found. "
            "On macOS: brew install liblouis (louis package included in src/liblouis_bridge/)\n"
            "On Linux: apt install python3-louis or dnf install python3-louis"
        ) from e

__all__ = ["louis"]
