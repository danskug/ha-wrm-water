"""Config flow for WRM Systems Water integration."""
from __future__ import annotations

import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CUSTOMER_ID,
    CONF_INITIAL_IMPORT_DONE,
    CONF_METER_SERIAL,
    CONF_START_DATE,
    CONF_SUBDOMAIN,
    DOMAIN,
    SUBDOMAIN_OPTIONS,
)
from .coordinator import WRMClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CUSTOMER_ID): str,
        vol.Required(CONF_METER_SERIAL): str,
        vol.Required(CONF_SUBDOMAIN): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=SUBDOMAIN_OPTIONS,
                custom_value=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class WRMWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WRM Systems Water."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow state."""
        self._discovered_info: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return WRMWaterOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial credential step with WRM pre-search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            customer_id = user_input[CONF_CUSTOMER_ID].strip()
            meter_serial = user_input[CONF_METER_SERIAL].strip()
            subdomain = user_input[CONF_SUBDOMAIN].strip().lower()

            await self.async_set_unique_id(f"{DOMAIN}_{meter_serial}")
            self._abort_if_unique_id_configured()

            client = WRMClient(subdomain, customer_id, meter_serial)

            try:
                # Pre-search starting from 2010 to discover full available data range
                data = await self.hass.async_add_executor_job(
                    client.fetch_readings_sync, "2010-01-01"
                )
                if not data:
                    errors["base"] = "no_readings"
            except PermissionError:
                errors["base"] = "invalid_auth"
            except Exception as ex:
                _LOGGER.exception("Failed to connect to WRM Systems: %s", ex)
                errors["base"] = "cannot_connect"

            if not errors:
                # Extract earliest and latest reading info from discovered data
                # Format: [dt_str, cum_m3, hour_m3, epoch_s] (sorted newest first)
                earliest_row = data[-1]
                latest_row = data[0]

                earliest_epoch = int(earliest_row[3])
                earliest_date_str = datetime.datetime.fromtimestamp(
                    earliest_epoch, tz=datetime.timezone.utc
                ).strftime("%Y-%m-%d")
                earliest_m3 = round(float(earliest_row[1]), 3)
                latest_m3 = round(float(latest_row[1]), 3)

                subdomain_labels = {
                    opt["value"]: opt["label"].split(" (")[0] for opt in SUBDOMAIN_OPTIONS
                }
                if subdomain == "kaarinanvesihuolto":
                    entry_title = f"Kaarinan Vesi ({meter_serial})"
                elif subdomain in subdomain_labels:
                    entry_title = f"{subdomain_labels[subdomain]} ({meter_serial})"
                else:
                    friendly_sub = subdomain.replace("-", " ").replace("_", " ").title()
                    entry_title = f"{friendly_sub} ({meter_serial})"

                self._discovered_info = {
                    CONF_CUSTOMER_ID: customer_id,
                    CONF_METER_SERIAL: meter_serial,
                    CONF_SUBDOMAIN: subdomain,
                    "entry_title": entry_title,
                    "earliest_date": earliest_date_str,
                    "earliest_m3": earliest_m3,
                    "latest_m3": latest_m3,
                }

                return await self.async_step_history()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_history(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the second step: choosing start date via preset calendar."""
        errors: dict[str, str] = {}
        earliest_date = self._discovered_info.get("earliest_date", "2020-01-01")
        earliest_m3 = self._discovered_info.get("earliest_m3", 0.0)
        latest_m3 = self._discovered_info.get("latest_m3", 0.0)

        if user_input is not None:
            start_date = str(user_input.get(CONF_START_DATE, earliest_date))
            return self.async_create_entry(
                title=self._discovered_info["entry_title"],
                data={
                    CONF_CUSTOMER_ID: self._discovered_info[CONF_CUSTOMER_ID],
                    CONF_METER_SERIAL: self._discovered_info[CONF_METER_SERIAL],
                    CONF_SUBDOMAIN: self._discovered_info[CONF_SUBDOMAIN],
                    CONF_START_DATE: start_date,
                    CONF_INITIAL_IMPORT_DONE: False,
                },
            )

        history_schema = vol.Schema(
            {
                vol.Required(
                    CONF_START_DATE, default=earliest_date
                ): selector.DateSelector(
                    selector.DateSelectorConfig()
                ),
            }
        )

        return self.async_show_form(
            step_id="history",
            data_schema=history_schema,
            description_placeholders={
                "earliest_date": earliest_date,
                "earliest_m3": str(earliest_m3),
                "latest_m3": str(latest_m3),
            },
            errors=errors,
        )


class WRMWaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WRM Systems Water."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        customer_id = self.config_entry.data.get(CONF_CUSTOMER_ID)
        meter_serial = self.config_entry.data.get(CONF_METER_SERIAL)
        subdomain = self.config_entry.data.get(CONF_SUBDOMAIN)

        earliest_date = "2020-01-01"
        earliest_m3 = 0.0
        latest_m3 = 0.0

        # Always pre-search WRM portal with 2010-01-01 to discover the meter's true lifetime earliest date
        if customer_id and meter_serial and subdomain:
            try:
                client = WRMClient(subdomain=subdomain, customer_id=customer_id, meter_serial=meter_serial)
                data = await self.hass.async_add_executor_job(client.fetch_readings_sync, "2010-01-01")
                if data:
                    earliest_row = data[-1]
                    latest_row = data[0]
                    earliest_epoch = int(earliest_row[3])
                    earliest_date = datetime.datetime.fromtimestamp(
                        earliest_epoch, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%d")
                    earliest_m3 = round(float(earliest_row[1]), 3)
                    latest_m3 = round(float(latest_row[1]), 3)
            except Exception as ex:
                _LOGGER.warning("Could not pre-search historical date range in options flow: %s", ex)

        if user_input is not None:
            start_date = str(user_input.get(CONF_START_DATE, earliest_date))

            # Reset initial_import_done flag in entry.data so the newly selected date range is imported on reload
            new_data = {
                **self.config_entry.data,
                CONF_START_DATE: start_date,
                CONF_INITIAL_IMPORT_DONE: False,
            }
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data=user_input)

        # Default calendar to earliest_date (or explicitly chosen historical custom date)
        current_date = self.config_entry.data.get(CONF_START_DATE)
        recent_threshold = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%d")
        if not current_date or current_date >= recent_threshold:
            current_date = earliest_date

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_START_DATE, default=current_date
                ): selector.DateSelector(
                    selector.DateSelectorConfig()
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "earliest_date": earliest_date,
                "earliest_m3": str(earliest_m3),
                "latest_m3": str(latest_m3),
            },
        )
