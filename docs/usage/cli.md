# Command Line Interface

Command line options for gpx_kml_converter.cli

```bash
python -m gpx_kml_converter.cli [OPTIONS] input
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
python -m gpx_kml_converter.cli input
```

### 2. With min_dist parameter

```bash
python -m gpx_kml_converter.cli --min_dist 20 input
```

### 3. With extract_waypoints parameter

```bash
python -m gpx_kml_converter.cli --extract_waypoints True input
```

### 4. With elevation parameter

```bash
python -m gpx_kml_converter.cli --elevation True input
```