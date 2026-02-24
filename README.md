# Intel620 Display & Graphics Management Toolkit

Intel620 is a Windows-focused toolkit for inspecting displays, managing graphics state transitions, and applying runtime color policies on Intel HD/UHD 620 systems.

## Highlights

- Enumerates adapters, monitors, active mode, and capabilities.
- Detects primary/secondary display roles with current resolution and refresh rate.
- Supports safe graphics refresh paths for startup, wake, and manual reset workflows.
- Applies validated runtime color settings (theme, color depth, profile) without full restart.
- Includes GUI panel (`BootUp.py`) and CLI utility (`GPU.py`).

## Architecture

```text
intel620/
  adapters/      # Win32 API bindings
  models/        # ctypes structures and Win32 constants
  services/      # display, graphics lifecycle, color, DXGI, DLL checks
  gui/           # Tkinter control panel
  reporting/     # JSON reporting
```

- `DisplayService` is the hardware-facing display domain service.
- `GraphicsLifecycleService` orchestrates safe reinitialization during lifecycle events.
- `ColorConfigurationService` validates and applies runtime visual settings.

## Quick Start

### Requirements

- Windows 10/11
- Python 3.10+
- Intel graphics drivers installed

### Run GUI

```bash
python BootUp.py
```

### Run CLI report

```bash
python GPU.py
```

### Trigger graphics reset

```bash
python GPU.py --reset-graphics
```

### Apply runtime color settings

```bash
python GPU.py --theme dark --color-depth 32 --profile srgb
```

## Documentation

- [System Initialization Flow](docs/system-initialization.md)
- [Display & Graphics Management](docs/display-graphics-management.md)
- [Color and Visual Configuration](docs/color-configuration.md)
- [Configuration Reference](docs/configuration-reference.md)

## Platform assumptions

This project assumes:

- `user32` and `gdi32` APIs are available.
- Intel drivers expose standard mode enumeration via `EnumDisplaySettingsW`.
- Driver mode changes are committed using `ChangeDisplaySettingsExW`.

For details, see the docs listed above.
