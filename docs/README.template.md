# Intel620

Production-grade Intel HD/UHD Graphics 620 toolkit with GUI and CLI utilities for Windows.

> Released version: **{version}**  
> Release date: **{date}**

## Install (development)

```bash
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Run

```bash
python cli.py
python main.py
```

## Build Windows executables (PyInstaller)

```bash
python scripts/build_windows.py
```

Artifacts are generated in `dist/`:

- `intel620-cli.exe`
- `intel620-gui.exe`

## Release notes

See [CHANGELOG.md](CHANGELOG.md) for complete release history.
