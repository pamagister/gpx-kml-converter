import math
import os
import stat
import tempfile
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPX, GPXWaypoint, GPXXMLSyntaxException

from gpx_kml_converter.core import logging


def add_poi_to_gpx(
    input_path: str | Path,
    output_path: str | Path,
    latitude: float,
    longitude: float,
    name: str,
    description: str | None = None,
    symbol: str | None = None,
    elevation: float | None = None,
) -> Path:
    """Append a waypoint to a GPX file, creating the document if it is missing."""
    source = Path(input_path)
    destination = Path(output_path)
    if source.suffix.lower() != ".gpx" or destination.suffix.lower() != ".gpx":
        raise ValueError("The input and output paths must have a .gpx extension.")
    if source.exists() and not source.is_file():
        raise ValueError(f"Input path is not a regular file: {source}")
    if destination.exists() and not destination.is_file():
        raise ValueError(f"Output path is not a regular file: {destination}")
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be a finite number between -90 and 90.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be a finite number between -180 and 180.")
    if elevation is not None and not math.isfinite(elevation):
        raise ValueError("Elevation must be a finite number.")
    if not name.strip():
        raise ValueError("POI name must not be empty.")

    if source.exists():
        try:
            with source.open("r", encoding="utf-8") as gpx_file:
                gpx = gpxpy.parse(gpx_file)
        except GPXXMLSyntaxException as error:
            raise ValueError(f"Input is not a valid GPX document: {source}") from error
        if not isinstance(gpx, GPX):
            raise ValueError(f"Input is not a valid GPX document: {source}")
    else:
        gpx = GPX()

    gpx.waypoints.append(
        GPXWaypoint(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            name=name,
            description=description,
            symbol=symbol,
        )
    )

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(gpx.to_xml())

        if destination.exists():
            os.chmod(temporary_path, stat.S_IMODE(destination.stat().st_mode))
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return destination


class GpxFiles:
    def __init__(self, logger: logging.LoggerManager = None):
        self.logger = logger
        self.gpx_files: dict[Path:GPX] = {}

    def add_file(self, file_path: str | Path | list[str]) -> None:
        pass
