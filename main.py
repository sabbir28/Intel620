"""Intel HD Graphics 620 — Display Control Panel GUI v2."""

import ctypes
import platform
import sys

from intel620.gui.panel import IntelDisplayPanel


def main():
    if platform.system() != "Windows":
        print("Windows only.")
        sys.exit(1)

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    IntelDisplayPanel().mainloop()


if __name__ == "__main__":
    main()
