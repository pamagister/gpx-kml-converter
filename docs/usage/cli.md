# Command Line Interface

Command line options for gpx_kml_converter

```bash
python -m gpx_kml_converter [OPTIONS] input
```

## Options

| Option        | Type  | Description                                              | Default    | Choices                               |
|---------------|-------|----------------------------------------------------------|------------|---------------------------------------|
| `input`       | str   | One or more input paths (GPX, KML, ZIP, or directory)    | *required* | -                                     |
| `--output`    | str   | Output directory; 'auto' creates a timestamped directory | 'auto'     | -                                     |
| `--tolerance` | float | Douglas-Peucker simplification tolerance in meters       | 10.0       | -                                     |
| `--mode`      | str   | Processing operation                                     | 'compress' | ['compress', 'merge', 'extract-pois'] |
| `--recursive` | bool  | Search input directories recursively                     | False      | [True, False]                         |
| `--elevation` | bool  | Include elevation data in waypoints                      | True       | [True, False]                         |


## Examples


### 1. Basic usage

```bash
python -m gpx_kml_converter input
```

### 2. With verbose logging

```bash
python -m gpx_kml_converter -v input
python -m gpx_kml_converter --verbose input
```

### 3. With quiet mode

```bash
python -m gpx_kml_converter -q input
python -m gpx_kml_converter --quiet input
```

### 4. With output parameter

```bash
python -m gpx_kml_converter --output auto input
```

### 5. With tolerance parameter

```bash
python -m gpx_kml_converter --tolerance 10.0 input
```

### 6. With mode parameter

```bash
python -m gpx_kml_converter --mode compress input
```