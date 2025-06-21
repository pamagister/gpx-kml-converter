# Command line interface

Command line options

```bash
python -m python_template_project.cli [OPTIONS] path/to/file
```

---

## ⚙️ CLI-Options

| Option                | Type | Description                                       | Default    | Choices       |
|-----------------------|------|---------------------------------------------------|------------|---------------|
| `path/to/file`        | str  | Path to input (file or folder)                    | *required* | -             |
| `--output`            | str  | Path to output destination                        | *required* | -             |
| `--min_dist`          | int  | Maximum distance between two waypoints            | 20         | -             |
| `--extract_waypoints` | bool | Extract starting points of each track as waypoint | True       | [True, False] |
| `--elevation`         | bool | Include elevation data in waypoints               | True       | [True, False] |


## 💡 Examples

In the example, the following is assumed: `example.input` in the current directory


### 1. Standard version (only required parameter)

```bash
python -m python_template_project.cli input
```

### 2. With verbose logging

```bash
python -m python_template_project.cli --verbose input
```

### 3. With quiet mode

```bash
python -m python_template_project.cli --quiet input
```

### 4. Example with 1 Parameter(s)

```bash
python -m python_template_project.cli --min_dist 20 input
```

### 5. Example with 2 Parameter(s)

```bash
python -m python_template_project.cli --min_dist 20 --extract_waypoints True input
```