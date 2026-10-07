# Command Line Interface

Command line options for gpx_kml_converter

```bash
gpx-kml-converter [OPTIONS] <input>
```

For development from a source checkout, the equivalent module invocation is:

```bash
python -m gpx_kml_converter [OPTIONS] <input>
```

## Options

| Option        | Type  | Description                                              | Default    | Choices                               |
|---------------|-------|----------------------------------------------------------|------------|---------------------------------------|
| --config      | str   | Path to configuration file                               | -          | -                                     |
| -v, --verbose | bool  | Enable debug logging                                     | False      | [True, False]                         |
| -q, --quiet   | bool  | Show warnings and errors only                            | False      | [True, False]                         |
| `input`       | str   | One or more input paths (GPX, KML, ZIP, or directory)    | *required* | -                                     |
| `--output`    | str   | Output directory; 'auto' creates a timestamped directory | 'auto'     | -                                     |
| `--tolerance` | float | Douglas-Peucker simplification tolerance in meters       | 10.0       | -                                     |
| `--mode`      | str   | Processing operation                                     | 'compress' | ['compress', 'merge', 'extract-pois'] |
| `--recursive` | bool  | Search input directories recursively                     | False      | [True, False]                         |
| `--elevation` | bool  | Include elevation data in waypoints                      | True       | [True, False]                         |


## Examples


### 1. Basic usage

```bash
gpx-kml-converter input
```

### 2. With verbose logging

```bash
gpx-kml-converter -v input
gpx-kml-converter --verbose input
```

### 3. With quiet mode

```bash
gpx-kml-converter -q input
gpx-kml-converter --quiet input
```

### 4. With output parameter

```bash
gpx-kml-converter --output auto input
```

### 5. With tolerance parameter

```bash
gpx-kml-converter --tolerance 10.0 input
```

### 6. With mode parameter

```bash
gpx-kml-converter --mode compress input
```

### Developer usage

```bash
python -m gpx_kml_converter --help
python -m gpx_kml_converter input
```
