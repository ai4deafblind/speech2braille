"""Bootstrap and prerequisite checker for speech2braille.

Detects OS, checks required dependencies, and prints actionable install commands.

Usage: uv run python scripts/setup.py
"""

import shutil
import sys
from pathlib import Path


def check_mark(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def check_liblouis() -> bool:
    """Check if the liblouis C library can be loaded."""
    try:
        from liblouis_bridge import louis

        ver = louis.version()
        print(f"  liblouis: {check_mark(True)} (version {ver})")
        return True
    except (ImportError, OSError) as e:
        print(f"  liblouis: {check_mark(False)} ({e})")
        return False


def check_espeak() -> bool:
    """Check if espeak-ng is available (required by piper TTS)."""
    found = shutil.which("espeak-ng") is not None
    if not found:
        # Also check for espeak (some systems)
        found = shutil.which("espeak") is not None
    print(f"  espeak-ng: {check_mark(found)}")
    return found


def check_voices() -> bool:
    """Check if voice models are downloaded."""
    script_dir = Path(__file__).resolve().parent
    voice_dir = script_dir.parent / "models" / "piper" / "voices"
    onnx_files = list(voice_dir.glob("*.onnx")) if voice_dir.exists() else []
    found = len(onnx_files) > 0
    if found:
        print(f"  Voice models: {check_mark(True)} ({len(onnx_files)} model(s) in {voice_dir})")
    else:
        print(f"  Voice models: {check_mark(False)}")
    return found


def print_install_instructions(liblouis_ok: bool, espeak_ok: bool, voices_ok: bool) -> None:
    """Print platform-specific install instructions for missing dependencies."""
    if liblouis_ok and espeak_ok and voices_ok:
        print("\nAll prerequisites satisfied!")
        return

    print("\nInstall missing dependencies:")

    if sys.platform == "darwin":
        cmds = []
        if not liblouis_ok:
            cmds.append("brew install liblouis")
        if not espeak_ok:
            cmds.append("brew install espeak-ng")
        if cmds:
            print(f"  {' && '.join(cmds)}")

    elif sys.platform == "win32":
        if not liblouis_ok:
            print("  Download liblouis from: https://github.com/liblouis/liblouis/releases")
            print("  Set LIBLOUIS_DIR environment variable to the install path.")
            print("  Or via MSYS2: pacman -S mingw-w64-x86_64-liblouis")
        if not espeak_ok:
            print("  Download espeak-ng from: https://github.com/espeak-ng/espeak-ng/releases")
            print("  Or via MSYS2: pacman -S mingw-w64-x86_64-espeak-ng")

    else:
        pkgs = []
        if not liblouis_ok:
            pkgs.extend(["liblouis-dev", "liblouis-data"])
        if not espeak_ok:
            pkgs.append("espeak-ng")
        if pkgs:
            print(f"  sudo apt install {' '.join(pkgs)}")

    if not voices_ok:
        print("  uv run python scripts/download_voices.py")


def main() -> None:
    print(f"Platform: {sys.platform}")
    print()
    print("Checking prerequisites:")
    liblouis_ok = check_liblouis()
    espeak_ok = check_espeak()
    voices_ok = check_voices()

    print_install_instructions(liblouis_ok, espeak_ok, voices_ok)

    if not (liblouis_ok and espeak_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
