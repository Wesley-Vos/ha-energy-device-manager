"""Config flow for the Energy device monitor integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.input_number import DOMAIN as INPUT_NUMBER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_DEVICE_KEY,
    CONF_DEVICE_NAME,
    CONF_HIGH_CONSUMPTION_ENTITY,
    CONF_HIGH_TARIFF_ENTITY,
    CONF_LOW_CONSUMPTION_ENTITY,
    CONF_LOW_TARIFF_ENTITY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LOW_TARIFF_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]),
        ),
        vol.Required(CONF_HIGH_TARIFF_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]),
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input."""

    return {
        "title": "Energy Device Monitor",
        "low_tariff_entity": data[CONF_LOW_TARIFF_ENTITY],
        "high_tariff_entity": data[CONF_HIGH_TARIFF_ENTITY],
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy device monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            info = await validate_input(self.hass, user_input)

            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"device": DeviceSubentryFlowHandler}


SUB_STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_NAME): str,
        vol.Required(CONF_DEVICE_KEY): str, vol.Required(CONF_LOW_CONSUMPTION_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]),
        ),
        vol.Required(CONF_HIGH_CONSUMPTION_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN]),
        ),
    }
)


async def validate_device_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the device user input."""

    return {
        "device_name": data[CONF_DEVICE_NAME],
        "device_key": data[CONF_DEVICE_KEY],
        "low_consumption_entity": data[CONF_LOW_CONSUMPTION_ENTITY],
        "high_consumption_entity": data[CONF_HIGH_CONSUMPTION_ENTITY],
    }


class DeviceSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying a device."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            info = await validate_device_input(self.hass, user_input)

            return self.async_create_entry(title=info["device_name"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=SUB_STEP_USER_DATA_SCHEMA, errors=errors
        )
