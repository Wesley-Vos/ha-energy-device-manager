"""Energy device monitor sensor entities for Home Assistant."""

from dataclasses import dataclass
from datetime import datetime, time
import zoneinfo

from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import STATE_UNAVAILABLE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import EnergyDeviceMonitorConfigEntry
from .const import (
    CONF_DEVICE_FRIENDLY_NAME,
    CONF_DEVICE_NAME,
    CONF_HIGH_CONSUMPTION_ENTITY,
    CONF_HIGH_TARIFF_ENTITY,
    CONF_LOW_CONSUMPTION_ENTITY,
    CONF_LOW_TARIFF_ENTITY,
)


@dataclass
class EnergyDeviceEntityState:  # noqa: D101
    available: bool
    state: float | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EnergyDeviceMonitorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the energy device monitor sensor entities."""

    for subentry in entry.subentries.values():
        if subentry.subentry_type != "device":
            continue

        entities = [
            DailyLowCostSensor(hass, entry, subentry),
            DailyHighCostSensor(hass, entry, subentry),
            TotalDailyCostSensor(hass, entry, subentry),
            TotalDailyConsumptionSensor(hass, entry, subentry),
        ]

        async_add_entities(
            entities, update_before_add=True, config_subentry_id=subentry.subentry_id
        )


class EnergyDeviceMonitorSensor(SensorEntity):
    """Representation of an energy device monitor sensor."""

    _attr_has_entity_name = True

    _entry: EnergyDeviceMonitorConfigEntry
    _subentry: ConfigSubentry
    _device_name: str
    _device_friendly_name: str

    _include_low_consumption: bool
    _include_high_consumption: bool
    _include_low_tariff: bool
    _include_high_tariff: bool

    low_tariff_state: EnergyDeviceEntityState
    high_tariff_state: EnergyDeviceEntityState
    low_consumption_state: EnergyDeviceEntityState
    high_consumption_state: EnergyDeviceEntityState

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EnergyDeviceMonitorConfigEntry,
        subentry: ConfigSubentry,
        include_low_consumption: bool = False,
        include_high_consumption: bool = False,
        include_low_tariff: bool = False,
        include_high_tariff: bool = False,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._subentry = subentry
        self._device_name = subentry.data[CONF_DEVICE_NAME]
        self._device_friendly_name = subentry.data[CONF_DEVICE_FRIENDLY_NAME]
        self._include_low_consumption = include_low_consumption
        self._include_high_consumption = include_high_consumption
        self._include_low_tariff = include_low_tariff
        self._include_high_tariff = include_high_tariff
    
        self._attr_translation_placeholders = {"device_name": self._device_friendly_name.lower()}

        entities_to_track = []
        if include_low_tariff:
            entities_to_track.append(entry.data[CONF_LOW_TARIFF_ENTITY])
        if include_high_tariff:
            entities_to_track.append(entry.data[CONF_HIGH_TARIFF_ENTITY])
        if include_low_consumption:
            entities_to_track.append(subentry.data[CONF_LOW_CONSUMPTION_ENTITY])
        if include_high_consumption:
            entities_to_track.append(subentry.data[CONF_HIGH_CONSUMPTION_ENTITY])

        async_track_state_change_event(
            self.hass,
            entities_to_track,
            self._handle_state_change,
        )

    async def _handle_state_change(self, event) -> None:
        await self.async_update_ha_state(True)

    async def async_update(self) -> None:
        """Update the sensor state."""
        if self._include_low_tariff:
            self.low_tariff_state = await self._async_update_entity_state(
                self._entry.data[CONF_LOW_TARIFF_ENTITY]
            )
        if self._include_high_tariff:
            self.high_tariff_state = await self._async_update_entity_state(
                self._entry.data[CONF_HIGH_TARIFF_ENTITY]
            )
        if self._include_low_consumption:
            self.low_consumption_state = await self._async_update_entity_state(
                self._subentry.data[CONF_LOW_CONSUMPTION_ENTITY]
            )
        if self._include_high_consumption:
            self.high_consumption_state = await self._async_update_entity_state(
                self._subentry.data[CONF_HIGH_CONSUMPTION_ENTITY]
            )

    async def _async_update_entity_state(
        self, entity_id: str
    ) -> EnergyDeviceEntityState:
        """Helper to update and return the state for a given entity ID."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state is None or state.state == STATE_UNAVAILABLE:
            return EnergyDeviceEntityState(available=False)
        try:
            return EnergyDeviceEntityState(state=float(state.state), available=True)
        except ValueError:
            return EnergyDeviceEntityState(available=False)


