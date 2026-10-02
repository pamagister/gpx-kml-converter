# Installation


## Install from PyPI

### Recommended for standalone use: `pipx`

Use `pipx` to install the application as a standalone tool. It creates an isolated environment for the package, so it will not conflict with other Python projects.

```bash
pipx install gpx-kml-converter
```

On Linux, install `pipx` using your distribution's package manager (for example, `sudo apt install pipx` on Debian or Ubuntu), then run `pipx ensurepath` if needed and open a new terminal. This avoids installing packages into the system-managed Python environment.

### Use `pip` inside a virtual environment

Choose `pip` when installing the package for a particular project or when you already manage a virtual environment. Do not run `pip install` against your system Python; some Linux distributions prevent this to protect OS-managed Python packages.

```bash
python -m venv .venv
```

Activate the environment before using commands installed with `pip`:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install the package:

```bash
python -m pip install gpx-kml-converter
```

### Run the application

Both installation methods provide the CLI and GUI commands:

```bash
gpx-kml-converter --help
gpx-kml-converter-gui
```

On Linux, the GUI may also require your distribution's Tk package (often named `python3-tk`).

## 🔽 Executable

Download the latest executable:

- [⬇️ Download for Windows](https://github.com/pamagister/gpx-kml-converter/releases/latest/download/installer-win.zip)
- [⬇️ Download for macOS](https://github.com/pamagister/gpx-kml-converter/releases/latest/download/package-macos.zip)

## 👩🏼‍💻 Run from source

### Clone the repository

```bash
git clone https://github.com/pamagister/gpx-kml-converter.git
cd gpx-kml-converter
```

### Create an environment and install dependencies

```bash
uv venv
uv pip install -e ".[dev,docs]"
```

### Run with CLI from source

```bash
uv run python -m gpx_kml_converter.cli --help
```

### Run with GUI from source

```bash
uv run python -m gpx_kml_converter.gui
```
