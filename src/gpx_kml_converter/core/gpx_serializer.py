"""GPX serialization to output files."""

import logging
import traceback
from pathlib import Path

from gpxpy.gpx import GPX


class GPXSerializer:
    """Write GPX objects to disk and report output sizes."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def save(
        self,
        gpx: GPX,
        output_path: Path,
        original_file_path: Path | None = None,
    ) -> Path | None:
        try:
            output_path.write_text(gpx.to_xml(), encoding="utf-8")
            if original_file_path and original_file_path.exists():
                size_kb = original_file_path.stat().st_size / 1024
                self.logger.info(f"Original file size: {size_kb:.2f} KB")
            self.logger.info(f"Processed file size: {output_path.stat().st_size / 1024:.2f} KB")
            return output_path
        except (OSError, ValueError):
            self.logger.exception(f"Error saving GPX file {output_path.name}")
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return None
