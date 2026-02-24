import ctypes
from ctypes import byref


class DxgiService:
    def get_dxgi_info(self):
        try:
            dxgi = ctypes.WinDLL("dxgi.dll")
        except OSError:
            return {"error": "dxgi.dll not found"}

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        iid = GUID()
        iid.Data1 = 0x770AAE78
        iid.Data2 = 0xF26F
        iid.Data3 = 0x4DBA
        iid.Data4 = (ctypes.c_ubyte * 8)(0xA8, 0x29, 0x25, 0x3C, 0x83, 0xD1, 0xB3, 0x87)

        factory = ctypes.c_void_p()
        hr = dxgi.CreateDXGIFactory1(byref(iid), byref(factory))
        if hr != 0 or not factory:
            return {"error": f"CreateDXGIFactory1 failed (hr=0x{hr & 0xFFFFFFFF:08X})"}

        return {
            "status": "✅ DXGI Factory1 created successfully",
            "note": "Install comtypes (pip install comtypes) for full adapter/output enumeration",
        }
