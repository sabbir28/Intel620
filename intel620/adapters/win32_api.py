from ctypes import byref, sizeof
import ctypes

from intel620.models.win32_structures import (
    BITSPIXEL,
    CDS_GLOBAL,
    CDS_NORESET,
    CDS_TEST,
    CDS_UPDATEREGISTRY,
    DESKTOPHORZRES,
    DESKTOPVERTRES,
    DEVMODEW,
    DISP_CHANGE_SUCCESSFUL,
    DISPLAY_DEVICEW,
    ENUM_CURRENT_SETTINGS,
    GAMMA_SIZE,
    HORZRES,
    LOGPIXELSX,
    LOGPIXELSY,
    PLANES,
    RAMP,
    VERTRES,
    VREFRESH,
)


class Win32DisplayAdapter:
    def __init__(self):
        if not hasattr(ctypes, "windll"):
            raise OSError("Win32 APIs are unavailable on this platform")
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32

    def enum_display_devices(self, parent_name, index):
        dev = DISPLAY_DEVICEW()
        dev.cb = sizeof(DISPLAY_DEVICEW)
        ok = self.user32.EnumDisplayDevicesW(parent_name, index, byref(dev), 0)
        return bool(ok), dev

    def enum_display_settings(self, device_name, mode_index):
        dm = DEVMODEW()
        dm.dmSize = sizeof(DEVMODEW)
        ok = self.user32.EnumDisplaySettingsW(device_name, mode_index, byref(dm))
        return bool(ok), dm

    def get_current_mode(self, device_name):
        ok, dm = self.enum_display_settings(device_name, ENUM_CURRENT_SETTINGS)
        return dm if ok else None

    def apply_mode(self, device_name, dm, test_first=False, include_global=False):
        if test_first:
            result = self.user32.ChangeDisplaySettingsExW(device_name, byref(dm), None, CDS_TEST, None)
            if result != DISP_CHANGE_SUCCESSFUL:
                return result

        flags = CDS_UPDATEREGISTRY | CDS_NORESET
        if include_global:
            flags |= CDS_GLOBAL
        return self.user32.ChangeDisplaySettingsExW(device_name, byref(dm), None, flags, None)

    def commit(self):
        return self.user32.ChangeDisplaySettingsExW(None, None, None, 0, None)

    def get_dc_caps(self, device_name):
        hdc = self.gdi32.CreateDCW("DISPLAY", device_name, None, None)
        if not hdc:
            return {}

        data = {
            "horizontal_res_px": self.gdi32.GetDeviceCaps(hdc, HORZRES),
            "vertical_res_px": self.gdi32.GetDeviceCaps(hdc, VERTRES),
            "desktop_horiz_px": self.gdi32.GetDeviceCaps(hdc, DESKTOPHORZRES),
            "desktop_vert_px": self.gdi32.GetDeviceCaps(hdc, DESKTOPVERTRES),
            "bits_per_pixel": self.gdi32.GetDeviceCaps(hdc, BITSPIXEL),
            "color_planes": self.gdi32.GetDeviceCaps(hdc, PLANES),
            "dpi_x": self.gdi32.GetDeviceCaps(hdc, LOGPIXELSX),
            "dpi_y": self.gdi32.GetDeviceCaps(hdc, LOGPIXELSY),
            "refresh_rate_hz": self.gdi32.GetDeviceCaps(hdc, VREFRESH),
        }
        self.gdi32.DeleteDC(hdc)
        return data

    def set_gamma(self, device_name, level):
        scale = max(0.05, level / 100.0)
        ramp = RAMP()
        for i in range(GAMMA_SIZE):
            value = int(min(65535, i * 256 * scale))
            ramp.Red[i] = ramp.Green[i] = ramp.Blue[i] = value

        hdc = self.gdi32.CreateDCW("DISPLAY", device_name, None, None)
        if not hdc:
            return False

        ok = bool(self.gdi32.SetDeviceGammaRamp(hdc, byref(ramp)))
        self.gdi32.DeleteDC(hdc)
        return ok
