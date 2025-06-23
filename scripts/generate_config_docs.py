from config_cli_gui.docs import DocumentationGenerator

from gpx_kml_converter.config.config import ProjectConfigManager

"""function to generate config file and documentation."""


default_config: str = "config.yaml"
default_cli_doc: str = "docs/usage/cli.md"
default_config_doc: str = "docs/usage/config.md"

config_manager = ProjectConfigManager()

docGen = DocumentationGenerator(config_manager)
docGen.generate_default_config_file(output_file=default_config)
print(f"Generated: {default_config}")

docGen.generate_config_markdown_doc(output_file=default_config_doc)
print(f"Generated: {default_config_doc}")

docGen.generate_cli_markdown_doc(output_file=default_cli_doc, app_name="gpx_kml_converter.cli")
print(f"Generated: {default_cli_doc}")