# Setup virtual environment

## Create `venv`

Creating virtual environment `venv` using [uv](https://docs.astral.sh/uv/):
```bash
uv venv
```

## Activate `venv`

Activating a Python virtual environment `venv`
> Note: Replace `.venv` with your Venv folder name if you have chosen a different one.

🔹 Windows (PowerShell)

```bash
.venv\Scripts\activate.ps1
```

🔹 Windows (CMD)
```cmd
.venv\Scripts\activate.bat
```

🔹 Linux / macOS (Bash/Zsh)
```bash
source .venv/bin/activate
```