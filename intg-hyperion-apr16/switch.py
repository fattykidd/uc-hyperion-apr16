"""Switch entities for APR-16 global settings, triggers, and HPD control."""

from ucapi_framework import SwitchEntity
from .client import APR16Client


class TriggerOutputSwitchEntity(SwitchEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="trigger_output_1",
            name="12V / 5V Hardware Trigger Output",
            category=EntityCategory.CONFIG,
        )
        self._client = client

    async def update_state_data(self) -> None:
        enabled = await self._client.get_trigger_output_state()
        if enabled is not None:
            self.update_state(value=enabled)

    async def turn_on(self) -> None:
        res = await self._client.set_trigger_output_state(True)
        if res is not None:
            self.update_state(value=res)

    async def turn_off(self) -> None:
        res = await self._client.set_trigger_output_state(False)
        if res is not None:
            self.update_state(value=res)


class HdmiOutputHpdSwitchEntity(SwitchEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="hdmi_output_hpd",
            name="HDMI Output Hotplug (HPD)",
            category=EntityCategory.CONFIG,
        )
        self._client = client

    async def turn_on(self) -> None:
        res = await self._client.set_hdmi_output_hpd(True)
        if res and res.get("success"):
            self.update_state(value=True)

    async def turn_off(self) -> None:
        res = await self._client.set_hdmi_output_hpd(False)
        if res and res.get("success"):
            self.update_state(value=False)


class EdidGlobalSwitchEntity(SwitchEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="edid_global_enable",
            name="Global EDID Advertisement",
            category=EntityCategory.CONFIG,
        )
        self._client = client

    async def update_state_data(self) -> None:
        cfg = await self._client.get_edid_config()
        if cfg is not None and "enabled" in cfg:
            self.update_state(value=bool(cfg["enabled"]))

    async def turn_on(self) -> None:
        res = await self._client.set_edid_config("APR-16", enabled=True)
        if res and res.get("success"):
            self.update_state(value=True)

    async def turn_off(self) -> None:
        res = await self._client.set_edid_config("APR-16", enabled=False)
        if res and res.get("success"):
            self.update_state(value=False)