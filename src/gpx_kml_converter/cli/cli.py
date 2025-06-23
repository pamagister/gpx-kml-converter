"""CLI interface for python-template-project using the generic config framework.

This file uses the CliGenerator from the generic config framework.
"""

from pathlib import Path

from config_cli_gui.cli import CliGenerator

from gpx_kml_converter.config.config import ProjectConfigManager
from gpx_kml_converter.core.base import BaseGPXProcessor
from gpx_kml_converter.core.logging import initialize_logging


def validate_config(config: ProjectConfigManager, logger) -> bool:
    """Validate the configuration parameters.

    Args:
        config: Configuration manager instance
        logger: Logger instance for error reporting

    Returns:
        True if configuration is valid, False otherwise
    """
    # Get CLI category and check required parameters
    cli_category = config.get_category("cli")
    if not cli_category:
        logger.error("No CLI configuration found")
        return False

    # Check if input parameter exists and has a value
    input_param = getattr(cli_category, "input", None)
    if not input_param or not input_param.default:
        logger.error("Input is required")
        return False

    # Check if input file exists
    input_path = Path(input_param.default)
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return False

    logger.debug(f"Input file validation passed: {input_path}")
    return True


def run_main_processing(config: ProjectConfigManager) -> int:
    """Main processing function that gets called by the CLI generator.

    Args:
        config: Configuration manager with all settings

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Initialize logging system
    logger_manager = initialize_logging(config)
    logger = logger_manager.get_logger("python_template_project.cli")

    try:
        # Log startup information
        logger.info("Starting python_template_project CLI")
        logger_manager.log_config_summary()

        # Validate configuration
        if not validate_config(config, logger):
            logger.error("Configuration validation failed")
            return 1

        # Get CLI parameters
        cli_category = config.get_category("cli")
        input_file = cli_category.input.default
        output_file = cli_category.output.default
        min_dist = cli_category.min_dist.default
        extract_waypoints = cli_category.extract_waypoints.default

        # Get app parameters
        app_category = config.get_category("app")
        date_format = app_category.date_format.default if app_category else "%Y-%m-%d"

        logger.info(f"Processing input: {input_file}")

        # Create and run BaseGPXProcessor
        processor = BaseGPXProcessor(
            input_=input_file,
            output=output_file,
            min_dist=min_dist,
            date_format=date_format,
            elevation=extract_waypoints,
            logger=logger,
        )

        logger.info("Starting conversion process")

        # Run the processing (adjust method name based on your actual implementation)
        result_files = processor.compress_files()

        logger.info(f"Successfully processed: {input_file}")
        if output_file:
            logger.info(f"Output written to: {output_file}")
        if result_files:
            logger.info(f"Generated files: {', '.join(result_files)}")

        logger.info("CLI processing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def main():
    """Main entry point for the CLI application."""
    # Create the base configuration manager
    config_manager = ProjectConfigManager()

    # Create CLI generator
    cli_generator = CliGenerator(config_manager=config_manager, app_name="python_template_project")

    # Run the CLI with our main processing function
    return cli_generator.run_cli(
        main_function=run_main_processing,
        description="Process GPX files with various operations like compression, "
        "merging, and POI extraction",
        validator=validate_config,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
