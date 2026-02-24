import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from intel620.models.win32_structures import DISP_CHANGE_SUCCESSFUL
from intel620.services.display_service import DisplayService

logger = logging.getLogger(__name__)


class GraphicsLifecycleEvent(str, Enum):
    STARTUP = "startup"
    WAKE = "wake"
    MANUAL_RESET = "manual_reset"


@dataclass(frozen=True)
class GraphicsResetResult:
    event: GraphicsLifecycleEvent
    refreshed_displays: int
    commit_code: int
    success: bool
    message: str


class GraphicsLifecycleService:
    """Coordinates safe graphics refresh behavior across lifecycle events."""

    def __init__(self, display_service: Optional[DisplayService] = None):
        self.display_service = display_service or DisplayService()

    def trigger_refresh(self, event: GraphicsLifecycleEvent) -> GraphicsResetResult:
        detection = self.display_service.detect_displays()
        refreshed = 0

        for display in detection["all"]:
            if not display.is_active:
                continue
            mode = self.display_service.get_current_mode(display.device_name)
            if not mode:
                logger.warning("Skipping display %s: current mode unavailable", display.device_name)
                continue

            result = self.display_service.enable_display(
                device_name=display.device_name,
                pos_x=int(mode.dmPositionX),
                pos_y=int(mode.dmPositionY),
                width=int(mode.dmPelsWidth),
                height=int(mode.dmPelsHeight),
                freq=int(mode.dmDisplayFrequency),
                color_depth=int(mode.dmBitsPerPel),
            )
            if result != DISP_CHANGE_SUCCESSFUL:
                logger.error("Display refresh test failed for %s with code %s", display.device_name, result)
                continue
            refreshed += 1

        commit_code = self.display_service.commit_changes()
        success = commit_code == DISP_CHANGE_SUCCESSFUL
        message = "Graphics stack refreshed" if success else f"Commit failed with code {commit_code}"

        logger.info(
            "Graphics refresh complete event=%s refreshed=%s success=%s",
            event.value,
            refreshed,
            success,
        )
        return GraphicsResetResult(
            event=event,
            refreshed_displays=refreshed,
            commit_code=commit_code,
            success=success,
            message=message,
        )

    def initialize_for_startup(self) -> GraphicsResetResult:
        return self.trigger_refresh(GraphicsLifecycleEvent.STARTUP)

    def initialize_for_wake(self) -> GraphicsResetResult:
        return self.trigger_refresh(GraphicsLifecycleEvent.WAKE)

    def manual_reset(self) -> GraphicsResetResult:
        return self.trigger_refresh(GraphicsLifecycleEvent.MANUAL_RESET)

    def get_runtime_state(self) -> Dict[str, object]:
        detection = self.display_service.detect_displays()
        return {
            "active_displays": detection["active_count"],
            "primary_display": detection["primary"].device_name if detection["primary"] else None,
            "secondary_displays": [d.device_name for d in detection["secondary"]],
        }
