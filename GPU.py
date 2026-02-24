"""Intel HD/UHD Graphics 620 - Display Information Query Tool."""

import platform
import sys

from intel620.reporting.report_writer import ReportWriter
from intel620.services.display_service import DisplayService
from intel620.services.dll_service import IntelDllService
from intel620.services.dxgi_service import DxgiService


def print_display_info(devices, display_service):
    print("\n" + "=" * 60)
    print("  CONNECTED DISPLAY INFORMATION")
    print("=" * 60)

    if not devices:
        print("  [!] No display devices found.")
        return

    for dev in devices:
        print(f"\n{'─' * 60}")
        print(f"  ADAPTER [{dev['adapter_index']}]: {dev['device_string']}")
        print(f"{'─' * 60}")
        print(f"  Device Name  : {dev['device_name']}")
        print(f"  Device ID    : {dev['device_id'][:80]}")
        print(f"  Active       : {'Yes' if dev['is_active'] else 'No'}")
        print(f"  Primary      : {'Yes' if dev['is_primary'] else 'No'}")

        if dev["current_mode"]:
            mode = dev["current_mode"]
            print("\n  Current Mode:")
            print(f"    Resolution   : {mode['resolution']}")
            print(f"    Refresh Rate : {mode['refresh_rate']}")
            print(f"    Color Depth  : {mode['color_depth']}")
            print(f"    Position     : {mode['position']}")
            print(f"    Orientation  : {mode['orientation']}")

        if dev["is_active"]:
            dc = display_service.get_dc_info(dev["device_name"])
            if dc:
                print("\n  GDI Device Context Caps:")
                print(f"    DPI (X / Y)  : {dc['dpi_x']} / {dc['dpi_y']}")
                print(f"    Desktop Size : {dc['desktop_horiz_px']} x {dc['desktop_vert_px']} px")
                print(f"    Bits/Pixel   : {dc['bits_per_pixel']}")
                print(f"    Color Planes : {dc['color_planes']}")
                print(f"    Refresh Rate : {dc['refresh_rate_hz']} Hz")

        if dev["monitors"]:
            print("\n  Monitors on this adapter:")
            for mon in dev["monitors"]:
                active_tag = "🟢" if mon["is_active"] else "⚪"
                print(f"    {active_tag} [{mon['monitor_index']}] {mon['device_string']}")
                print(f"        ID: {mon['device_id'][:70]}")

        total_modes = len(dev["supported_modes"])
        if total_modes:
            max_res = max(dev["supported_modes"], key=lambda x: x["width_px"] * x["height_px"], default=dev["supported_modes"][-1])
            print(f"\n  Supported Modes : {total_modes} total")
            print(f"  Highest Res Mode: {max_res['resolution']} @ {max_res['refresh_rate']}Hz")


def main():
    if platform.system() != "Windows":
        print("[ERROR] This script must be run on Windows with Intel drivers installed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Intel HD/UHD Graphics 620 - Display Query Tool")
    print("  Running on:", platform.system(), platform.version())
    print("=" * 60)

    display_service = DisplayService()
    dll_service = IntelDllService()
    dxgi_service = DxgiService()
    report_writer = ReportWriter()

    dll_status = dll_service.print_load_status()

    print("\n" + "=" * 60)
    print("  DXGI ADAPTER CHECK")
    print("=" * 60)
    dxgi_result = dxgi_service.get_dxgi_info()
    for key, value in dxgi_result.items():
        print(f"  {key}: {value}")

    devices = display_service.enumerate_display_devices()
    print_display_info(devices, display_service)

    out_path = report_writer.save_report(devices, dll_status)
    print(f"\n  [✅] Full JSON report saved → {out_path}")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
