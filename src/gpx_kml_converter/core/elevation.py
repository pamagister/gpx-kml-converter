"""Elevation lookup boundary and deterministic fallback policy."""

import logging
from typing import Protocol

from gpxpy.gpx import GPXTrackPoint, GPXWaypoint


class ElevationProvider(Protocol):
    """Source of elevation values in meters."""

    def get_elevation(self, latitude: float, longitude: float) -> float | None:
        """Return an elevation, or ``None`` when no value is available."""


class SRTMElevationProvider:
    """Adapter for the optional srtm-py package."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._data = None
        try:
            import srtm

            self._data = srtm.get_data()
            self.logger.info("SRTM elevation data initialized.")
        except ImportError:
            self.logger.warning("SRTM library not available.")
        except Exception as error:
            self.logger.warning(f"SRTM elevation data unavailable: {error}")

    def get_elevation(self, latitude: float, longitude: float) -> float | None:
        if self._data is None:
            return None
        try:
            return self._data.get_elevation(latitude, longitude)
        except Exception as error:
            self.logger.warning(f"SRTM lookup failed for point ({latitude}, {longitude}): {error}")
            return None


class ElevationService:
    """Apply a provider and the application's stable source-value fallback."""

    def __init__(
        self,
        provider: ElevationProvider | None,
        enabled: bool,
    ):
        self.provider = provider
        self.enabled = enabled

    def get_adjusted_elevation(self, point: GPXTrackPoint | GPXWaypoint) -> float | None:
        if not self.enabled:
            return None

        if self.provider is not None:
            elevation = self.provider.get_elevation(point.latitude, point.longitude)
            if elevation is not None:
                return round(elevation, 1)

        original_elevation = point.elevation if point.elevation is not None else 0
        return round(original_elevation, 1)
