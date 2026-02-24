import ctypes
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from intel620.adapters.win32_api import Win32DisplayAdapter
from intel620.models.win32_structures import (
    DEVMODEW,
    DISPLAY_DEVICE_ACTIVE,
    DISPLAY_DEVICE_PRIMARY_DEVICE,
    DM_BITSPERPEL,
    DM_DISPLAYFREQUENCY,
    DM_PELSHEIGHT,
    DM_PELSWIDTH,
    DM_POSITION,
    DISP_CHANGE_SUCCESSFUL,
)

logger = logging.getLogger(__name__)

ORIENTATIONS = ["Landscape", "Portrait", "Landscape Flipped", "Portrait Flipped"]


@dataclass(frozen=True)
class DisplayDetectionResult:
    device_name: str
    adapter_label: str
    is_primary: bool
    is_active: bool
    resolution: Tuple[int, int]
    refresh_rate_hz: int


class DisplayService:
    def __init__(self, api=None):
        self.api = api or Win32DisplayAdapter()

    def get_all_adapters(self):
        adapters = []
        idx = 0
        while True:
            ok, dev = self.api.enum_display_devices(None, idx)
            if not ok:
                break
            adapters.append(
                {
                    "index": idx,
                    "name": dev.DeviceName.strip(),
                    "string": dev.DeviceString.strip(),
                    "device_id": dev.DeviceID.strip(),
                    "device_key": dev.DeviceKey.strip(),
                    "is_active": bool(dev.StateFlags & DISPLAY_DEVICE_ACTIVE),
                    "is_primary": bool(dev.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE),
                    "flags": dev.StateFlags,
                }
            )
            idx += 1
        return adapters

    def detect_displays(self) -> Dict[str, object]:
        """Return primary/secondary display information with mode details."""
        detected: List[DisplayDetectionResult] = []
        for adapter in self.get_all_adapters():
            mode = self.get_current_mode(adapter["name"])
            if mode:
                resolution = (int(mode.dmPelsWidth), int(mode.dmPelsHeight))
                refresh_hz = int(mode.dmDisplayFrequency)
            else:
                resolution = (0, 0)
                refresh_hz = 0

            detected.append(
                DisplayDetectionResult(
                    device_name=adapter["name"],
                    adapter_label=adapter["string"],
                    is_primary=adapter["is_primary"],
                    is_active=adapter["is_active"],
                    resolution=resolution,
                    refresh_rate_hz=refresh_hz,
                )
            )

        primary = next((d for d in detected if d.is_primary), None)
        secondaries = [d for d in detected if not d.is_primary]
        logger.info(
            "Detected displays: total=%s active=%s primary=%s",
            len(detected),
            sum(1 for d in detected if d.is_active),
            primary.device_name if primary else "none",
        )

        return {
            "primary": primary,
            "secondary": secondaries,
            "all": detected,
            "active_count": sum(1 for d in detected if d.is_active),
        }

    def get_monitors_for(self, device_name):
        monitors, idx = [], 0
        while True:
            ok, mon = self.api.enum_display_devices(device_name, idx)
            if not ok:
                break
            monitors.append(
                {
                    "name": mon.DeviceName.strip(),
                    "string": mon.DeviceString.strip(),
                    "device_id": mon.DeviceID.strip(),
                    "is_active": bool(mon.StateFlags & DISPLAY_DEVICE_ACTIVE),
                }
            )
            idx += 1
        return monitors

    def get_current_mode(self, device_name):
        return self.api.get_current_mode(device_name)

    def get_supported_modes(self, device_name):
        modes, idx, seen = [], 0, set()
        while True:
            ok, dm = self.api.enum_display_settings(device_name, idx)
            if not ok:
                break
            key = (dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency)
            if key not in seen and dm.dmBitsPerPel in (24, 30, 32):
                seen.add(key)
                modes.append((dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency, dm.dmBitsPerPel))
            idx += 1
        return sorted(modes, key=lambda m: m[0] * m[1], reverse=True)

    def enable_display(self, device_name, pos_x, pos_y, width, height, freq=60, color_depth=32):
        dm = self._build_mode(width, height, freq, pos_x, pos_y, color_depth=color_depth)
        return self.api.apply_mode(device_name, dm, test_first=True, include_global=True)

    def disable_display(self, device_name):
        dm = self._build_mode(0, 0, 0, 0, 0, disable=True)
        return self.api.apply_mode(device_name, dm)

    def commit_changes(self):
        return self.api.commit()

    def get_dc_info(self, device_name):
        return self.api.get_dc_caps(device_name)

    def enumerate_display_devices(self):
        devices = []
        for adapter in self.get_all_adapters():
            item = {
                "adapter_index": adapter["index"],
                "device_name": adapter["name"],
                "device_string": adapter["string"],
                "device_id": adapter["device_id"],
                "device_key": adapter["device_key"],
                "is_active": adapter["is_active"],
                "is_primary": adapter["is_primary"],
                "role": "primary" if adapter["is_primary"] else "secondary",
                "monitors": [],
                "current_mode": None,
                "supported_modes": [],
            }
            dm = self.get_current_mode(adapter["name"])
            if dm:
                item["current_mode"] = {
                    "resolution": f"{dm.dmPelsWidth} x {dm.dmPelsHeight}",
                    "width_px": dm.dmPelsWidth,
                    "height_px": dm.dmPelsHeight,
                    "refresh_rate": f"{dm.dmDisplayFrequency} Hz",
                    "refresh_rate_hz": dm.dmDisplayFrequency,
                    "color_depth": f"{dm.dmBitsPerPel} bpp",
                    "color_depth_bpp": dm.dmBitsPerPel,
                    "position": f"({dm.dmPositionX}, {dm.dmPositionY})",
                    "orientation": ORIENTATIONS[dm.dmDisplayOrientation] if dm.dmDisplayOrientation < 4 else "Unknown",
                }
            item["supported_modes"] = [
                {
                    "resolution": f"{w}x{h}",
                    "refresh_rate": hz,
                    "color_depth": bpp,
                    "width_px": w,
                    "height_px": h,
                }
                for w, h, hz, bpp in self.get_supported_modes(adapter["name"])
            ]
            for index, mon in enumerate(self.get_monitors_for(adapter["name"])):
                item["monitors"].append(
                    {
                        "monitor_index": index,
                        "device_name": mon["name"],
                        "device_string": mon["string"],
                        "device_id": mon["device_id"],
                        "is_active": mon["is_active"],
                    }
                )
            devices.append(item)
        return devices

    def _build_mode(self, width, height, freq, pos_x, pos_y, disable=False, color_depth=32):
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT | DM_POSITION
        dm.dmPelsWidth = width
        dm.dmPelsHeight = height
        dm.dmPositionX = pos_x
        dm.dmPositionY = pos_y
        if not disable:
            dm.dmFields |= DM_BITSPERPEL | DM_DISPLAYFREQUENCY
            dm.dmBitsPerPel = color_depth
            dm.dmDisplayFrequency = freq
        return dm


def is_success(code):
    return code == DISP_CHANGE_SUCCESSFUL
