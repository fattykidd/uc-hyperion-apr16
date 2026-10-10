"""Diagnostic and stream status sensors for APR-16."""

from ucapi_framework import SensorEntity
from .client import APR16Client


class AudioFormatSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="audio_codec_format",
            name="Audio Format",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def update_state_data(self) -> None:
        fmt = await self._client.get_audio_format()
        if fmt is not None:
            self.update_state(value=fmt)


class AudioSampleRateSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="audio_sample_rate",
            name="Audio Sample Rate",
            category=EntityCategory.DIAGNOSTIC,
            unit="Hz",
        )
        self._client = client

    async def update_state_data(self) -> None:
        rate = await self._client.get_audio_sample_rate()
        if rate is not None:
            self.update_state(value=rate)


class AudioBitDepthSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="audio_bit_depth",
            name="Audio Bit Depth",
            category=EntityCategory.DIAGNOSTIC,
            unit="bits",
        )
        self._client = client

    async def update_state_data(self) -> None:
        bit = await self._client.get_audio_bit_depth()
        if bit is not None:
            self.update_state(value=bit)


class VideoFormatSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="video_format_signal",
            name="Video Format",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def update_state_data(self) -> None:
        fmt = await self._client.get_video_format()
        if fmt is not None:
            self.update_state(value=fmt)


class SystemStatusSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="system_health_status",
            name="System Health Status",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def update_state_data(self) -> None:
        st = await self._client.get_system_status()
        if st is not None:
            self.update_state(value=st)


class FirmwareVersionSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="firmware_version",
            name="Firmware Version",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def update_state_data(self) -> None:
        ver_data = await self._client.get_system_version()
        if ver_data:
            self.update_state(
                value=ver_data.get("version", "Unknown"),
                attributes={
                    "api_version": ver_data.get("apiVersion"),
                    "git_commit": ver_data.get("gitCommit"),
                    "build_time": ver_data.get("buildTime"),
                },
            )


class HostIpSensorEntity(SensorEntity):
    def __init__(self, client: APR16Client):
        super().__init__(
            entity_id="primary_management_ip",
            name="Processor Management IP",
            category=EntityCategory.DIAGNOSTIC,
        )
        self._client = client

    async def update_state_data(self) -> None:
        ip = await self._client.get_host_ip()
        if ip is not None:
            self.update_state(value=ip)