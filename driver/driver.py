"""Main Integration Driver implementation connecting APR16 to ucapi-framework."""

import asyncio
import logging
import sys
from ucapi.driver import Driver
from ucapi.const import DriverState

from .client import APR16Client
from .media_player import APR16MediaPlayerEntity
from .number import MaxVolumeNumberEntity, PowerOnVolumeNumberEntity
from .select import AudioModeSelectEntity, TriggerVoltageSelectEntity
from .sensor import (
    AudioFormatSensorEntity,
    AudioSampleRateSensorEntity,
    AudioBitDepthSensorEntity,
    VideoFormatSensorEntity,
    SystemStatusSensorEntity,
    FirmwareVersionSensorEntity,
    HostIpSensorEntity,
)
from .switch import TriggerOutputSwitchEntity, HdmiOutputHpdSwitchEntity, EdidGlobalSwitchEntity
from .button import SystemRebootButtonEntity, HdmiHandshakeResetButtonEntity

_LOGGER = logging.getLogger(__name__)


class APR16Driver:
    """Unfolded Circle integration driver for AudioControl Hyperion APR-16."""

    def __init__(self):
        self.driver = Driver("uc-hyperion-apr16")
        self.client: APR16Client | None = None
        self._poll_task: asyncio.Task | None = None

        # Register callbacks
        self.driver.on_setup = self.on_setup
        self.driver.on_connect = self.on_connect
        self.driver.on_disconnect = self.on_disconnect

    async def on_setup(self, setup_data: dict) -> DriverState:
        """Process user setup configuration from Remote 3 UI."""
        host = setup_data.get("host")
        port = setup_data.get("port", 80)

        if not host:
            _LOGGER.error("Setup failed: Host IP address is required")
            return DriverState.SETUP_ERROR

        self.client = APR16Client(host=host, port=port)
        await self.client.start()

        # Instantiate entities
        mp = APR16MediaPlayerEntity(self.client)
        max_vol = MaxVolumeNumberEntity(self.client)
        on_vol = PowerOnVolumeNumberEntity(self.client)
        audio_mode = AudioModeSelectEntity(self.client)
        trig_volt = TriggerVoltageSelectEntity(self.client)
        trig_switch = TriggerOutputSwitchEntity(self.client)
        hpd_switch = HdmiOutputHpdSwitchEntity(self.client)
        edid_switch = EdidGlobalSwitchEntity(self.client)
        reboot_btn = SystemRebootButtonEntity(self.client)
        hpd_btn = HdmiHandshakeResetButtonEntity(self.client)

        fmt_sensor = AudioFormatSensorEntity(self.client)
        rate_sensor = AudioSampleRateSensorEntity(self.client)
        bit_sensor = AudioBitDepthSensorEntity(self.client)
        vfmt_sensor = VideoFormatSensorEntity(self.client)
        status_sensor = SystemStatusSensorEntity(self.client)
        ver_sensor = FirmwareVersionSensorEntity(self.client)
        ip_sensor = HostIpSensorEntity(self.client)

        # Register entities with driver
        entities = [
            mp, max_vol, on_vol, audio_mode, trig_volt, trig_switch,
            hpd_switch, edid_switch, reboot_btn, hpd_btn, fmt_sensor,
            rate_sensor, bit_sensor, vfmt_sensor, status_sensor,
            ver_sensor, ip_sensor
        ]
        for entity in entities:
            self.driver.add_entity(entity)

        return DriverState.CONNECTED

    async def on_connect(self) -> None:
        """Start background polling on successful connection."""
        _LOGGER.info("Driver connected, starting background polling loop")
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def on_disconnect(self) -> None:
        """Clean up background tasks on disconnect."""
        _LOGGER.info("Driver disconnected")
        if self._poll_task:
            self._poll_task.cancel()
        if self.client:
            await self.client.close()

    async def _poll_loop(self) -> None:
        """Periodically refresh state for all registered entities."""
        while True:
            try:
                for entity in self.driver.entities.values():
                    if hasattr(entity, "update_state_data"):
                        await entity.update_state_data()
            except Exception as err:
                _LOGGER.error("Error in background polling loop: %s", err)
            await asyncio.sleep(4)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    driver_wrapper = APR16Driver()
    asyncio.run(driver_wrapper.driver.run())