import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from intel620.models.win32_structures import DISP_CHANGE_SUCCESSFUL
from intel620.services.display_service import DisplayService

logger = logging.getLogger(__name__)

ALLOWED_THEMES = {"light", "dark", "auto"}
ALLOWED_COLOR_DEPTHS = {24, 30, 32}
ALLOWED_PROFILES = {"srgb", "dcip3", "adobergb"}


@dataclass
class ColorConfiguration:
    theme: str = "dark"
    color_depth_bpp: int = 32
    profile: str = "srgb"


class ColorConfigurationError(ValueError):
    pass


class ColorConfigurationService:
    """Applies validated color configuration to active displays at runtime."""

    def __init__(self, display_service: Optional[DisplayService] = None):
        self.display_service = display_service or DisplayService()
        self._config = ColorConfiguration()

    def get_config(self) -> Dict[str, object]:
        return asdict(self._config)

    def validate_config(self, config: ColorConfiguration) -> None:
        if config.theme not in ALLOWED_THEMES:
            raise ColorConfigurationError(f"Unsupported theme '{config.theme}'. Allowed: {sorted(ALLOWED_THEMES)}")
        if config.color_depth_bpp not in ALLOWED_COLOR_DEPTHS:
            raise ColorConfigurationError(
                f"Unsupported color depth '{config.color_depth_bpp}'. Allowed: {sorted(ALLOWED_COLOR_DEPTHS)}"
            )
        if config.profile not in ALLOWED_PROFILES:
            raise ColorConfigurationError(f"Unsupported profile '{config.profile}'. Allowed: {sorted(ALLOWED_PROFILES)}")

    def _display_supports_depth(self, device_name: str, target_depth: int) -> bool:
        for _, _, _, bpp in self.display_service.get_supported_modes(device_name):
            if bpp == target_depth:
                return True
        return False

    def apply_runtime_config(
        self,
        *,
        theme: Optional[str] = None,
        color_depth_bpp: Optional[int] = None,
        profile: Optional[str] = None,
    ) -> Dict[str, object]:
        new_config = ColorConfiguration(
            theme=theme or self._config.theme,
            color_depth_bpp=color_depth_bpp or self._config.color_depth_bpp,
            profile=profile or self._config.profile,
        )
        self.validate_config(new_config)

        devices = self.display_service.enumerate_display_devices()
        applied = 0
        skipped = []
        for dev in devices:
            if not dev["is_active"]:
                continue
            if not self._display_supports_depth(dev["device_name"], new_config.color_depth_bpp):
                skipped.append({"device": dev["device_name"], "reason": "requested color depth unsupported"})
                continue
            mode = self.display_service.get_current_mode(dev["device_name"])
            if not mode:
                skipped.append({"device": dev["device_name"], "reason": "current mode unavailable"})
                continue

            result = self.display_service.enable_display(
                device_name=dev["device_name"],
                pos_x=int(mode.dmPositionX),
                pos_y=int(mode.dmPositionY),
                width=int(mode.dmPelsWidth),
                height=int(mode.dmPelsHeight),
                freq=int(mode.dmDisplayFrequency),
                color_depth=new_config.color_depth_bpp,
            )
            if result == DISP_CHANGE_SUCCESSFUL:
                applied += 1
            else:
                skipped.append({"device": dev["device_name"], "reason": f"driver apply failed ({result})"})

        commit_code = self.display_service.commit_changes()
        if commit_code != DISP_CHANGE_SUCCESSFUL:
            logger.error("Color configuration commit failed: %s", commit_code)
            raise ColorConfigurationError(f"Color settings commit failed with code {commit_code}")

        self._config = new_config
        logger.info("Applied runtime color config to %s displays with %s skipped", applied, len(skipped))
        return {
            "config": self.get_config(),
            "applied_displays": applied,
            "skipped": skipped,
            "commit_code": commit_code,
        }
