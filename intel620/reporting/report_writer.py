import json


class ReportWriter:
    def save_report(self, devices, dll_status, out_path="intel_display_report.json"):
        report = {
            "intel_dll_status": {k: ("loaded" if v else "not_found") for k, v in dll_status.items()},
            "display_devices": devices,
        }
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        return out_path
