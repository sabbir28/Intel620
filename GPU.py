"""
Intel HD/UHD Graphics 620 - Display Information Query Tool
============================================================
This script queries connected display settings using:
- Windows ctypes (EnumDisplayDevices, EnumDisplaySettings, GetDeviceCaps)
- Attempts to load Intel-specific DLLs (igc64.dll, igd9dxva64.dll)
- DirectX/DXGI for adapter/monitor enumeration

Requirements: Windows OS with Intel GPU drivers installed
Run: python intel_display_info.py
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import platform
import json
from ctypes import windll, byref, sizeof, POINTER, Structure, c_int, c_long, c_wchar_p

# ─── Guard: Windows only ──────────────────────────────────────────────────────
if platform.system() != "Windows":
    print("[ERROR] This script must be run on Windows with Intel drivers installed.")
    sys.exit(1)

# ─── Win32 Constants ──────────────────────────────────────────────────────────
ENUM_CURRENT_SETTINGS  = -1
ENUM_REGISTRY_SETTINGS = -2
DISPLAY_DEVICE_ACTIVE  = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004

# DeviceCap indices
HORZRES      = 8
VERTRES      = 10
BITSPIXEL    = 12
PLANES       = 14
LOGPIXELSX   = 88
LOGPIXELSY   = 90
VREFRESH     = 116
DESKTOPHORZRES = 118
DESKTOPVERTRES = 117

# ─── Win32 Structures ─────────────────────────────────────────────────────────
class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName",       ctypes.c_wchar * 32),
        ("dmSpecVersion",      wintypes.WORD),
        ("dmDriverVersion",    wintypes.WORD),
        ("dmSize",             wintypes.WORD),
        ("dmDriverExtra",      wintypes.WORD),
        ("dmFields",           wintypes.DWORD),
        ("dmPositionX",        c_long),
        ("dmPositionY",        c_long),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor",            wintypes.SHORT),
        ("dmDuplex",           wintypes.SHORT),
        ("dmYResolution",      wintypes.SHORT),
        ("dmTTOption",         wintypes.SHORT),
        ("dmCollate",          wintypes.SHORT),
        ("dmFormName",         ctypes.c_wchar * 32),
        ("dmLogPixels",        wintypes.WORD),
        ("dmBitsPerPel",       wintypes.DWORD),
        ("dmPelsWidth",        wintypes.DWORD),
        ("dmPelsHeight",       wintypes.DWORD),
        ("dmDisplayFlags",     wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod",        wintypes.DWORD),
        ("dmICMIntent",        wintypes.DWORD),
        ("dmMediaType",        wintypes.DWORD),
        ("dmDitherType",       wintypes.DWORD),
        ("dmReserved1",        wintypes.DWORD),
        ("dmReserved2",        wintypes.DWORD),
        ("dmPanningWidth",     wintypes.DWORD),
        ("dmPanningHeight",    wintypes.DWORD),
    ]

class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb",             wintypes.DWORD),
        ("DeviceName",     ctypes.c_wchar * 32),
        ("DeviceString",   ctypes.c_wchar * 128),
        ("StateFlags",     wintypes.DWORD),
        ("DeviceID",       ctypes.c_wchar * 128),
        ("DeviceKey",      ctypes.c_wchar * 128),
    ]

# ─── Intel DLL Loader ─────────────────────────────────────────────────────────
def find_intel_dll(dll_name):
    """Search common Intel driver installation directories for a DLL."""
    import os
    search_paths = [
        r"C:\Windows\System32",
        r"C:\Windows\SysWOW64",
        r"C:\Windows\System32\DriverStore\FileRepository",
    ]
    # Also scan DriverStore subdirectories (Intel drivers live here)
    driver_store = r"C:\Windows\System32\DriverStore\FileRepository"
    if os.path.isdir(driver_store):
        for folder in os.listdir(driver_store):
            if "igd" in folder.lower() or "igfx" in folder.lower() or "iigd" in folder.lower():
                search_paths.append(os.path.join(driver_store, folder))

    for directory in search_paths:
        full_path = os.path.join(directory, dll_name)
        if os.path.isfile(full_path):
            return full_path
    return None


def try_load_intel_dlls():
    """Attempt to load Intel GPU DLLs and report status."""
    import os
    dlls_to_try = {
        "igc64.dll":       "Intel Graphics Compiler (Core shader compilation, DX12/Vulkan/OpenGL)",
        "igd9dxva64.dll":  "Intel DirectX Video Acceleration (DXVA2 hardware video decode)",
        "igdgmm64.dll":    "Intel Graphics Memory Manager",
        "igdumdim64.dll":  "Intel User Mode Driver (DX11/DX12)",
    }

    print("\n" + "=" * 60)
    print("  INTEL GPU DLL STATUS")
    print("=" * 60)

    loaded = {}
    for dll_name, description in dlls_to_try.items():
        full_path = find_intel_dll(dll_name)
        if full_path:
            try:
                handle = ctypes.WinDLL(full_path)
                status = f"✅ LOADED\n    Path    : {full_path}"
                loaded[dll_name] = handle
            except OSError as e:
                status = f"⚠️  FOUND but failed to load: {e}\n    Path    : {full_path}"
                loaded[dll_name] = None
        else:
            status = "❌ NOT FOUND in System32, SysWOW64, or DriverStore"
            loaded[dll_name] = None

        print(f"\n  {dll_name}")
        print(f"    Purpose : {description}")
        print(f"    Status  : {status}")

    return loaded

# ─── Display Device Enumeration ───────────────────────────────────────────────
def enumerate_display_devices():
    """Enumerate all display adapters and their monitors."""
    user32 = windll.user32
    devices = []

    adapter_idx = 0
    while True:
        adapter = DISPLAY_DEVICEW()
        adapter.cb = sizeof(DISPLAY_DEVICEW)

        if not user32.EnumDisplayDevicesW(None, adapter_idx, byref(adapter), 0):
            break

        adapter_info = {
            "adapter_index":  adapter_idx,
            "device_name":    adapter.DeviceName.strip(),
            "device_string":  adapter.DeviceString.strip(),
            "device_id":      adapter.DeviceID.strip(),
            "device_key":     adapter.DeviceKey.strip(),
            "is_active":      bool(adapter.StateFlags & DISPLAY_DEVICE_ACTIVE),
            "is_primary":     bool(adapter.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE),
            "monitors":       [],
            "current_mode":   None,
            "supported_modes": [],
        }

        # Get current display mode
        devmode = DEVMODEW()
        devmode.dmSize = sizeof(DEVMODEW)
        if user32.EnumDisplaySettingsW(adapter.DeviceName, ENUM_CURRENT_SETTINGS, byref(devmode)):
            adapter_info["current_mode"] = {
                "resolution":    f"{devmode.dmPelsWidth} x {devmode.dmPelsHeight}",
                "width_px":      devmode.dmPelsWidth,
                "height_px":     devmode.dmPelsHeight,
                "refresh_rate":  f"{devmode.dmDisplayFrequency} Hz",
                "color_depth":   f"{devmode.dmBitsPerPel} bpp",
                "position":      f"({devmode.dmPositionX}, {devmode.dmPositionY})",
                "orientation":   (["Landscape","Portrait","Landscape Flipped","Portrait Flipped"]
                                   [devmode.dmDisplayOrientation]
                                   if devmode.dmDisplayOrientation < 4 else "Unknown"),
            }

        # Get supported modes
        mode_idx = 0
        seen_modes = set()
        while True:
            dm = DEVMODEW()
            dm.dmSize = sizeof(DEVMODEW)
            if not user32.EnumDisplaySettingsW(adapter.DeviceName, mode_idx, byref(dm)):
                break
            key = (dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency, dm.dmBitsPerPel)
            if key not in seen_modes:
                seen_modes.add(key)
                adapter_info["supported_modes"].append({
                    "resolution":   f"{dm.dmPelsWidth}x{dm.dmPelsHeight}",
                    "refresh_rate": dm.dmDisplayFrequency,
                    "color_depth":  dm.dmBitsPerPel,
                })
            mode_idx += 1

        # Enumerate monitors connected to this adapter
        monitor_idx = 0
        while True:
            monitor = DISPLAY_DEVICEW()
            monitor.cb = sizeof(DISPLAY_DEVICEW)
            if not user32.EnumDisplayDevicesW(adapter.DeviceName, monitor_idx, byref(monitor), 0):
                break
            adapter_info["monitors"].append({
                "monitor_index":  monitor_idx,
                "device_name":    monitor.DeviceName.strip(),
                "device_string":  monitor.DeviceString.strip(),
                "device_id":      monitor.DeviceID.strip(),
                "is_active":      bool(monitor.StateFlags & DISPLAY_DEVICE_ACTIVE),
            })
            monitor_idx += 1

        devices.append(adapter_info)
        adapter_idx += 1

    return devices

# ─── Device Context Info (GDI) ────────────────────────────────────────────────
def get_dc_info(device_name):
    """Get detailed device context capabilities via GDI."""
    gdi32  = windll.gdi32
    user32 = windll.user32

    hdc = gdi32.CreateDCW("DISPLAY", device_name, None, None)
    if not hdc:
        return {}

    info = {
        "horizontal_res_px":    gdi32.GetDeviceCaps(hdc, HORZRES),
        "vertical_res_px":      gdi32.GetDeviceCaps(hdc, VERTRES),
        "desktop_horiz_px":     gdi32.GetDeviceCaps(hdc, DESKTOPHORZRES),
        "desktop_vert_px":      gdi32.GetDeviceCaps(hdc, DESKTOPVERTRES),
        "bits_per_pixel":       gdi32.GetDeviceCaps(hdc, BITSPIXEL),
        "color_planes":         gdi32.GetDeviceCaps(hdc, PLANES),
        "dpi_x":                gdi32.GetDeviceCaps(hdc, LOGPIXELSX),
        "dpi_y":                gdi32.GetDeviceCaps(hdc, LOGPIXELSY),
        "refresh_rate_hz":      gdi32.GetDeviceCaps(hdc, VREFRESH),
    }

    gdi32.DeleteDC(hdc)
    return info

# ─── DXGI Adapter Info (COM / ctypes) ─────────────────────────────────────────
def get_dxgi_info():
    """Use DXGI via ctypes COM to enumerate GPU adapters & outputs."""
    try:
        dxgi = ctypes.WinDLL("dxgi.dll")
    except OSError:
        return {"error": "dxgi.dll not found"}

    # IID_IDXGIFactory1 = {770AAE78-F26F-4DBA-A829-253C83D1B387}
    class GUID(ctypes.Structure):
        _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

    iid = GUID()
    iid.Data1 = 0x770AAE78
    iid.Data2 = 0xF26F
    iid.Data3 = 0x4DBA
    iid.Data4 = (ctypes.c_ubyte * 8)(0xA8, 0x29, 0x25, 0x3C, 0x83, 0xD1, 0xB3, 0x87)

    factory = ctypes.c_void_p()
    hr = dxgi.CreateDXGIFactory1(byref(iid), byref(factory))
    if hr != 0 or not factory:
        return {"error": f"CreateDXGIFactory1 failed (hr=0x{hr & 0xFFFFFFFF:08X})"}

    return {"status": "✅ DXGI Factory1 created successfully",
            "note": "Install comtypes (pip install comtypes) for full adapter/output enumeration"}

# ─── Pretty Print ─────────────────────────────────────────────────────────────
def print_display_info(devices):
    print("\n" + "=" * 60)
    print("  CONNECTED DISPLAY INFORMATION")
    print("=" * 60)

    if not devices:
        print("  [!] No display devices found.")
        return

    for dev in devices:
        print(f"\n{'─'*60}")
        print(f"  ADAPTER [{dev['adapter_index']}]: {dev['device_string']}")
        print(f"{'─'*60}")
        print(f"  Device Name  : {dev['device_name']}")
        print(f"  Device ID    : {dev['device_id'][:80]}")
        print(f"  Active       : {'Yes' if dev['is_active'] else 'No'}")
        print(f"  Primary      : {'Yes' if dev['is_primary'] else 'No'}")

        if dev["current_mode"]:
            m = dev["current_mode"]
            print(f"\n  Current Mode:")
            print(f"    Resolution   : {m['resolution']}")
            print(f"    Refresh Rate : {m['refresh_rate']}")
            print(f"    Color Depth  : {m['color_depth']}")
            print(f"    Position     : {m['position']}")
            print(f"    Orientation  : {m['orientation']}")

        # DC caps
        if dev["is_active"]:
            dc = get_dc_info(dev["device_name"])
            if dc:
                print(f"\n  GDI Device Context Caps:")
                print(f"    DPI (X / Y)  : {dc['dpi_x']} / {dc['dpi_y']}")
                print(f"    Desktop Size : {dc['desktop_horiz_px']} x {dc['desktop_vert_px']} px")
                print(f"    Bits/Pixel   : {dc['bits_per_pixel']}")
                print(f"    Color Planes : {dc['color_planes']}")
                print(f"    Refresh Rate : {dc['refresh_rate_hz']} Hz")

        if dev["monitors"]:
            print(f"\n  Monitors on this adapter:")
            for mon in dev["monitors"]:
                active_tag = "🟢" if mon["is_active"] else "⚪"
                print(f"    {active_tag} [{mon['monitor_index']}] {mon['device_string']}")
                print(f"        ID: {mon['device_id'][:70]}")

        total_modes = len(dev["supported_modes"])
        if total_modes:
            max_res = max(dev["supported_modes"], key=lambda x: x["width_px"] * x["height_px"]
                          if "width_px" in x else 0,
                         default=dev["supported_modes"][-1])
            print(f"\n  Supported Modes : {total_modes} total")
            print(f"  Highest Res Mode: {max_res['resolution']} @ {max_res['refresh_rate']}Hz")

# ─── Save JSON Report ─────────────────────────────────────────────────────────
def save_report(devices, dll_status):
    report = {
        "intel_dll_status": {k: ("loaded" if v else "not_found") for k, v in dll_status.items()},
        "display_devices": devices,
    }
    out_path = "intel_display_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  [✅] Full JSON report saved → {out_path}")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 60)
    print("  Intel HD/UHD Graphics 620 - Display Query Tool")
    print("  Running on:", platform.system(), platform.version())
    print("=" * 60)

    # 1. Try loading Intel DLLs
    dll_status = try_load_intel_dlls()

    # 2. DXGI info
    print("\n" + "=" * 60)
    print("  DXGI ADAPTER CHECK")
    print("=" * 60)
    dxgi_result = get_dxgi_info()
    if dxgi_result:
        for k, v in dxgi_result.items():
            print(f"  {k}: {v}")
    else:
        print("  DXGI not available.")

    # 3. Enumerate displays
    devices = enumerate_display_devices()

    # Fix: add width/height keys to supported modes for max_res lookup
    for dev in devices:
        for mode in dev["supported_modes"]:
            parts = mode["resolution"].split("x")
            if len(parts) == 2:
                mode["width_px"]  = int(parts[0])
                mode["height_px"] = int(parts[1])

    # 4. Print results
    print_display_info(devices)

    # 5. Save JSON
    save_report(devices, dll_status)

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()