# Display & Graphics Management

## Display detection model

`DisplayService.detect_displays()` classifies displays into:

- Primary display (`DISPLAY_DEVICE_PRIMARY_DEVICE`)
- Secondary displays (all non-primary adapters)
- Active count (`DISPLAY_DEVICE_ACTIVE`)

Each detected display includes:

- Device name and adapter label
- Primary/active flags
- Current resolution (`width x height`)
- Current refresh rate (Hz)

## Display enumeration

`DisplayService.enumerate_display_devices()` returns expanded metadata for reporting:

- Adapter details and monitor list
- Role (`primary` or `secondary`)
- Current mode (resolution, refresh rate, color depth, orientation, position)
- Supported modes filtered for practical desktop depths (24/30/32 bpp)

## Graphics reset and driver refresh

`GraphicsLifecycleService` exposes programmatic APIs:

- `initialize_for_startup()`
- `initialize_for_wake()`
- `manual_reset()`
- `trigger_refresh(event)`

Behavior:

1. Detect active displays.
2. Read each display’s current mode.
3. Re-apply mode with test-first validation.
4. Commit all changes in one global call.
5. Return structured `GraphicsResetResult` with success and diagnostics.

## Failure handling

- Per-display mode apply failures are logged and skipped.
- Commit failure returns non-success result and error message.
- Runtime state can be queried with `get_runtime_state()` for health checks.

## Programmatic usage

```python
from intel620.services.graphics_service import GraphicsLifecycleService

service = GraphicsLifecycleService()
result = service.manual_reset()
if not result.success:
    print(result.message)
```
