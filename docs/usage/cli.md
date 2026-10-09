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

| Option        | Type  | Description                                                           | Default    | Choices                                          |
|---------------|-------|-----------------------------------------------------------------------|------------|--------------------------------------------------|
| --config      | str   | Path to configuration file                                            | -          | -                                                |
| -v, --verbose | bool  | Enable debug logging                                                  | False      | [True, False]                                    |
| -q, --quiet   | bool  | Show warnings and errors only                                         | False      | [True, False]                                    |
| `input`       | str   | One or more input paths (GPX, KML, ZIP, or directory)                 | *required* | -                                                |
| `--output`    | str   | Output directory override; 'auto' uses mode-specific output locations | 'auto'     | -                                                |
| `--tolerance` | float | Douglas-Peucker simplification tolerance in meters                    | 10.0       | -                                                |
| `--mode`      | str   | Processing operation                                                  | 'compress' | ['compress', 'merge', 'extract-pois', 'add-poi'] |
| `--recursive` | bool  | Search input directories recursively                                  | False      | [True, False]                                    |
| `--elevation` | bool  | Include elevation data in waypoints                                   | True       | [True, False]                                    |


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
gpx-kml-converter --mode add-poi --lat 51.0632 --lon 13.7421 \
  --name "Historic Cafe" \
  --desc "A nice coffee shop with outdoor seating." \
  --sym Coffee --ele 115 input.gpx
```

To create a new file, pass a not-yet-existing `.gpx` path as the input:

```bash
gpx-kml-converter --mode add-poi --lat 48.8584 --lon 2.2945 \
  --name "Eiffel Tower" new-pois.gpx
```

## Notes on --output parameter

By default, `compress` writes each GPX result beside its source as
`<source-stem>_processed_<date-time>.gpx`. A ZIP member is written under a
sibling directory named after the archive without its extension. `merge`
writes `gpx_processed_<date-time>.gpx` in the current directory. A custom
`--output` directory overrides these destinations. Existing output names are
overwritten; duplicate names within one batch receive a numeric suffix.

