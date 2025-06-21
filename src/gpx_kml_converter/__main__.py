"""Entry point for gpx_kml_converter."""

import sys  # pragma: no cover

from .cli.cli import main  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
