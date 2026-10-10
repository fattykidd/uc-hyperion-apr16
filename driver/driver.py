"""Main Integration Driver implementation connecting APR16 to ucapi-framework."""

import asyncio
import logging
from ucapi_framework import BaseIntegrationDriver
from ucapi import StatusCodes

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
        super().__init__(
            device_class=APR16Client,
            entity_classes=[
                APR16MediaPlayerEntity,
                AudioModeSelectEntity,
                TriggerVoltageSelectEntity,
                TriggerOutputSwitchEntity,
                HdmiOutputHpdSwitchEntity,
                EdidGlobalSwitchEntity,
                SystemRebootButtonEntity,
                HdmiHandshakeResetButtonEntity,
                AudioFormatSensorEntity,
                AudioSampleRateSensorEntity,
                AudioBitDepthSensorEntity,
                VideoFormatSensorEntity,
                SystemStatusSensorEntity,
                FirmwareVersionSensorEntity,
                HostIpSensorEntity,
            ]
        )
        self.client: APR16Client | None = None
        self._poll_task: asyncio.Task | None = None
        self._connected = False

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

        # Add the configured device to the framework. 
        # The framework automatically instantiates and registers all entity_classes 
        # passed to super().__init__() for this device instance.
        self.add_configured_device(setup_data, connect=True)

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
                for entity in self.api.configured_entities.values():
                    if hasattr(entity, "update_state_data"):
                        await entity.update_state_data()
            except Exception as err:
                _LOGGER.error("Error in background polling loop: %s", err)
            await asyncio.sleep(4)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Instantiate the driver
    driver_wrapper = APR16Driver()
    
    _LOGGER.info("Starting AudioControl Hyperion APR-16 integration driver...")
    
    # Run the asyncio event loop indefinitely to keep the driver active
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        _LOGGER.info("Driver stopped by user")