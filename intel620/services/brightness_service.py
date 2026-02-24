import subprocess

from intel620.adapters.win32_api import Win32DisplayAdapter


class BrightnessService:
    def __init__(self, api=None):
        self.api = api or Win32DisplayAdapter()
        self._wmi_ok = None

    def test_wmi(self):
        if self._wmi_ok is not None:
            return self._wmi_ok
        try:
            import wmi

            wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[0]
            self._wmi_ok = True
        except Exception:
            self._wmi_ok = False
        return self._wmi_ok

    def get_brightness_wmi(self):
        try:
            import wmi

            return int(wmi.WMI(namespace="wmi").WmiMonitorBrightness()[0].CurrentBrightness)
        except Exception:
            return None

    def set_brightness_wmi(self, level):
        try:
            import wmi

            wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[0].WmiSetBrightness(level, 0)
            return True
        except Exception:
            return False

    def set_brightness_powershell(self, level):
        try:
            cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def set_brightness(self, device_name, level, is_primary=False):
        level = max(0, min(100, int(level)))
        if is_primary:
            if self.set_brightness_wmi(level):
                return "WMI Hardware", True
            if self.set_brightness_powershell(level):
                return "PowerShell WMI", True
        return "Gamma Ramp", self.api.set_gamma(device_name, level)

    def get_current_brightness(self):
        value = self.get_brightness_wmi()
        return value if value is not None else 80
