"""Command-line interface for processing GPX and KML files."""

import argparse
import math
from pathlib import Path

from gpx_kml_converter.application.processing import (
    PROCESSING_MODES as GPX_PROCESSING_MODES,
)
from gpx_kml_converter.application.processing import (
    process_gpx_files,
)
from gpx_kml_converter.config.config import ConfigParameterManager
from gpx_kml_converter.core.base import GeoFileManager
from gpx_kml_converter.core.gpx_file import add_poi_to_gpx
from gpx_kml_converter.core.logging import initialize_logging

SUPPORTED_INPUTS = {".gpx", ".kml", ".zip"}
PROCESSING_MODES = (*GPX_PROCESSING_MODES, "add-poi")


def _parse_bool(value: str) -> bool:
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress, merge, or extract POIs from GPX/KML files, or add a GPX waypoint."
    )
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Show warnings and errors only")
    parser.add_argument(
        "--mode",
        choices=PROCESSING_MODES,
        default=argparse.SUPPRESS,
        help="Processing operation (default: compress)",
    )
    parser.add_argument(
        "--output",
        default=argparse.SUPPRESS,
        help="Output directory, or output GPX file in add-poi mode",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=argparse.SUPPRESS,
        help="Douglas-Peucker simplification tolerance in meters (default: 10)",
    )
    parser.add_argument(
        "--elevation",
        nargs="?",
        const=True,
        type=_parse_bool,
        default=argparse.SUPPRESS,
        help="Add SRTM elevation to extracted waypoints; optionally pass true or false",
    )
    parser.add_argument("--lat", type=float, help="Latitude of the waypoint (add-poi mode)")
    parser.add_argument("--lon", type=float, help="Longitude of the waypoint (add-poi mode)")
    parser.add_argument("--name", help="Name of the waypoint (add-poi mode)")
    parser.add_argument("--desc", help="Description of the waypoint (add-poi mode)")
    parser.add_argument("--sym", help="Symbol of the waypoint (add-poi mode)")
    parser.add_argument(
        "--ele", type=float, help="Elevation of the waypoint in meters (add-poi mode)"
    )
    recursion = parser.add_mutually_exclusive_group()
    recursion.add_argument(
        "--recursive",
        dest="recursive",
        nargs="?",
        const=True,
        type=_parse_bool,
        default=argparse.SUPPRESS,
        help="Search input directories recursively (optionally true or false)",
    )
    recursion.add_argument(
        "--no-recursive", dest="recursive", action="store_false", default=argparse.SUPPRESS
    )
    parser.add_argument(
        "input",
        nargs="+",
        metavar="INPUT",
        help="One or more GPX/KML/ZIP files or directories",
    )
    return parser


def _expand_inputs(inputs: list[str], recursive: bool) -> list[Path]:
    expanded: list[Path] = []
    seen: set[Path] = set()

    for input_value in inputs:
        path = Path(input_value)
        if not path.exists():
            raise ValueError(f"Input path does not exist: {path}")
        if path.is_dir():
            candidates = path.rglob("*") if recursive else path.iterdir()
            paths = sorted(candidate for candidate in candidates if candidate.is_file())
        elif path.is_file():
            paths = [path]
        else:
            raise ValueError(f"Input path is not a regular file or directory: {path}")

        supported = [item for item in paths if item.suffix.lower() in SUPPORTED_INPUTS]
        if path.is_file() and not supported:
            raise ValueError(f"Unsupported input type: {path}")
        for candidate in supported:
            normalized = candidate.resolve()
            if normalized not in seen:
                seen.add(normalized)
                expanded.append(normalized)

    if not expanded:
        raise ValueError("No GPX, KML, or ZIP files found in the provided inputs.")
    return expanded


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose and args.quiet:
        parser.error("--verbose and --quiet cannot be used together")

    config_manager = ConfigParameterManager(config_file=args.config)
    cli_overrides = {"cli__input": args.input}
    for name in ("mode", "output", "tolerance", "elevation", "recursive"):
        if hasattr(args, name):
            cli_overrides[f"cli__{name}"] = getattr(args, name)
    if args.verbose:
        cli_overrides["app__log_level"] = "DEBUG"
    elif args.quiet:
        cli_overrides["app__log_level"] = "WARNING"
    config_manager.apply_overrides(cli_overrides)

    mode = config_manager.cli.mode.value
    if mode == "add-poi":
        if len(args.input) != 1:
            parser.error("add-poi requires exactly one GPX input path")
        if args.lat is None or args.lon is None or args.name is None:
            parser.error("add-poi requires --lat, --lon, and --name")
        if Path(args.input[0]).suffix.lower() != ".gpx":
            parser.error("add-poi accepts only a .gpx input path")

    logger_manager = initialize_logging(config_manager)
    logger = logger_manager.get_logger("cli")

    try:
        if mode not in PROCESSING_MODES:
            raise ValueError(f"Unsupported processing mode in configuration: {mode}")
        if mode == "add-poi":
            input_path = Path(args.input[0])
            output_path = Path(args.output) if hasattr(args, "output") else input_path
            saved_path = add_poi_to_gpx(
                input_path=input_path,
                output_path=output_path,
                latitude=args.lat,
                longitude=args.lon,
                name=args.name,
                description=args.desc,
                symbol=args.sym,
                elevation=args.ele,
            )
            logger.info(f"POI added successfully. Output written to: {saved_path}")
            return 0

        input_paths = _expand_inputs(args.input, config_manager.cli.recursive.value)
        tolerance = config_manager.cli.tolerance.value
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("--tolerance must be a finite, non-negative number of meters.")

        loaded_files = GeoFileManager(logger=logger).load_files(input_paths)
        if not loaded_files:
            raise ValueError("No valid GPX or KML data could be loaded.")

        logger.info(f"Loaded {len(loaded_files)} input files.")
        result_files = process_gpx_files(
            list(loaded_files.values()),
            mode=mode,
            output=config_manager.cli.output.value,
            tolerance=tolerance,
            date_format=config_manager.app.date_format.value,
            elevation=config_manager.cli.elevation.value,
            logger=logger,
        )
        if not result_files:
            raise RuntimeError(f"The {mode} operation did not produce any output files.")

        logger.info(f"Processing completed successfully: {len(result_files)} output file(s).")
        for output_path in result_files:
            logger.info(f"Output written to: {output_path}")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        logger.error(f"Processing failed: {error}")
        return 1
    finally:
        logger_manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
