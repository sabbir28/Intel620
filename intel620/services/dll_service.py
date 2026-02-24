import ctypes
import os


DLLS_TO_TRY = {
    "igc64.dll": "Intel Graphics Compiler (Core shader compilation, DX12/Vulkan/OpenGL)",
    "igd9dxva64.dll": "Intel DirectX Video Acceleration (DXVA2 hardware video decode)",
    "igdgmm64.dll": "Intel Graphics Memory Manager",
    "igdumdim64.dll": "Intel User Mode Driver (DX11/DX12)",
}


class IntelDllService:
    def __init__(self):
        self.driver_store = r"C:\Windows\System32\DriverStore\FileRepository"

    def find_intel_dll(self, dll_name):
        search_paths = [r"C:\Windows\System32", r"C:\Windows\SysWOW64", self.driver_store]
        if os.path.isdir(self.driver_store):
            for folder in os.listdir(self.driver_store):
                key = folder.lower()
                if "igd" in key or "igfx" in key or "iigd" in key:
                    search_paths.append(os.path.join(self.driver_store, folder))

        for directory in search_paths:
            full_path = os.path.join(directory, dll_name)
            if os.path.isfile(full_path):
                return full_path
        return None

    def discover_paths(self):
        return {name: self.find_intel_dll(name) for name in DLLS_TO_TRY if self.find_intel_dll(name)}

    def try_load(self):
        loaded = {}
        for dll_name in DLLS_TO_TRY:
            full_path = self.find_intel_dll(dll_name)
            if not full_path:
                loaded[dll_name] = None
                continue
            try:
                loaded[dll_name] = ctypes.WinDLL(full_path)
            except OSError:
                loaded[dll_name] = None
        return loaded

    def print_load_status(self):
        print("\n" + "=" * 60)
        print("  INTEL GPU DLL STATUS")
        print("=" * 60)
        loaded = {}
        for dll_name, description in DLLS_TO_TRY.items():
            full_path = self.find_intel_dll(dll_name)
            if full_path:
                try:
                    handle = ctypes.WinDLL(full_path)
                    status = f"✅ LOADED\n    Path    : {full_path}"
                    loaded[dll_name] = handle
                except OSError as exc:
                    status = f"⚠️  FOUND but failed to load: {exc}\n    Path    : {full_path}"
                    loaded[dll_name] = None
            else:
                status = "❌ NOT FOUND in System32, SysWOW64, or DriverStore"
                loaded[dll_name] = None

            print(f"\n  {dll_name}")
            print(f"    Purpose : {description}")
            print(f"    Status  : {status}")
        return loaded
