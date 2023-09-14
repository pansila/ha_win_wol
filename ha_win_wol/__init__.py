import asyncio
import json
import requests
from homeassistant import config_entries, core
from .const import (
    DOMAIN
)
import logging
import subprocess
from functools import partial

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady
_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "switch",
]

async def async_setup(hass: core.HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry):
    _LOGGER.info("Setting up My Device component")

    key = entry.data.get('key')
    method = 'CheckKey'
    # 获取服务器url信息
    url = f"http://hass.07110712.xyz:18868/{method}"
    headers = {
        
    }
    data = {
        "key": key,
    }

    try:
        # 使用 functools.partial 创建一个新的函数，将 headers 作为默认参数传递给 requests.post()
        request_func = partial(requests.post, url, headers=headers, json=data)               
        response = await hass.async_add_executor_job(request_func)
        _LOGGER.debug(f"请求服务器返回response: {response.json()}")
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        _LOGGER.debug(f"请求服务器返回 An error occurred: {e}")    

    if response_data['code'] != 200:
        return False

    ip = entry.data.get('ip')
    name = entry.data.get('name')
    mac = entry.data.get('mac')

    result = subprocess.run(["ping", "-n", "1", "-w", "1000", ip], capture_output=True, text=True)

    if result.returncode == 0:
        status = "0"
    else:
        status = "-1"

    _LOGGER.info(f"获取初始化信息完成，开始创建设备IP: {ip}, Name:{name}, Mac:{mac}, Status: {status}")

    coordinator = DEVICEDataUpdateCoordinator(hass, entry, ip, name, mac, status)

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][ip] = coordinator

    _LOGGER.info(f"创建设备完成IP: {ip}, Name:{name}, Mac:{mac}, Status: {status}")

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True

async def update_listener(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    return unload_ok

class DEVICEDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching DEVICE data."""

    def __init__(self, hass, entry, ip, name, mac, status):
        self.hass = hass
        self.entry = entry

        self.ip = ip
        self.name = name
        self.mac = mac
        self.status = status

        self._isenable = True

        super().__init__(
            hass,
            _LOGGER,
            name=self.name,
            update_interval=300,
        )

    def set_device_enabled(self, enabled):
        # 设置设备是否可用
        self._isenable = enabled

    async def _async_update_data(self):
        """Fetch data from My Custom Device."""
        try:
            return json.loads('{"ip":"'+ self.ip 
                              +'","name":"'+ self.name 
                              +'","status":"'+ self.status +'"}')  
        except Exception as err:
            raise UpdateFailed(f"Error communicating with My Custom Device: {err}")
        