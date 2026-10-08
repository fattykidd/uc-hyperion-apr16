"""Action buttons for APR-16 system maintenance and recovery."""

from ucapi.entities import ButtonEntity
from ucapi.const import EntityCategory
from .client import APR16Client


class SystemRebootButtonEntity(ButtonEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="system_reboot",
            name="Reboot APR-16 Processor",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def press(self) -> None:
        await self._client.trigger_reboot()


class HdmiHandshakeResetButtonEntity(ButtonEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="hdmi_handshake_reset",
            name="Reset HDMI Handshake (HPD Pulse)",
            category=EntityCategory.CONFIG,
        )
        self._client = client

    async def press(self) -> None:
        await self._client.pulse_hdmi_output_hpd(delay_seconds=1.5)