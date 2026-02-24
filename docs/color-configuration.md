# Color and Visual Configuration

## Runtime color API

`ColorConfigurationService` supports safe runtime updates without process restart.

### Current configuration

```python
service.get_config()
```

Returns:

- `theme`: `light`, `dark`, or `auto`
- `color_depth_bpp`: `24`, `30`, or `32`
- `profile`: `srgb`, `dcip3`, or `adobergb`

### Apply configuration

```python
service.apply_runtime_config(theme="dark", color_depth_bpp=32, profile="srgb")
```

Operation semantics:

1. Validate requested values against allowed domains.
2. Validate requested color depth against each active display’s supported modes.
3. Re-apply existing mode dimensions/refresh with requested depth.
4. Commit staged changes globally.
5. Return applied/skip details.

## Validation and constraints

- Unsupported theme/profile/depth raises `ColorConfigurationError`.
- Displays that cannot support the requested depth are skipped with reason payload.
- Commit failure raises `ColorConfigurationError` with Win32 return code.

## Edge cases

- If no active display supports a requested depth, no display is modified but commit still executes.
- Driver mode transitions may reject a valid depth for transient states; those adapters are skipped.
- Profile values are configuration-level metadata and do not load ICC files directly in this release.
