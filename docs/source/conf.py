from __future__ import annotations

from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
project_data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

project = "Intel620"
author = "Intel620 Engineering"
release = project_data["project"]["version"]
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = []
html_theme = "furo"
