# Configuration Reference

## CLI options (`GPU.py`)

| Option | Default | Allowed values | Description |
|---|---|---|---|
| `--reset-graphics` | `false` | flag | Triggers manual graphics refresh sequence. |
| `--theme` | current runtime value (`dark`) | `light`, `dark`, `auto` | Logical application theme selector. |
| `--color-depth` | current runtime value (`32`) | `24`, `30`, `32` | Requested bits-per-pixel for active displays. |
| `--profile` | current runtime value (`srgb`) | `srgb`, `dcip3`, `adobergb` | Named color profile metadata selector. |

## Service interfaces

### DisplayService

- `detect_displays()`
- `enumerate_display_devices()`
- `enable_display(...)`
- `disable_display(device_name)`
- `commit_changes()`

### GraphicsLifecycleService

- `initialize_for_startup()`
- `initialize_for_wake()`
- `manual_reset()`
- `trigger_refresh(event)`
- `get_runtime_state()`

### ColorConfigurationService

- `get_config()`
- `validate_config(config)`
- `apply_runtime_config(...)`

## Defaults

- Theme: `dark`
- Color depth: `32`
- Profile: `srgb`

## Platform constraints

- Windows only.
- Requires functional user-mode graphics driver support.
- Runtime mode changes can be blocked by policy-managed endpoints.
