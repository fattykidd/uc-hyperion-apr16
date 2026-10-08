"""Async REST API Client for AudioControl Hyperion APR-16 Processor."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)


class APR16Client:
    """HTTP Client for communicating with AudioControl APR-16 REST API."""

    def __init__(self, host: str, port: int = 80, session: Optional[aiohttp.ClientSession] = None):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/v1"
        self._session = session
        self._own_session = False

    async def start(self) -> None:
        """Initialize HTTP session if not provided."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True

    async def close(self) -> None:
        """Close HTTP session if managed internally."""
        if self._own_session and self._session:
            await self._session.close()

    # --- System & Power ---
    async def get_power_state(self) -> Optional[str]:
        return await self._get("/power", "state")

    async def set_power_state(self, state: str) -> Optional[str]:
        return await self._post("/power", {"state": state.lower()}, "state")

    async def trigger_reboot(self) -> bool:
        res = await self._post_raw("/reboot", {})
        return res is not None

    async def get_system_status(self) -> Optional[str]:
        return await self._get("/status", "status")

    async def get_system_version(self) -> Optional[Dict[str, Any]]:
        return await self._get_full("/version")

    # --- Volume & Mute ---
    async def get_master_volume(self) -> Optional[int]:
        return await self._get("/vol", "level")

    async def set_master_volume(self, level: int) -> Optional[int]:
        return await self._post("/vol", {"level": level}, "level")

    async def get_master_mute(self) -> Optional[bool]:
        return await self._get("/mute", "state")

    async def set_master_mute(self, state: bool) -> Optional[bool]:
        return await self._post("/mute", {"state": state}, "state")

    async def get_max_volume(self) -> Optional[int]:
        return await self._get("/maxvol", "level")

    async def set_max_volume(self, level: int) -> Optional[int]:
        return await self._post("/maxvol", {"level": level}, "level")

    async def get_power_on_volume(self) -> Optional[int]:
        return await self._get("/onvol", "level")

    async def set_power_on_volume(self, level: int) -> Optional[int]:
        return await self._post("/onvol", {"level": level}, "level")

    # --- Inputs & Audio Processing ---
    async def get_input_state(self) -> Optional[str]:
        return await self._get("/inputstate", "input")

    async def set_input_state(self, input_name: str) -> Optional[str]:
        return await self._post("/inputstate", {"input": input_name}, "input")

    async def get_audio_mode(self) -> Optional[str]:
        return await self._get("/audiomode", "mode")

    async def set_audio_mode(self, mode: str) -> Optional[str]:
        return await self._post("/audiomode", {"mode": mode}, "mode")

    async def get_audio_format(self) -> Optional[str]:
        return await self._get("/audioformat", "format")

    async def get_audio_bit_depth(self) -> Optional[int]:
        return await self._get("/bit", "bit")

    async def get_audio_sample_rate(self) -> Optional[int]:
        return await self._get("/sample", "sample")

    async def get_audio_detail(self) -> Optional[str]:
        return await self._get("/audiodetail", "detail")

    async def get_video_format(self) -> Optional[str]:
        return await self._get("/videoformat", "format")

    async def get_video_detail(self) -> Optional[str]:
        return await self._get("/videodetail", "detail")

    # --- Speaker Configuration ---
    async def get_speaker_config(self, speaker_id: Any) -> Optional[Dict[str, Any]]:
        base_api = self.base_url.replace("/v1", "/api")
        res = await self._get_full(f"{base_api}/atlas/speaker/{speaker_id}", is_abs=True)
        return res.get("speaker") if res else None

    async def set_speaker_level(self, speaker_id: Any, level: float) -> Optional[Dict[str, Any]]:
        base_api = self.base_url.replace("/v1", "/api")
        return await self._post_full(f"{base_api}/atlas/speaker/{speaker_id}/lvl/{level}", {}, is_abs=True)

    # --- HDMI, EDID, HPD & Triggers ---
    async def set_hdmi_output_hpd(self, state: bool) -> Optional[Dict[str, Any]]:
        return await self._post_full("/hdmi/output/hpd", {"state": state})

    async def pulse_hdmi_output_hpd(self, delay_seconds: float = 1.5) -> bool:
        res_off = await self.set_hdmi_output_hpd(False)
        if res_off is None:
            return False
        await asyncio.sleep(delay_seconds)
        res_on = await self.set_hdmi_output_hpd(True)
        return res_on is not None and res_on.get("success", False)

    async def get_edid_config(self) -> Optional[Dict[str, Any]]:
        return await self._get_full("/edid/config")

    async def set_edid_config(self, device_name: str, enabled: bool = True) -> Optional[Dict[str, Any]]:
        payload = {"config": {"deviceName": device_name, "enabled": enabled}}
        return await self._post_full("/edid/config", payload)

    async def get_input_edid_status(self, hdmi_input: int) -> Optional[Dict[str, Any]]:
        return await self._get_full(f"/edid/input/{hdmi_input}")

    async def get_trigger_output_state(self) -> Optional[bool]:
        return await self._get("/trigger/output", "enabled")

    async def set_trigger_output_state(self, enabled: bool) -> Optional[bool]:
        return await self._post("/trigger/output", {"enabled": enabled}, "enabled")

    async def get_trigger_level(self) -> Optional[int]:
        return await self._get("/trigger/level", "level")

    async def set_trigger_level(self, level: int) -> Optional[int]:
        return await self._post("/trigger/level", {"level": level}, "level")

    async def get_trigger_input_state(self) -> Optional[bool]:
        return await self._get("/trigger/input", "active")

    async def get_host_ip(self) -> Optional[str]:
        return await self._get("/hostip", "ip")

    # --- Internal HTTP Helpers ---
    async def _get(self, endpoint: str, key: str) -> Any:
        res = await self._get_full(endpoint)
        return res.get(key) if res else None

    async def _post(self, endpoint: str, payload: dict, key: str) -> Any:
        res = await self._post_full(endpoint, payload)
        return res.get(key) if res else None

    async def _get_full(self, endpoint: str, is_abs: bool = False) -> Optional[Dict[str, Any]]:
        url = endpoint if is_abs else f"{self.base_url}{endpoint}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.error("GET %s failed: HTTP %s", url, resp.status)
        except Exception as err:
            _LOGGER.error("GET %s error: %s", url, err)
        return None

    async def _post_full(self, endpoint: str, payload: dict, is_abs: bool = False) -> Optional[Dict[str, Any]]:
        url = endpoint if is_abs else f"{self.base_url}{endpoint}"
        try:
            async with self._session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.error("POST %s failed: HTTP %s", url, resp.status)
        except Exception as err:
            _LOGGER.error("POST %s error: %s", url, err)
        return None

    async def _post_raw(self, endpoint: str, payload: dict) -> Optional[aiohttp.ClientResponse]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.post(url, json=payload) as resp:
                if resp.status in (200, 202, 204):
                    return resp
        except Exception as err:
            _LOGGER.error("POST RAW %s error: %s", url, err)
        return None