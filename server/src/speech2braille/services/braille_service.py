"""Braille translation service using liblouis."""

import logging
import sys

from liblouis_bridge import louis
from speech2braille.config import BrailleConfig

logger = logging.getLogger(__name__)


class BrailleService:
    """Service for braille translation using liblouis."""

    def __init__(self, config: BrailleConfig) -> None:
        self.config = config
        self._verify_louis_installation()

    def _verify_louis_installation(self) -> None:
        """Verify that liblouis is properly installed and accessible."""
        try:
            version = louis.version()
            logger.info(f"liblouis version {version} loaded successfully")
        except Exception as e:
            if sys.platform == "darwin":
                hint = (
                    "On macOS, ensure:\n"
                    "1. brew install liblouis\n"
                    "2. The louis package is in src/liblouis_bridge/\n"
                    "3. DYLD_LIBRARY_PATH includes /opt/homebrew/lib if needed"
                )
            elif sys.platform == "win32":
                hint = (
                    "On Windows, ensure:\n"
                    "1. Download liblouis from https://github.com/liblouis/liblouis/releases\n"
                    "2. Set LIBLOUIS_DIR to the install path\n"
                    "   Or install via MSYS2: pacman -S mingw-w64-x86_64-liblouis"
                )
            else:
                hint = (
                    "On Linux, ensure:\n"
                    "1. sudo apt install liblouis-dev liblouis-data\n"
                    "   Or: sudo dnf install liblouis-devel liblouis-utils"
                )
            raise RuntimeError(f"Failed to load liblouis: {e}\n{hint}") from e

    @property
    def default_table(self) -> str:
        return self.config.default_table

    @staticmethod
    def get_version() -> str:
        """Get the liblouis version string."""
        return louis.version()

    def translate(self, text: str, table: str | None = None) -> str:
        """Translate text to braille.

        Args:
            text: Text to translate
            table: Braille table filename (uses default if not specified)

        Returns:
            Unicode braille string
        """
        table = table or self.default_table
        braille_output = louis.translate([table], text, mode=louis.dotsIO | louis.ucBrl)

        # Extract the Unicode braille string from the tuple
        braille = braille_output[0] if isinstance(braille_output, tuple) else braille_output
        return braille

    def back_translate(self, braille: str, table: str | None = None) -> str:
        """Back-translate braille to text.

        Args:
            braille: Braille text to translate back
            table: Braille table filename (uses default if not specified)

        Returns:
            Text string
        """
        table = table or self.default_table
        return louis.backTranslateString([table], braille)
