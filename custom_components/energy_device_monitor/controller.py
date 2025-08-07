"""Controller module for managing energy device data.

This module provides the Controller class for handling logic related to energy devices,
including storing device information and providing methods to access or update device state.
"""

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change_event


class Controller:
    """Controller for managing energy device data.

    This class handles the logic for interacting with energy devices,
    storing device information, and providing methods to access or update device state.
    """

    low_tariff_entity_id: str
    high_tariff_entity_id: str
    low_tariff_state: State | None = None
    high_tariff_state: State | None = None

    def __init__(
        self, hass: HomeAssistant, low_tariff_entity_id: str, high_tariff_entity_id: str
    ) -> None:
        """Initialize the controller with device data.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            low_tariff_entity_id (str): The entity ID for the low tariff sensor.
            high_tariff_entity_id (str): The entity ID for the high tariff sensor.
        """

        self.low_tariff_entity_id = low_tariff_entity_id
        self.high_tariff_entity_id = high_tariff_entity_id

        async_track_state_change_event(
            hass,
            [self.low_tariff_entity_id, self.high_tariff_entity_id],
            self._handle_state_change,
        )

    async def _handle_state_change(self, event) -> None:
        await self.async_update_ha_state(True)

    @property
    def low_tariff_state(self) -> State | None:
        """Return the current state of the low tariff entity."""
        return self.low_tariff_state

    @property
    def high_tariff_state(self) -> State | None:
        """Return the current state of the high tariff entity."""
        return self.high_tariff_state
