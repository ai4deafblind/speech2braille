"""Braille translation service using liblouis."""

import logging

import louis

from speech2braille.config import BrailleConfig

logger = logging.getLogger(__name__)


class BrailleService:
    """Service for braille translation using liblouis."""

    def __init__(self, config: BrailleConfig) -> None:
        self.config = config

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