class TotalDailyCostSensor(EnergyDeviceMonitorSensor):
    """Representation of a total daily cost sensor for the energy device monitor."""

    _attr_translation_key = "total_cost"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EnergyDeviceMonitorConfigEntry,
        sub_entry: ConfigSubentry,
    ) -> None:
        """Initialize the total daily cost sensor."""
        super().__init__(
            hass,
            entry,
            sub_entry,
            include_low_tariff=True,
            include_low_consumption=True,
            include_high_tariff=True,
            include_high_consumption=True,
        )
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"util_cost_{self._device_name}_daily", hass=hass
        )
        self._attr_unique_id = f"{self._device_name}_total_daily_cost_sensor"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_suggested_display_precision = 2
        self._attr_state_class = SensorStateClass.TOTAL


    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return (
            self.low_tariff_state.available
            and self.high_tariff_state.available
            and self.low_consumption_state.available
            and self.high_consumption_state.available
        )

    @property
    def native_value(self) -> float:
        """Return the current value of the sensor."""
        return (self.low_tariff_state.state * self.low_consumption_state.state) + (
            self.high_tariff_state.state * self.high_consumption_state.state
        )

    @property
    def last_reset(self) -> datetime:
        """Return the last reset time for the sensor."""
        tz = zoneinfo.ZoneInfo(self.hass.config.time_zone)
        return datetime.combine(datetime.now(tz).date(), time.min, tzinfo=tz)


class DailyLowCostSensor(EnergyDeviceMonitorSensor):
    """Representation of a daily low cost sensor for the energy device monitor."""
    
    _attr_translation_key = "low_cost"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EnergyDeviceMonitorConfigEntry,
        sub_entry: ConfigSubentry,
    ) -> None:
        """Initialize the daily low cost sensor."""
        super().__init__(
            hass,
            entry,
            sub_entry,
            include_low_tariff=True,
            include_low_consumption=True,
        )
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"util_cost_{self._device_name}_t1_daily", hass=hass
        )
        self._attr_unique_id = f"{self._device_name}_daily_low_cost_sensor"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_suggested_display_precision = 2

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return self.low_tariff_state.available and self.low_consumption_state.available

    @property
    def native_value(self) -> float:
        """Return the current value of the sensor."""
        return self.low_tariff_state.state * self.low_consumption_state.state


class DailyHighCostSensor(EnergyDeviceMonitorSensor, SensorEntity):
    """Representation of a daily high cost sensor for the energy device monitor."""
    
    _attr_translation_key = "high_cost"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EnergyDeviceMonitorConfigEntry,
        sub_entry: ConfigSubentry,
    ) -> None:
        """Initialize the daily high cost sensor."""
        super().__init__(
            hass,
            entry,
            sub_entry,
            include_high_tariff=True,
            include_high_consumption=True,
        )
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"util_cost_{self._device_name}_t2_daily", hass=hass
        )
        self._attr_unique_id = f"{self._device_name}_sensor_daily_high_cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_suggested_display_precision = 2

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return (
            self.high_tariff_state.available and self.high_consumption_state.available
        )

    @property
    def native_value(self) -> float:
        """Return the current value of the sensor."""
        return self.high_tariff_state.state * self.high_consumption_state.state


class TotalDailyConsumptionSensor(EnergyDeviceMonitorSensor, SensorEntity):
    """Representation of a total daily consumption sensor for the energy device monitor."""
    
    _attr_translation_key = "total_consumption"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EnergyDeviceMonitorConfigEntry,
        sub_entry: ConfigSubentry,
    ) -> None:
        """Initialize the total daily consumption sensor."""
        super().__init__(
            hass,
            entry,
            sub_entry,
            include_low_consumption=True,
            include_high_consumption=True,
        )
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"util_energy_{self._device_name}_daily", hass=hass
        )
        self._attr_unique_id = f"{self._device_name}_total_daily_consumption_sensor"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_suggested_display_precision = 3
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return (
            self.low_consumption_state.available
            and self.high_consumption_state.available
        )

    @property
    def native_value(self) -> float:
        """Return the current value of the sensor."""
        return self.low_consumption_state.state + self.high_consumption_state.state
