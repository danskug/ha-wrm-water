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
            KaarinaWaterYesterdaySensor(coordinator, entry),
            KaarinaWaterTodaySensor(coordinator, entry),
            KaarinaWaterMonthlySensor(coordinator, entry),
            KaarinaWaterLastHourSensor(coordinator, entry),
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

        self._attr_unique_id = f"{DOMAIN}_{meter_serial}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, meter_serial)},
            name=f"Kaarinan Vesi ({meter_serial})",
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
        # Ensure default entity_id is sensor.kaarina_water_meter_reading for seamless compatibility
        self.entity_id = "sensor.kaarina_water_meter_reading"

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


class KaarinaWaterYesterdaySensor(BaseWRMWaterSensor):
    """Yesterday's total water consumption in liters."""

    _attr_translation_key = "yesterday_liters"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_icon = "mdi:water"

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "yesterday_liters")
        self.entity_id = "sensor.kaarina_water_yesterday_liters"

    @property
    def native_value(self) -> float | None:
        """Return yesterday's total water consumption in liters."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("yesterday_liters")


class KaarinaWaterTodaySensor(BaseWRMWaterSensor):
    """Today's preliminary water consumption in liters."""

    _attr_translation_key = "today_liters"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_icon = "mdi:water-pump"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "today_liters")
        self.entity_id = "sensor.kaarina_water_daily_liters"

    @property
    def native_value(self) -> float | None:
        """Return today's water consumption in liters."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("today_liters")


class KaarinaWaterMonthlySensor(BaseWRMWaterSensor):
    """Current month's water consumption in m³."""

    _attr_translation_key = "monthly_consumption"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_icon = "mdi:calendar-month"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "monthly_consumption")
        self.entity_id = "sensor.kaarina_water_monthly"

    @property
    def native_value(self) -> float | None:
        """Return the current month's water consumption in m³."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("month_m3")


class KaarinaWaterLastHourSensor(BaseWRMWaterSensor):
    """Last reported hour's water consumption in liters."""

    _attr_translation_key = "last_hour_liters"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "last_hour_liters")
        self.entity_id = "sensor.kaarina_water_last_hour_liters"

    @property
    def native_value(self) -> float | None:
        """Return the last reported hour's water consumption in liters."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("last_hour_liters")


class KaarinaWaterLastReportedSensor(BaseWRMWaterSensor):
    """Sensor showing when the water meter data was last reported."""

    _attr_translation_key = "last_reported"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(
        self, coordinator: WRMWaterDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry, "last_reported")
        self.entity_id = "sensor.kaarina_water_last_reported"

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the timestamp when water meter data was last reported."""
        if not self.coordinator.data:
            return None
        epoch = self.coordinator.data.get("last_timestamp")
        if not epoch:
            return None
        return datetime.datetime.fromtimestamp(int(epoch), tz=datetime.timezone.utc)

