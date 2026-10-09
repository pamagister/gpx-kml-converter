from pathlib import Path

from config_cli_gui.docs import DocumentationGenerator

from gpx_kml_converter.config.config import ConfigParameterManager

"""function to generate config file and documentation."""


default_config: str = "config.yaml"
default_cli_doc: str = "docs/usage/cli.md"
default_config_doc: str = "docs/usage/config.md"

config_manager = ConfigParameterManager()

docGen = DocumentationGenerator(config_manager)
docGen.generate_default_config_file(output_file=default_config)
print(f"Generated: {default_config}")

docGen.generate_config_markdown_doc(output_file=default_config_doc)
print(f"Generated: {default_config_doc}")

docGen.generate_cli_markdown_doc(output_file=default_cli_doc, app_name="gpx_kml_converter")
print(f"Generated: {default_cli_doc}")

with Path(default_cli_doc).open("a", encoding="utf-8") as cli_doc:
    cli_doc.write(
        """

## Adding a waypoint

Use `--mode add-poi` to append one waypoint to a GPX file. The input must be a single
`.gpx` path; if it does not exist, a new GPX document is created. The waypoint is appended
even if an equivalent waypoint already exists. Latitude, longitude, and name are required;
description, symbol, and elevation are optional.

| Option | Description |
| --- | --- |
| `--lat` | Latitude in decimal degrees, from -90 to 90 |
| `--lon` | Longitude in decimal degrees, from -180 to 180 |
| `--name` | Waypoint name |
| `--desc` | Optional waypoint description |
| `--sym` | Optional waypoint symbol |
| `--ele` | Optional elevation in meters |

In this mode, `--output` is an output GPX file path rather than the output directory used
by the other modes. If omitted, the input file is updated in place.

```bash
gpx-kml-converter --mode add-poi --lat 51.0632 --lon 13.7421 \\
  --name "Historic Cafe" \\
  --desc "A nice coffee shop with outdoor seating." \\
  --sym Coffee --ele 115 input.gpx
```

To create a new file, pass a not-yet-existing `.gpx` path as the input:

```bash
gpx-kml-converter --mode add-poi --lat 48.8584 --lon 2.2945 \\
  --name "Eiffel Tower" new-pois.gpx
```

## Notes on --output parameter

By default, `compress` writes each GPX result beside its source as
`<source-stem>_processed_<date-time>.gpx`. A ZIP member is written under a
sibling directory named after the archive without its extension. `merge`
writes `gpx_processed_<date-time>.gpx` in the current directory. A custom
`--output` directory overrides these destinations. Existing output names are
overwritten; duplicate names within one batch receive a numeric suffix.

"""
    )
