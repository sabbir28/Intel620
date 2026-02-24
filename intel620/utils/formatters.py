def fmt_bytes(val):
    try:
        size = int(val)
        if size == 0:
            return "Shared (Dynamic VRAM)"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return str(val)


def fmt_kb(val):
    try:
        kb = int(val)
        return f"{kb/1024/1024:.2f} GB  ({kb:,} KB)"
    except Exception:
        return str(val)
