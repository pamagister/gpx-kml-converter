"""Compatibility exports for the historical core.base module."""

from gpx_kml_converter.core.file_loader import GeoFileManager
from gpx_kml_converter.core.processor import NAME, BaseGPXProcessor

__all__ = ["BaseGPXProcessor", "GeoFileManager", "NAME"]
