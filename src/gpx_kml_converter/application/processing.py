"""Shared orchestration for GPX processing operations."""

import logging
from collections.abc import Sequence
from pathlib import Path

from gpxpy.gpx import GPX

from gpx_kml_converter.core.base import BaseGPXProcessor

PROCESSING_MODES = ("compress", "merge", "extract-pois")


def process_gpx_files(
    input_files: Sequence[GPX],
    *,
    mode: str,
    output: str | Path | None,
    tolerance: float,
    date_format: str,
    elevation: bool,
    logger: logging.Logger,
) -> dict[Path, GPX]:
    """Run one of the shared GPX operations and return its generated files."""
    if mode not in PROCESSING_MODES:
        raise ValueError(f"Unsupported processing mode: {mode}")

    processor = BaseGPXProcessor(
        input_=list(input_files),
        output=output,
        tolerance=tolerance,
        date_format=date_format,
        elevation=elevation,
        logger=logger,
    )
    operation = {
        "compress": processor.compress_files,
        "merge": processor.merge_files,
        "extract-pois": processor.extract_pois,
    }[mode]
    return operation()
