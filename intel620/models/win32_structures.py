import ctypes
import ctypes.wintypes as wintypes

ENUM_CURRENT_SETTINGS = -1
ENUM_REGISTRY_SETTINGS = -2

CDS_UPDATEREGISTRY = 0x00000001
CDS_TEST = 0x00000002
CDS_GLOBAL = 0x00000008
CDS_NORESET = 0x10000000
DISP_CHANGE_SUCCESSFUL = 0

DISPLAY_DEVICE_ACTIVE = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004

DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_BITSPERPEL = 0x00040000
DM_DISPLAYFREQUENCY = 0x00400000
DM_POSITION = 0x00000020

HORZRES = 8
VERTRES = 10
BITSPIXEL = 12
PLANES = 14
LOGPIXELSX = 88
LOGPIXELSY = 90
VREFRESH = 116
DESKTOPHORZRES = 118
DESKTOPVERTRES = 117

GAMMA_SIZE = 256


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPositionX", ctypes.c_long),
        ("dmPositionY", ctypes.c_long),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


class RAMP(ctypes.Structure):
    _fields_ = [
        ("Red", wintypes.WORD * GAMMA_SIZE),
        ("Green", wintypes.WORD * GAMMA_SIZE),
        ("Blue", wintypes.WORD * GAMMA_SIZE),
    ]
