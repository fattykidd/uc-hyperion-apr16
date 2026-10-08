"""Select entities for APR-16 audio processing modes and trigger parameters."""

from ucapi.entities import SelectEntity
from ucapi.const import EntityCategory
from .client import APR16Client
from .media_player import SOUND_MODES


class AudioModeSelectEntity(SelectEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="audio_processing_mode",
            name="Audio Processing Mode",
            category=EntityCategory.CONFIG,
            options=SOUND_MODES,
        )
        self._client = client

    async def update_state_data(self) -> None:
        mode = await self._client.get_audio_mode()
        if mode is not None:
            self.update_state(value=mode)

    async def select_option(self, option: str) -> None:
        res = await self._client.set_audio_mode(option)
        if res is not None:
            self.update_state(value=res)


class TriggerVoltageSelectEntity(SelectEntity):
    LEVEL_MAP = {"12V (Standard)": 0, "5V (TTL)": 1}
    REVERSE_MAP = {v: k for k, v in LEVEL_MAP.items()}

    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="trigger_voltage_level",
            name="Trigger Output Voltage Level",
            category=EntityCategory.CONFIG,
            options=list(self.LEVEL_MAP.keys()),
        )
        self._client = client

    async def update_state_data(self) -> None:
        lvl = await self._client.get_trigger_level()
        if lvl is not None and lvl in self.REVERSE_MAP:
            self.update_state(value=self.REVERSE_MAP[lvl])

    async def select_option(self, option: str) -> None:
        if option in self.LEVEL_MAP:
            res = await self._client.set_trigger_level(self.LEVEL_MAP[option])
            if res is not None:
                self.update_state(value=option)