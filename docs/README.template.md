# Intel620

Production-grade Python toolkit for Intel 620 diagnostics, display inspection, and reporting.

> Released version: **{version}**  
> Release date: **{date}**

## Installation

```bash
python -m pip install intel620
```

## Usage

```python
from intel620.services.display_service import DisplayService

service = DisplayService()
print(service.get_displays())
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Release notes

See [CHANGELOG.md](CHANGELOG.md) for complete release history.
