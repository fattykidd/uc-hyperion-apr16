"""Number entities for APR-16 volume safety limits and channel trims."""

from ucapi.entities import NumberEntity
from ucapi.const import EntityCategory
from .client import APR16Client


class MaxVolumeNumberEntity(NumberEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="max_volume_limit",
            name="Max Volume Safety Limit",
            category=EntityCategory.CONFIG,
            min_value=0,
            max_value=100,
            step=1,
        )
        self._client = client

    async def update_state_data(self) -> None:
        val = await self._client.get_max_volume()
        if val is not None:
            self.update_state(value=val)

    async def set_value(self, value: float) -> None:
        res = await self._client.set_max_volume(int(value))
        if res is not None:
            self.update_state(value=res)


class PowerOnVolumeNumberEntity(NumberEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="power_on_volume_default",
            name="Power-On Default Volume",
            category=EntityCategory.CONFIG,
            min_value=0,
            max_value=100,
            step=1,
        )
        self._client = client

    async def update_state_data(self) -> None:
        val = await self._client.get_power_on_volume()
        if val is not None:
            self.update_state(value=val)

    async def set_value(self, value: float) -> None:
        res = await self._client.set_power_on_volume(int(value))
        if res is not None:
            self.update_state(value=res)


class SpeakerLevelTrimNumberEntity(NumberEntity):
    def __init__(self, client: APR16Client, speaker_id: str, speaker_name: str):
        self._speaker_id = speaker_id
        super().__init__(
            entity_id=f"speaker_{speaker_id}_level_trim",
            name=f"{speaker_name} Trim Level",
            category=EntityCategory.CONFIG,
            min_value=-20.0,
            max_value=10.0,
            step=0.5,
            unit="dB",
        )
        self._client = client

    async def update_state_data(self) -> None:
        cfg = await self._client.get_speaker_config(self._speaker_id)
        if cfg and "lvl" in cfg:
            self.update_state(value=float(cfg["lvl"]))

    async def set_value(self, value: float) -> None:
        res = await self._client.set_speaker_level(self._speaker_id, value)
        if res is not None:
            self.update_state(value=value)