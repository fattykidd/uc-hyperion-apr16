"""Media Player Entity implementation for AudioControl Hyperion APR-16."""

import logging

# Entity base class from ucapi-framework
from ucapi_framework import MediaPlayerEntity, MediaPlayerAttributes

# Commands, features, and states from ucapi.media_player or ucapi
from ucapi.media_player import (
    Commands as MediaPlayerCommand,
    Features as MediaPlayerFeature,
    States as MediaPlayerState,
)
from .client import APR16Client

_LOGGER = logging.getLogger(__name__)

INPUT_SOURCES = [
    "HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4",
    "HDMI 5", "HDMI 6", "HDMI 7", "eARC",
    "Coaxial 1", "Coaxial 2", "Optical 1", "Optical 2",
    "Analog 1", "Analog 2", "Dante"
]

SOUND_MODES = [
    "Direct", "Stereo", "All Channel Stereo",
    "Dolby Surround", "DTS Neural:X", "Auro-3D", "Native / Auto"
]


class APR16MediaPlayerEntity(MediaPlayerEntity):
    """Core Media Player entity exposing APR-16 control to Remote 3."""

    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="apr16_processor",
            name="Hyperion APR-16 Processor",
            features=[
                MediaPlayerFeature.POWER,
                MediaPlayerFeature.POWER_TOGGLE,
                MediaPlayerFeature.VOLUME,
                MediaPlayerFeature.VOLUME_UP_DOWN,
                MediaPlayerFeature.MUTE,
                MediaPlayerFeature.MUTE_TOGGLE,
                MediaPlayerFeature.SELECT_SOURCE,
                MediaPlayerFeature.SELECT_SOUND_MODE,
            ],
            source_list=INPUT_SOURCES,
            sound_mode_list=SOUND_MODES,
        )
        self.client = client

    async def update_state_data(self) -> None:
        """Poll system state and refresh entity properties."""
        pwr = await self.client.get_power_state()
        is_on = pwr and pwr.lower() == "on"

        if not is_on:
            self.update_state(state=MediaPlayerState.OFF)
            return

        vol = await self.client.get_master_volume()
        muted = await self.client.get_master_mute()
        inp = await self.client.get_input_state()
        mode = await self.client.get_audio_mode()
        fmt = await self.client.get_audio_format()
        v_fmt = await self.client.get_video_format()

        attributes = {}
        if fmt:
            attributes["audio_format"] = fmt
        if v_fmt:
            attributes["video_format"] = v_fmt

        self.update_state(
            state=MediaPlayerState.ON,
            volume_level=vol,
            is_muted=bool(muted),
            source=inp,
            sound_mode=mode,
            media_type=fmt if fmt else "Audio",
            attributes=attributes,
        )

    async def handle_command(self, command: MediaPlayerCommand, **kwargs) -> None:
        """Process incoming media player commands from Unfolded Circle API."""
        _LOGGER.debug("Handling media player command: %s (%s)", command, kwargs)

        if command == MediaPlayerCommand.POWER_ON:
            await self.client.set_power_state("on")
            self.update_state(state=MediaPlayerState.ON)

        elif command == MediaPlayerCommand.POWER_OFF:
            await self.client.set_power_state("off")
            self.update_state(state=MediaPlayerState.OFF)

        elif command == MediaPlayerCommand.POWER_TOGGLE:
            curr = await self.client.get_power_state()
            target = "off" if curr and curr.lower() == "on" else "on"
            await self.client.set_power_state(target)
            self.update_state(state=MediaPlayerState.ON if target == "on" else MediaPlayerState.OFF)

        elif command == MediaPlayerCommand.VOLUME:
            target_vol = int(kwargs.get("volume", 0))
            res = await self.client.set_master_volume(target_vol)
            if res is not None:
                self.update_state(volume_level=res)

        elif command in (MediaPlayerCommand.VOLUME_UP, MediaPlayerCommand.VOLUME_DOWN):
            curr_vol = await self.client.get_master_volume() or 0
            step = 1 if command == MediaPlayerCommand.VOLUME_UP else -1
            res = await self.client.set_master_volume(max(0, min(100, curr_vol + step)))
            if res is not None:
                self.update_state(volume_level=res)

        elif command == MediaPlayerCommand.MUTE:
            await self.client.set_master_mute(True)
            self.update_state(is_muted=True)

        elif command == MediaPlayerCommand.UNMUTE:
            await self.client.set_master_mute(False)
            self.update_state(is_muted=False)

        elif command == MediaPlayerCommand.MUTE_TOGGLE:
            curr_mute = await self.client.get_master_mute()
            res = await self.client.set_master_mute(not curr_mute)
            if res is not None:
                self.update_state(is_muted=res)

        elif command == MediaPlayerCommand.SELECT_SOURCE:
            src = kwargs.get("source")
            if src:
                res = await self.client.set_input_state(src)
                if res:
                    self.update_state(source=res)

        elif command == MediaPlayerCommand.SELECT_SOUND_MODE:
            mode = kwargs.get("sound_mode")
            if mode:
                res = await self.client.set_audio_mode(mode)
                if res:
                    self.update_state(sound_mode=res)