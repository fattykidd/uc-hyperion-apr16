"""Main Integration Driver implementation connecting APR16 to ucapi-framework."""

import asyncio
import logging
import sys
from ucapi_framework import (
    BaseIntegrationDriver,
    MediaPlayerEntity,
    SelectEntity,
    SwitchEntity,
    SensorEntity,
    ButtonEntity,
)
from ucapi import DeviceStates, StatusCodes

from .client import APR16Client
from .media_player import APR16MediaPlayerEntity
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


class APR16Driver(BaseIntegrationDriver):
    """Unfolded Circle integration driver for AudioControl Hyperion APR-16."""
    def __init__(self):
        super().__init__()
        self.client: APR16Client | None = None
        self._poll_task: asyncio.Task | None = None
        self._connected = False

        # Register the lifecycle callbacks expected by ucapi-framework.
        # These methods are the integration points for setup, connect,
        # and disconnect events; they are intentionally assigned here so
        # the framework can invoke them when the driver starts and stops.
        self.driver.on_setup = self.on_setup
        self.driver.on_connect = self.on_connect
        self.driver.on_disconnect = self.on_disconnect

        # Ensure the driver starts in a known clean state even before the
        # framework has connected any devices or clients.
        self.driver.set_available(True)

    async def _shutdown_client(self) -> None:
        """Close any existing client and clear the reference."""
        if self.client:
            await self.client.close()
            self.client = None

    async def on_setup(self, setup_data: dict):
        """Process user setup configuration from Remote 3 UI."""
        host = setup_data.get("host")
        port = setup_data.get("port", 80)

        if not host:
            _LOGGER.error("Setup failed: Host IP address is required")
            return StatusCodes.SETUP_ERROR

        try:
            port = int(port)
        except (TypeError, ValueError):
            _LOGGER.error("Setup failed: Port must be an integer, got %r", port)
            return StatusCodes.SETUP_ERROR

        await self._shutdown_client()

        self.client = APR16Client(host=host, port=port)
        try:
            await self.client.start()
        except Exception as err:
            _LOGGER.exception("Setup failed while connecting to APR16 at %s:%s: %s", host, port, err)
            self.client = None
            return StatusCodes.SETUP_ERROR

        # Instantiate entities
        mp = APR16MediaPlayerEntity(self.client)
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
            mp, audio_mode, trig_volt, trig_switch,
            hpd_switch, edid_switch, reboot_btn, hpd_btn, fmt_sensor,
            rate_sensor, bit_sensor, vfmt_sensor, status_sensor,
            ver_sensor, ip_sensor
        ]
        for entity in entities:
            self.driver.add_entity(entity)

        return StatusCodes.OK

    async def on_connect(self) -> None:
        """Start background polling on successful connection."""
        if self._connected:
            return

        _LOGGER.info("Driver connected, starting background polling loop")
        self._connected = True
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def on_disconnect(self) -> None:
        """Clean up background tasks on disconnect."""
        _LOGGER.info("Driver disconnected")
        self._connected = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            finally:
                self._poll_task = None

        await self._shutdown_client()

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