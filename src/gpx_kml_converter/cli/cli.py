"""Auto-generated CLI interface for gpx-kml-converter project.

This file was generated from config.py parameter definitions.
Do not modify manually - regenerate using ConfigParameterManager CLI generation methods.

run cli: python -m gpx_kml_converter.cli
"""

import argparse
import traceback
from pathlib import Path
from typing import Any

from gpx_kml_converter.config.config import ConfigParameterManager
from gpx_kml_converter.core.base import BaseGPXProcessor
from gpx_kml_converter.core.logging import initialize_logging


def parse_arguments():
    """Parse command line arguments with config file support."""
    parser = argparse.ArgumentParser(
        description="Process input files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m gpx_kml_converter.cli input.txt
  python -m gpx_kml_converter.cli --output result.txt input.txt
  python -m gpx_kml_converter.cli --config custom_config.yaml input.txt
        """,
    )

    # Config file argument
    parser.add_argument(
        "--config",
        default=None,
        help="Path to configuration file (JSON or YAML)",
    )

    # Verbose/quiet options for log level override
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Enable quiet mode (WARNING level only)"
    )

    # Get CLI parameters from ConfigParameterManager
    config_manager = ConfigParameterManager()
    cli_params = config_manager.get_cli_parameters()

    # Generate arguments from CLI config parameters
    for param in cli_params:
        if param.required and param.cli_arg is None:
            # Positional argument (like 'input')
            parser.add_argument(param.name, help=param.help)
        else:
            # Optional argument
            kwargs = {
                "default": argparse.SUPPRESS,  # Don't set default here, handle in config
                "help": f"{param.help} (default: {param.default})",
            }

            # Handle different parameter types
            if param.choices and not param.type_ == bool:
                kwargs["choices"] = param.choices

            if param.type_ == int:
                kwargs["type"] = int
            if param.type_ == float:
                kwargs["type"] = float
            elif param.type_ == bool:
                kwargs["action"] = "store_true" if not param.default else "store_false"
                kwargs["help"] = f"{param.help} (default: {param.default})"
            elif param.type_ == str:
                kwargs["type"] = str

            parser.add_argument(param.cli_arg, **kwargs)

    return parser.parse_args()


def create_config_overrides(args: argparse.Namespace) -> dict[str, Any]:
    """Create configuration overrides from CLI arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Dictionary with CLI parameter overrides in format cli__parameter_name
    """
    config_manager = ConfigParameterManager()
    cli_params = config_manager.get_cli_parameters()
    overrides = {}

    for param in cli_params:
        if hasattr(args, param.name):
            arg_value = getattr(args, param.name)
            # Add CLI category prefix for override system
            overrides[f"cli__{param.name}"] = arg_value

    # Handle log level overrides from verbose/quiet flags
    if hasattr(args, "verbose") and args.verbose:
        overrides["app__log_level"] = "DEBUG"
    elif hasattr(args, "quiet") and args.quiet:
        overrides["app__log_level"] = "WARNING"

    return overrides


def validate_config(config: ConfigParameterManager, logger) -> bool:
    """Validate the configuration parameters.

    Args:
        config: Configuration manager instance
        logger: Logger instance for error reporting

    Returns:
        True if configuration is valid, False otherwise
    """
    # Check required parameters
    if not config.cli.input.default:
        logger.error("Input is required")
        return False

    # Check if input file exists
    input_path = Path(config.cli.input.default)
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return False

    logger.debug(f"Input file validation passed: {input_path}")
    return True


def main():
    """Main entry point for the CLI application."""
    logger = None

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Create configuration overrides from CLI arguments
        cli_overrides = create_config_overrides(args)

        # Create config object with file and CLI overrides
        config = ConfigParameterManager(
            config_file=args.config if hasattr(args, "config") and args.config else None,
            **cli_overrides,
        )

        # Initialize logging system
        logger_manager = initialize_logging(config)
        logger = logger_manager.get_logger()

        # Log startup information
        logger.info("Starting gpx_kml_converter CLI")
        logger.debug(f"Command line arguments: {vars(args)}")
        logger_manager.log_config_summary()

        # Validate configuration
        if not validate_config(config, logger):
            logger.error("Configuration validation failed")
            return 1

        logger.info(f"Processing input: {config.cli.input.default}")

        # Create and run BaseGPXProcessor
        project = BaseGPXProcessor(
            config.cli.input.default,
            config.cli.output.default,
            config.cli.min_dist.default,
            config.cli.extract_waypoints.default,
            config.app.date_format.default,
        )

        logger.info("Starting conversion process")

        project.compress_files()

        logger.info(f"Successfully processed: {config.cli.input.default}")
        if config.cli.output.default:
            logger.info(f"Output written to: {config.cli.output.default}")

        logger.info("CLI processing completed successfully")
        return 0

    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}")
            logger.debug("Full traceback:", exc_info=True)
        else:
            print(f"Error: {e}")
            traceback.print_exc()
        return 1

    except KeyboardInterrupt:
        if logger:
            logger.warning("Process interrupted by user")
        else:
            print("Process interrupted by user")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}")
            logger.debug("Full traceback:", exc_info=True)
        else:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
