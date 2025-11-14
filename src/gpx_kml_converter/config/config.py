"""Central configuration management for config-cli-gui project.

This module provides a single source of truth for all configuration parameters
organized in categories (CLI, App, GUI). It can generate config files, CLI modules,
and documentation from the parameter definitions.
"""

from config_cli_gui.config import (
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
)
from config_cli_gui.docs import DocumentationGenerator


class CliConfig(ConfigCategory):
    """CLI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "cli"

    # Positional argument
    input: ConfigParameter = ConfigParameter(
        name="input",
        value="",
        help="Path to input (file or folder)",
        required=True,
        is_cli=True,
    )

    # Optional CLI arguments
    output: ConfigParameter = ConfigParameter(
        name="output",
        value="",
        help="Path to output destination",
        is_cli=True,
    )

    min_dist: ConfigParameter = ConfigParameter(
        name="min_dist",
        value=20,
        help="Maximum distance between two waypoints",
        is_cli=True,
    )

    extract_waypoints: ConfigParameter = ConfigParameter(
        name="extract_waypoints",
        value=True,
        help="Extract starting points of each track as waypoint",
        is_cli=True,
    )

    elevation: ConfigParameter = ConfigParameter(
        name="elevation",
        value=True,
        help="Include elevation data in waypoints",
        is_cli=True,
    )


class AppConfig(ConfigCategory):
    """Application-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "app"

    date_format: ConfigParameter = ConfigParameter(
        name="date_format",
        value="%Y-%m-%d",
        help="Date format to use",
    )

    log_level: ConfigParameter = ConfigParameter(
        name="log_level",
        value="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the application",
    )

    log_file_max_size: ConfigParameter = ConfigParameter(
        name="log_file_max_size",
        value=10,
        help="Maximum log file size in MB before rotation",
    )

    log_backup_count: ConfigParameter = ConfigParameter(
        name="log_backup_count",
        value=5,
        help="Number of backup log files to keep",
    )

    log_format: ConfigParameter = ConfigParameter(
        name="log_format",
        value="detailed",
        choices=["simple", "detailed", "json"],
        help="Log message format style",
    )

    max_workers: ConfigParameter = ConfigParameter(
        name="max_workers",
        value=4,
        help="Maximum number of worker threads",
    )

    enable_file_logging: ConfigParameter = ConfigParameter(
        name="enable_file_logging",
        value=True,
        help="Enable logging to file",
    )

    enable_console_logging: ConfigParameter = ConfigParameter(
        name="enable_console_logging",
        value=True,
        help="Enable logging to console",
    )


class GuiConfig(ConfigCategory):
    """GUI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "gui"

    theme: ConfigParameter = ConfigParameter(
        name="theme",
        value="light",
        choices=["light", "dark", "auto"],
        help="GUI theme setting",
    )

    window_width: ConfigParameter = ConfigParameter(
        name="window_width",
        value=800,
        help="Default window width",
    )

    window_height: ConfigParameter = ConfigParameter(
        name="window_height",
        value=600,
        help="Default window height",
    )

    log_window_height: ConfigParameter = ConfigParameter(
        name="log_window_height",
        value=200,
        help="Height of the log window in pixels",
    )

    auto_scroll_log: ConfigParameter = ConfigParameter(
        name="auto_scroll_log",
        value=True,
        help="Automatically scroll to newest log entries",
    )

    max_log_lines: ConfigParameter = ConfigParameter(
        name="max_log_lines",
        value=1000,
        help="Maximum number of log lines to keep in GUI",
    )


class ProjectConfigManager(ConfigManager):  # Inherit from ConfigManager
    """Main configuration manager that handles all parameter categories."""

    cli: CliConfig
    app: AppConfig
    gui: GuiConfig

    def __init__(self, config_file: str | None = None, **kwargs):
        """Initialize the configuration manager with all parameter categories."""
        categories = (CliConfig(), AppConfig(), GuiConfig())
        super().__init__(categories, config_file, **kwargs)


def main():
    """Main function to generate config file and documentation."""
    default_config: str = "config.yaml"
    default_cli_doc: str = "docs/usage/cli.md"
    default_config_doc: str = "docs/usage/config.md"
    app_name = "gpx_kml_converter"
    _config = ProjectConfigManager()
    doc_gen = DocumentationGenerator(_config)
    doc_gen.generate_default_config_file(output_file=default_config)
    print(f"Generated: {default_config}")

    doc_gen.generate_config_markdown_doc(output_file=default_config_doc)
    print(f"Generated: {default_config_doc}")

    doc_gen.generate_cli_markdown_doc(output_file=default_cli_doc, app_name=app_name)
    print(f"Generated: {default_cli_doc}")


if __name__ == "__main__":
    main()
