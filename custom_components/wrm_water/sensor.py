"""Sensor platform for WRM Systems Water."""
from __future__ import annotations

import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_METER_SERIAL, CONF_SUBDOMAIN, DOMAIN
from .coordinator import WRMWaterDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WRM Systems Water sensors based on a config entry."""
    coordinator: WRMWaterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            KaarinaWaterMeterReadingSensor(coordinator, entry),
            KaarinaWaterLastReportedSensor(coordinator, entry),
        ]
    )


class BaseWRMWaterSensor(CoordinatorEntity[WRMWaterDataUpdateCoordinator], SensorEntity):
    """Base class for WRM Systems Water sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WRMWaterDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._key = key
        meter_serial = entry.data[CONF_METER_SERIAL]
        subdomain = entry.data.get(CONF_SUBDOMAIN, "kaarinanvesihuolto")
        clean_subdomain = subdomain.lower().replace("-", "_").replace(".", "_")
        self.clean_subdomain = clean_subdomain

        if clean_subdomain == "kaarinanvesihuolto":
            device_name = f"Kaarinan Vesi ({meter_serial})"
        else:
            friendly_sub = subdomain.replace("-", " ").replace("_", " ").title()
            device_name = f"{friendly_sub} ({meter_serial})"

        self._attr_unique_id = f"{DOMAIN}_{meter_serial}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, meter_serial)},
            name=device_name,
            manufacturer="Axioma",
            model="Qalcosonic W1",
            configuration_url=f"https://wmd.wrm-systems.fi/{subdomain}",
        )


class KaarinaWaterMeterReadingSensor(BaseWRMWaterSensor):
    """Main water meter reading sensor (m³)."""

    _attr_translation_key = "meter_reading"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "meter_reading")
        if self.clean_subdomain == "kaarinanvesihuolto":
            self.entity_id = "sensor.kaarina_water_meter_reading"
        else:
            self.entity_id = f"sensor.{self.clean_subdomain}_water_meter_reading"

    @property
    def native_value(self) -> float | None:
        """Return the current cumulative water meter reading."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("current_reading_m3")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "last_reported": self.coordinator.data.get("last_reported"),
            "last_hour_consumption_l": self.coordinator.data.get("last_hour_liters"),
            "last_timestamp": self.coordinator.data.get("last_timestamp"),
        }


class KaarinaWaterLastReportedSensor(BaseWRMWaterSensor):
    """Sensor showing when the water meter data was last reported."""

    _attr_translation_key = "last_reported"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "last_reported")
        if self.clean_subdomain == "kaarinanvesihuolto":
            self.entity_id = "sensor.kaarina_water_last_reported"
        else:
            self.entity_id = f"sensor.{self.clean_subdomain}_last_reported"

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the timestamp when water meter data was last reported."""
        if not self.coordinator.data:
            return None
        epoch = self.coordinator.data.get("last_timestamp")
        if not epoch:
            return None
        return datetime.datetime.fromtimestamp(int(epoch), tz=datetime.timezone.utc)

