"""Braille table discovery service."""

import logging
import os
from pathlib import Path

from speech2braille.config import BrailleConfig
from speech2braille.models.braille import BrailleTable

logger = logging.getLogger(__name__)


class TableService:
    """Service for discovering and parsing braille tables."""

    def __init__(self, config: BrailleConfig) -> None:
        self.config = config

    def get_table_directories(self) -> list[Path]:
        """Get list of directories where liblouis tables are stored."""
        directories = []

        # Check configured paths
        for path_str in self.config.table_directories:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                directories.append(path)

        # Also check user local path
        user_local = Path.home() / ".local/share/liblouis/tables"
        if user_local.exists() and user_local.is_dir():
            directories.append(user_local)

        # Also check LOUIS_TABLEPATH environment variable
        env_path = os.environ.get("LOUIS_TABLEPATH")
        if env_path:
            for path_str in env_path.split(":"):
                path = Path(path_str)
                if path.exists() and path.is_dir() and path not in directories:
                    directories.append(path)

        return directories

    @staticmethod
    def parse_table_metadata(table_file: Path) -> dict:
        """Parse metadata from a liblouis table file."""
        metadata = {
            "display_name": None,
            "language": None,
        }

        try:
            with open(table_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#-display-name:"):
                        metadata["display_name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("#-language:"):
                        metadata["language"] = line.split(":", 1)[1].strip()
                    # Stop after reading header lines
                    if metadata["display_name"] and metadata["language"]:
                        break
        except Exception:
            pass

        return metadata

    @staticmethod
    def infer_metadata_from_filename(filename: str) -> dict:
        """Infer metadata from table filename when metadata headers are missing."""
        metadata = {
            "display_name": filename,
            "language": "unknown",
            "grade": None,
        }

        # Extract language code (usually first 2-3 chars before hyphen)
        parts = filename.replace(".ctb", "").replace(".utb", "").split("-")
        if len(parts) >= 1:
            metadata["language"] = parts[0]

        # Detect grade
        if "-g1" in filename or "_g1" in filename:
            metadata["grade"] = "g1"
            metadata["display_name"] = f"{parts[0].upper()} Grade 1"
        elif "-g2" in filename or "_g2" in filename:
            metadata["grade"] = "g2"
            metadata["display_name"] = f"{parts[0].upper()} Grade 2"

        # Common language names
        lang_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "pl": "Polish",
            "cs": "Czech",
            "ru": "Russian",
            "ar": "Arabic",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
        }

        if metadata["language"] in lang_names:
            base_name = lang_names[metadata["language"]]
            if metadata["grade"]:
                metadata["display_name"] = f"{base_name} Grade {metadata['grade'][1]}"
            else:
                metadata["display_name"] = base_name

        return metadata

    def list_tables(self) -> list[BrailleTable]:
        """List all available braille translation tables."""
        tables = []
        seen_filenames: set[str] = set()

        for directory in self.get_table_directories():
            for table_file in directory.glob("*.ctb"):
                filename = table_file.name

                # Skip if already seen (prioritize first occurrence)
                if filename in seen_filenames:
                    continue
                seen_filenames.add(filename)

                # Parse metadata from file
                file_metadata = self.parse_table_metadata(table_file)

                # Use filename inference as fallback
                inferred = self.infer_metadata_from_filename(filename)

                tables.append(
                    BrailleTable(
                        filename=filename,
                        display_name=file_metadata["display_name"] or inferred["display_name"],
                        language=file_metadata["language"] or inferred["language"],
                        grade=inferred.get("grade"),
                    )
                )

        # Sort by display name
        tables.sort(key=lambda t: t.display_name)

        return tables
