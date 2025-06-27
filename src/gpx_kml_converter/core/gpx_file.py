from pathlib import Path

from gpxpy.gpx import GPX

from gpx_kml_converter.core import logging


class GpxFiles:
    def __init__(self, logger: logging.LoggerManager = None):
        self.logger = logger
        self.gpx_files: dict[Path:GPX] = {}

    def add_file(self, file_path: str | Path | list[str]) -> None:
        pass
