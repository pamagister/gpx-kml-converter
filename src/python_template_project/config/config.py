"""Central configuration management for python-template-project project.

This module provides a single source of truth for all configuration parameters
organized in categories (CLI, App, GUI). It can generate config files, CLI modules,
and documentation from the parameter definitions.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml  # type: ignore
from pydantic import BaseModel  # type: ignore


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter with all its metadata."""

    name: str
    default: Any
    type_: type
    choices: list[str | bool | int] | None = None
    help: str = ""
    cli_arg: str | None = None
    required: bool = False

    def __post_init__(self):
        if self.cli_arg is None and not self.required:
            self.cli_arg = f"--{self.name}"
        if self.type_ is bool:
            self.choices = [True, False]


class CliConfig(BaseModel):
    """CLI-specific configuration parameters."""

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


class AppConfig(BaseModel):
    """Application-specific configuration parameters."""

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


class GuiConfig(BaseModel):
    """GUI-specific configuration parameters."""

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


class ConfigParameterManager(BaseModel):
    """Main configuration manager that handles all parameter categories."""

    cli: CliConfig = CliConfig()
    app: AppConfig = AppConfig()
    gui: GuiConfig = GuiConfig()

    def __init__(self, config_file: str | None = None, **kwargs):
        """Initialize configuration from file and/or keyword arguments.

        Args:
            config_file: Path to configuration file (JSON or YAML)
            **kwargs: Override parameters in format category__parameter (e.g., cli__output)
        """
        super().__init__()

        # Load from file if provided
        if config_file:
            self.load_from_file(config_file)

        # Override with provided kwargs
        self._apply_kwargs(kwargs)

    def _apply_kwargs(self, kwargs: dict[str, Any]):
        """Apply keyword arguments to override configuration values.

        Args:
            kwargs: Dictionary with keys in format 'category__parameter'
        """
        for key, value in kwargs.items():
            if "__" in key:
                category, param_name = key.split("__", 1)
                if hasattr(self, category):
                    category_obj = getattr(self, category)
                    if hasattr(category_obj, param_name):
                        param = getattr(category_obj, param_name)
                        param.default = value

    def load_from_file(self, config_file: str):
        """Load configuration from JSON or YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yml", ".yaml"]:
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)

        # Apply loaded configuration
        for category_name, category_data in config_data.items():
            if hasattr(self, category_name):
                category_obj = getattr(self, category_name)
                for param_name, param_value in category_data.items():
                    if hasattr(category_obj, param_name):
                        param = getattr(category_obj, param_name)
                        param.default = param_value

    def save_to_file(self, config_file: str, format_: str = "auto"):
        """Save current configuration to file.

        Args:
            config_file: Path to save configuration
            format_: Format to use ('json', 'yaml', or 'auto' to detect from extension)
        """
        config_path = Path(config_file)
        config_data = self.to_dict()

        # Determine format
        if format_ == "auto":
            format_ = "yaml" if config_path.suffix.lower() in [".yml", ".yaml"] else "json"

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            if format_ == "yaml":
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for category_name in self.model_fields.keys():
            category_obj = getattr(self, category_name)
            category_dict = {}
            for field_name in category_obj.model_fields:
                param = getattr(category_obj, field_name)
                category_dict[param.name] = param.default
            result[category_name] = category_dict
        return result

    def get_all_parameters(self) -> list[ConfigParameter]:
        """Get all parameters from all categories."""
        parameters = []
        for category_name in self.model_fields.keys():
            category_obj = getattr(self, category_name)
            for field_name in category_obj.model_fields:
                param = getattr(category_obj, field_name)
                parameters.append(param)
        return parameters

    def get_cli_parameters(self) -> list[ConfigParameter]:
        """Get only CLI parameters."""
        cli_params = []
        for field_name in type(self.cli).model_fields.keys():
            param = getattr(self.cli, field_name)
            cli_params.append(param)
        return cli_params

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging-specific configuration as dictionary.

        Returns:
            Dictionary with logging configuration parameters
        """
        return {
            "log_level": self.app.log_level.default,
            "log_file_max_size": self.app.log_file_max_size.default
            * 1024
            * 1024,  # Convert MB to bytes
            "log_backup_count": self.app.log_backup_count.default,
            "log_format": self.app.log_format.default,
            "enable_file_logging": self.app.enable_file_logging.default,
            "enable_console_logging": self.app.enable_console_logging.default,
            "max_log_lines": self.gui.max_log_lines.default,
            "auto_scroll_log": self.gui.auto_scroll_log.default,
        }

    @classmethod
    def generate_config_markdown_doc(cls, output_file: str):
        """Generate a Markdown documentation for all
        configuration parameters organized by category."""

        manager = cls()

        def pad(s, width):
            return s + " " * (width - len(s))

        markdown_content = dedent(
            """
            # Config parameters

            These parameters are available to configure the behavior of your application.
            The parameters in the cli category can be accessed via the command line interface.

            """
        ).lstrip()

        for category_name in cls.model_fields.keys():
            category_obj = getattr(manager, category_name)
            markdown_content += f'## Category "{category_name}"\n\n'

            # Collect all parameters for this category
            rows = []
            header = ["Name", "Type", "Description", "Default", "Choices"]

            for field_name in type(category_obj).model_fields.keys():
                param = getattr(category_obj, field_name)
                name = param.name
                typ = param.type_.__name__
                desc = param.help
                default = repr(param.default)
                choices = str(param.choices) if param.choices else "-"

                rows.append((name, typ, desc, default, choices))

            # Calculate column widths
            all_rows = [header] + rows
            widths = [max(len(str(col)) for col in column) for column in zip(*all_rows)]

            # Create Markdown table
            table = (
                "| "
                + " | ".join(pad(h, w) for h, w in zip(header, widths))
                + " |\n"
                + "|-"
                + "-|-".join("-" * w for w in widths)
                + "-|\n"
            )
            for row in rows:
                table += "| " + " | ".join(pad(str(col), w) for col, w in zip(row, widths)) + " |\n"

            markdown_content += table + "\n"

        # Write to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    @classmethod
    def generate_default_config_file(cls, output_file: str):
        """Generate a default configuration file with all parameters and their descriptions."""
        manager = cls()
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Configuration File\n")
            f.write("# This file was auto-generated. Modify as needed.\n\n")

            for category_name in cls.model_fields.keys():
                category_obj = getattr(manager, category_name)
                f.write(f"# {category_name.upper()} Configuration\n")
                f.write(f"{category_name}:\n")

                for field_name in type(category_obj).model_fields.keys():
                    param = getattr(category_obj, field_name)
                    f.write(f"  # {param.help}\n")
                    if param.choices:
                        f.write(f"  # Choices: {param.choices}\n")
                    f.write(f"  # Type: {param.type_.__name__}\n")
                    f.write(f"  {param.name}: {repr(param.default)}\n\n")

                f.write("\n")

    @classmethod
    def generate_cli_markdown_doc(cls, output_file: str):
        """Generate a Markdown CLI documentation with a formatted table and examples."""
        manager = cls()
        cli_params = manager.get_cli_parameters()

        rows = []
        required_params = []
        optional_params = []

        for param in cli_params:
            cli_arg = f"`--{param.name}`" if param.name != "input" else "`path/to/file`"
            typ = param.type_.__name__
            desc = param.help
            default = (
                "*required*"
                if param.required or param.default in (None, "")
                else repr(param.default)
            )
            choices = str(param.choices) if param.choices else "-"

            rows.append((cli_arg, typ, desc, default, choices))
            if default == "*required*":
                required_params.append(param)
            else:
                optional_params.append(param)

        # Dynamically determine column width
        def pad(s, width):
            return s + " " * (width - len(s))

        widths = [max(len(str(col)) for col in column) for column in zip(*rows)]
        header = ["Option", "Type", "Description", "Default", "Choices"]

        # Create Markdown table
        table = (
            "| "
            + " | ".join(pad(h, w) for h, w in zip(header, widths))
            + " |\n"
            + "|-"
            + "-|-".join("-" * w for w in widths)
            + "-|\n"
        )
        for row in rows:
            table += "| " + " | ".join(pad(str(col), w) for col, w in zip(row, widths)) + " |\n"

        # Generate example commands
        examples = []
        required_arg = required_params[0].name if required_params else "example.input"
        examples.append(
            dedent(
                f"""
        ### 1. Standard version (only required parameter)

        ```bash
        python -m python_template_project.cli {required_arg}
        ```
        """
            )
        )

        # Add logging examples
        examples.append(
            dedent(
                f"""
        ### 2. With verbose logging

        ```bash
        python -m python_template_project.cli --verbose {required_arg}
        ```
        """
            )
        )

        examples.append(
            dedent(
                f"""
        ### 3. With quiet mode

        ```bash
        python -m python_template_project.cli --quiet {required_arg}
        ```
        """
            )
        )

        for i in range(1, min(3, len(optional_params) + 1)):
            selected = [p for p in optional_params if p.name not in ["verbose", "quiet"]][:i]
            if selected:
                cli_part = " ".join(
                    f"--{p.name} {p.choices[0] if p.choices else p.default}" for p in selected
                )
                examples.append(
                    dedent(
                        f"""
                ### {i + 3}. Example with {i} Parameter(s)

                ```bash
                python -m python_template_project.cli {cli_part} {required_arg}
                ```
                """
                    )
                )

        markdown = dedent(
            """
        # Command line interface

        Command line options

        ```bash
        python -m python_template_project.cli [OPTIONS] path/to/file
        ```

        ---

        ## ⚙️ CLI-Options

        {}

        ## 💡 Examples

        In the example, the following is assumed: `example.input` in the current directory

        {}
        """
        ).format(table, "".join(examples))

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown.strip())


def main():
    """Main function to generate config file and documentation."""
    default_config: str = "../../config.yaml"
    default_cli_doc: str = "../../docs/usage/cli.md"
    default_config_doc: str = "../../docs/usage/config.md"

    ConfigParameterManager.generate_default_config_file(default_config)
    print(f"Generated: {default_config}")

    ConfigParameterManager.generate_config_markdown_doc(default_config_doc)
    print(f"Generated: {default_config_doc}")

    ConfigParameterManager.generate_cli_markdown_doc(default_cli_doc)
    print(f"Generated: {default_cli_doc}")


if __name__ == "__main__":
    main()
