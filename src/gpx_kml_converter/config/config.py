"""Central configuration management for python-template-project project.

This module provides a single source of truth for all configuration parameters
organized in categories (CLI, App, GUI). It can generate config files, CLI modules,
and documentation from the parameter definitions.
"""

from config_cli_gui.config_framework import (
    BaseConfigCategory,
    CliConfigCategory,
    ConfigManager,
    ConfigParameter,
    DocumentationGenerator,
)


class CliConfig(CliConfigCategory):
    """CLI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "cli"

    # Positional argument
    input: ConfigParameter = ConfigParameter(
        name="input",
        default="",
        type_=str,
        help="Path to input (file or folder)",
        required=True,
        cli_arg=None,  # Positional argument
    )

    # Optional CLI arguments
    output: ConfigParameter = ConfigParameter(
        name="output",
        default="",
        type_=str,
        help="Path to output destination",
    )

    min_dist: ConfigParameter = ConfigParameter(
        name="min_dist",
        default=20,
        type_=int,
        help="Maximum distance between two waypoints",
    )

    extract_waypoints: ConfigParameter = ConfigParameter(
        name="extract_waypoints",
        default=True,
        type_=bool,
        help="Extract starting points of each track as waypoint",
    )

    elevation: ConfigParameter = ConfigParameter(
        name="elevation",
        default=True,
        type_=bool,
        help="Include elevation data in waypoints",
    )


class AppConfig(BaseConfigCategory):
    """Application-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "app"

    date_format: ConfigParameter = ConfigParameter(
        name="date_format",
        default="%Y-%m-%d",
        type_=str,
        help="Date format to use",
    )

    log_level: ConfigParameter = ConfigParameter(
        name="log_level",
        default="INFO",
        type_=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the application",
    )

    log_file_max_size: ConfigParameter = ConfigParameter(
        name="log_file_max_size",
        default=10,
        type_=int,
        help="Maximum log file size in MB before rotation",
    )

    log_backup_count: ConfigParameter = ConfigParameter(
        name="log_backup_count",
        default=5,
        type_=int,
        help="Number of backup log files to keep",
    )

    log_format: ConfigParameter = ConfigParameter(
        name="log_format",
        default="detailed",
        type_=str,
        choices=["simple", "detailed", "json"],
        help="Log message format style",
    )

    max_workers: ConfigParameter = ConfigParameter(
        name="max_workers",
        default=4,
        type_=int,
        help="Maximum number of worker threads",
    )

    enable_file_logging: ConfigParameter = ConfigParameter(
        name="enable_file_logging",
        default=True,
        type_=bool,
        help="Enable logging to file",
    )

    enable_console_logging: ConfigParameter = ConfigParameter(
        name="enable_console_logging",
        default=True,
        type_=bool,
        help="Enable logging to console",
    )


class GuiConfig(BaseConfigCategory):
    """GUI-specific configuration parameters."""

    def get_category_name(self) -> str:
        return "gui"

    theme: ConfigParameter = ConfigParameter(
        name="theme",
        default="light",
        type_=str,
        choices=["light", "dark", "auto"],
        help="GUI theme setting",
    )

    window_width: ConfigParameter = ConfigParameter(
        name="window_width",
        default=800,
        type_=int,
        help="Default window width",
    )

    window_height: ConfigParameter = ConfigParameter(
        name="window_height",
        default=600,
        type_=int,
        help="Default window height",
    )

    log_window_height: ConfigParameter = ConfigParameter(
        name="log_window_height",
        default=200,
        type_=int,
        help="Height of the log window in pixels",
    )

    auto_scroll_log: ConfigParameter = ConfigParameter(
        name="auto_scroll_log",
        default=True,
        type_=bool,
        help="Automatically scroll to newest log entries",
    )

    max_log_lines: ConfigParameter = ConfigParameter(
        name="max_log_lines",
        default=1000,
        type_=int,
        help="Maximum number of log lines to keep in GUI",
    )


class ConfigParameterManager(ConfigManager):  # Inherit from ConfigManager
    """Main configuration manager that handles all parameter categories."""

    def __init__(self, config_file: str | None = None, **kwargs):
        # Erst den Parent initialisieren
        super().__init__(config_file, **kwargs)

        # Dann die Kategorien hinzufügen
        self.add_category("cli", CliConfig())
        self.add_category("app", AppConfig())
        self.add_category("gui", GuiConfig())


def main():
    """Main function to generate config file and documentation."""
    default_config: str = "../../config.yaml"
    default_cli_doc: str = "../../docs/usage/cli.md"
    default_config_doc: str = "../../docs/usage/config.md"
    config_manager = ConfigParameterManager()
    docGen = DocumentationGenerator(config_manager)
    docGen.generate_default_config_file(output_file=default_config)
    print(f"Generated: {default_config}")

    docGen.generate_config_markdown_doc(output_file=default_config_doc)
    print(f"Generated: {default_config_doc}")

    docGen.generate_cli_markdown_doc(output_file=default_cli_doc, app_name="gpx_kml_converter.cli")
    print(f"Generated: {default_cli_doc}")


if __name__ == "__main__":
    main()
