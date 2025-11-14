# Command Line Interface

Command line options for gpx_kml_converter

```bash
python -m gpx_kml_converter [OPTIONS] input
```

## Options

| Option                | Type | Description                                       | Default    | Choices       |
|-----------------------|------|---------------------------------------------------|------------|---------------|
| `input`               | str  | Path to input (file or folder)                    | *required* | -             |
| `--output`            | str  | Path to output destination                        | *required* | -             |
| `--min_dist`          | int  | Maximum distance between two waypoints            | 20         | -             |
| `--extract_waypoints` | bool | Extract starting points of each track as waypoint | True       | [True, False] |
| `--elevation`         | bool | Include elevation data in waypoints               | True       | [True, False] |


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

### 4. With min_dist parameter

```bash
python -m gpx_kml_converter --min_dist 20 input
```

### 5. With extract_waypoints parameter

```bash
python -m gpx_kml_converter --extract_waypoints True input
```

### 6. With elevation parameter

```bash
python -m gpx_kml_converter --elevation True input
```