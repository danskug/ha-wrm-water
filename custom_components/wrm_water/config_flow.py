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
    CONF_HISTORY_DAYS,
    CONF_METER_SERIAL,
    CONF_SUBDOMAIN,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_SUBDOMAIN,
    DOMAIN,
    HISTORY_DAYS_OPTIONS,
)
from .coordinator import WRMClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CUSTOMER_ID): str,
        vol.Required(CONF_METER_SERIAL): str,
        vol.Required(CONF_SUBDOMAIN, default=DEFAULT_SUBDOMAIN): str,
        vol.Required(CONF_HISTORY_DAYS, default=DEFAULT_HISTORY_DAYS): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=HISTORY_DAYS_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="history_days",
            )
        ),
    }
)


class WRMWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WRM Systems Water."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return WRMWaterOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            customer_id = user_input[CONF_CUSTOMER_ID].strip()
            meter_serial = user_input[CONF_METER_SERIAL].strip()
            subdomain = user_input[CONF_SUBDOMAIN].strip()
            history_days = user_input.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)

            await self.async_set_unique_id(f"{DOMAIN}_{meter_serial}")
            self._abort_if_unique_id_configured()

            client = WRMClient(subdomain, customer_id, meter_serial)
            start_date = (
                datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)
            ).strftime("%Y-%m-%d")

            try:
                data = await self.hass.async_add_executor_job(
                    client.fetch_readings_sync, start_date
                )
                if not data:
                    errors["base"] = "no_readings"
            except Exception as ex:
                _LOGGER.exception("Failed to connect to WRM Systems: %s", ex)
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Kaarinan Vesi ({meter_serial})",
                    data={
                        CONF_CUSTOMER_ID: customer_id,
                        CONF_METER_SERIAL: meter_serial,
                        CONF_SUBDOMAIN: subdomain,
                        CONF_HISTORY_DAYS: history_days,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class WRMWaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for WRM Systems Water."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_history = self.config_entry.options.get(
            CONF_HISTORY_DAYS,
            self.config_entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS),
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HISTORY_DAYS, default=current_history
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=HISTORY_DAYS_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="history_days",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
