import os
import platform
import subprocess

from intel620.services.dll_service import DLLS_TO_TRY


class SystemInfoService:
    def collect(self):
        info = {
            "os": platform.system(),
            "os_ver": platform.version(),
            "os_rel": platform.release(),
            "machine": platform.machine(),
            "node": platform.node(),
            "python": platform.python_version(),
        }
        for cmd, prefix in [
            (["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed", "/format:list"], "cpu_"),
            (["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/format:list"], "ram_"),
            (
                [
                    "wmic",
                    "path",
                    "win32_VideoController",
                    "get",
                    "Name,DriverVersion,VideoModeDescription,AdapterRAM,CurrentRefreshRate,VideoProcessor",
                    "/format:list",
                ],
                "gpu_",
            ),
        ]:
            self._merge_wmic_output(info, cmd, prefix)
        info["dll_paths"] = self._find_dll_paths()
        return info

    def _merge_wmic_output(self, info, cmd, prefix):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            for line in result.stdout.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    info[f"{prefix}{key.strip().lower()}"] = value.strip()
        except Exception:
            return

    def _find_dll_paths(self):
        dlls = list(DLLS_TO_TRY.keys())
        driver_store = r"C:\Windows\System32\DriverStore\FileRepository"
        paths = {}
        if not os.path.isdir(driver_store):
            return paths

        for folder in os.listdir(driver_store):
            name = folder.lower()
            if "igd" not in name and "igfx" not in name:
                continue
            for dll in dlls:
                fp = os.path.join(driver_store, folder, dll)
                if os.path.isfile(fp) and dll not in paths:
                    paths[dll] = fp
        return paths
