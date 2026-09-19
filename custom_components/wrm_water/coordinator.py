"""DataUpdateCoordinator and API client for WRM Systems Water."""
from __future__ import annotations

import datetime
import http.cookiejar
from html.parser import HTMLParser
import json
import logging
import ssl
from typing import Any
import urllib.parse
import urllib.request

from homeassistant.components.recorder import get_instance
try:
    from homeassistant.components.recorder.db_schema import Statistics
except ImportError:
    Statistics = None
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BASE_URL,
    CONF_CUSTOMER_ID,
    CONF_METER_SERIAL,
    CONF_STATISTIC_ID,
    CONF_SUBDOMAIN,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class LoginFormParser(HTMLParser):
    """HTML parser to extract CSRF tokens and form targets from WRM login page."""

    def __init__(self) -> None:
        super().__init__()
        self.csrf_token: str | None = None
        self.forms: list[dict[str, Any]] = []
        self.current_form: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "meta" and attr_dict.get("name") == "csrf-token":
            self.csrf_token = attr_dict.get("content")
        elif tag == "form":
            self.current_form = {
                "action": attr_dict.get("action", ""),
                "method": attr_dict.get("method", "GET").upper(),
                "id": attr_dict.get("id", ""),
                "inputs": {},
            }
            self.forms.append(self.current_form)
        elif tag in ["input", "select"] and self.current_form is not None:
            name = attr_dict.get("name")
            val = attr_dict.get("value", "")
            if name:
                self.current_form["inputs"][name] = val

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.current_form = None


class WRMClient:
    """Client for fetching water meter readings from WRM Systems web portal."""

    def __init__(self, subdomain: str, customer_id: str, meter_serial: str) -> None:
        self.subdomain = subdomain
        self.customer_id = customer_id
        self.meter_serial = meter_serial
        self.cookie_jar = http.cookiejar.CookieJar()
        self._ctx = ssl._create_unverified_context()
        self.login_url = f"{BASE_URL}/{self.subdomain}/login"

    def fetch_readings_sync(self, start_date: str) -> list[list[Any]]:
        """Synchronously authenticate and fetch readings from WRM Systems."""
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=self._ctx),
        )
        opener.addheaders = [
            (
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            ),
            (
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            ),
        ]

        # 1. Load login page to extract CSRF token and action
        resp = opener.open(self.login_url, timeout=20)
        body = resp.read().decode("utf-8", errors="replace")

        parser = LoginFormParser()
        parser.feed(body)

        target_form = parser.forms[0] if parser.forms else {"action": self.login_url, "inputs": {}}
        action = target_form["action"]
        if action.startswith("/"):
            action = BASE_URL + action
        elif not action.startswith("http"):
            action = self.login_url

        post_data = dict(target_form["inputs"])
        if parser.csrf_token and "_csrf" not in post_data:
            post_data["_csrf"] = parser.csrf_token

        post_data["mode"] = "water"
        post_data["login-input-a"] = self.customer_id
        post_data["login-input-b"] = self.meter_serial
        post_data["login-by"] = "ul"

        # 2. Submit login form
        encoded_data = urllib.parse.urlencode(post_data).encode("utf-8")
        req_post = urllib.request.Request(action, data=encoded_data, method="POST")
        req_post.add_header("Content-Type", "application/x-www-form-urlencoded")
        req_post.add_header("Origin", BASE_URL)
        req_post.add_header("Referer", self.login_url)

        resp_post = opener.open(req_post, timeout=20)
        _ = resp_post.read()

        # 3. Request hourly readings JSON
        readings_url = f"{BASE_URL}/data/readings?serialNumber={self.meter_serial}&startDate={start_date}"
        req_readings = urllib.request.Request(readings_url)
        req_readings.add_header("X-Requested-With", "XMLHttpRequest")
        req_readings.add_header("Accept", "application/json, text/javascript, */*; q=0.01")
        req_readings.add_header("Referer", resp_post.geturl())

        resp_readings = opener.open(req_readings, timeout=30)
        raw_json = resp_readings.read().decode("utf-8", errors="replace")
        data = json.loads(raw_json)

        if not isinstance(data, list):
            raise ValueError(f"Unexpected response format from WRM Systems: {data}")

        return data


class WRMWaterDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch WRM Systems data and import hourly statistics into LTS."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        subdomain = entry.data.get(CONF_SUBDOMAIN, "kaarinanvesihuolto")
        customer_id = entry.data[CONF_CUSTOMER_ID]
        meter_serial = entry.data[CONF_METER_SERIAL]
        self.statistic_id = entry.data.get(
            CONF_STATISTIC_ID, "sensor.kaarina_water_meter_reading"
        )

        self.client = WRMClient(subdomain, customer_id, meter_serial)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{meter_serial}",
            update_interval=datetime.timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from WRM Systems and inject hourly statistics into recorder."""
        # Fetch data for the last 7 days
        start_date = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%d")

        try:
            raw_data = await self.hass.async_add_executor_job(
                self.client.fetch_readings_sync, start_date
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching WRM Systems data: {err}") from err

        if not raw_data:
            raise UpdateFailed("WRM Systems returned no readings.")

        # WRM data format: [dt_str, cum_m3, hour_m3, epoch_s] (sorted newest first)
        latest_row = raw_data[0]
        current_reading_m3 = round(float(latest_row[1]), 3)
        last_reported = str(latest_row[0])
        last_hour_liters = round(float(latest_row[2]) * 1000.0, 1)
        last_timestamp = int(latest_row[3])

        # Reverse to chronological order (oldest first)
        chronological_data = list(reversed(raw_data))

        # 1. Group by local Finnish calendar day
        # In WRM: dt_str format is "D.M.YYYY H:MM"
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        current_month_prefix = datetime.date.today().strftime("%Y-%m")

        daily_liters: dict[str, float] = {}
        month_liters = 0.0

        for row in chronological_data:
            dt_str, _, hour_m3, _ = row
            date_part = dt_str.split(" ")[0]
            d, m, y = [int(x) for x in date_part.split(".")]
            day_key = f"{y:04d}-{m:02d}-{d:02d}"

            liters = float(hour_m3) * 1000.0
            daily_liters[day_key] = daily_liters.get(day_key, 0.0) + liters

            if day_key.startswith(current_month_prefix):
                month_liters += liters

        yesterday_liters = round(daily_liters.get(yesterday_str, 0.0), 0)
        today_liters = round(daily_liters.get(today_str, 0.0), 0)
        month_m3 = round(month_liters / 1000.0, 3)

        # 2. Automatically import hourly statistics into Home Assistant LTS
        try:
            await self._async_import_lts_statistics(chronological_data)
        except Exception as err:
            _LOGGER.error("Failed to import hourly LTS statistics: %s", err, exc_info=True)

        return {
            "current_reading_m3": current_reading_m3,
            "yesterday_liters": yesterday_liters,
            "today_liters": today_liters,
            "last_hour_liters": last_hour_liters,
            "month_m3": month_m3,
            "last_reported": last_reported,
            "last_timestamp": last_timestamp,
            "readings": chronological_data,
        }

    async def _async_import_lts_statistics(self, chronological_data: list[list[Any]]) -> None:
        """Import hourly readings into Home Assistant Long-Term Statistics."""
        stats: list[StatisticData] = []
        for row in chronological_data:
            try:
                _, cum_m3, _, epoch_s = row
                dt_utc = datetime.datetime.fromtimestamp(
                    int(epoch_s), tz=datetime.timezone.utc
                ).replace(minute=0, second=0, microsecond=0)

                stats.append(
                    StatisticData(
                        start=dt_utc,
                        state=round(float(cum_m3), 3),
                        sum=round(float(cum_m3), 3),
                    )
                )
            except Exception as e:
                _LOGGER.warning("Skipping malformed row for LTS: %s (%s)", row, e)

        if stats:
            metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name="Kaarina Water Meter Reading",
                source="recorder",
                statistic_id=self.statistic_id,
                unit_of_measurement=UnitOfVolume.CUBIC_METERS,
            )
            _LOGGER.debug(
                "Importing %d hourly water statistics into LTS for %s",
                len(stats),
                self.statistic_id,
            )
            recorder = get_instance(self.hass)
            try:
                if Statistics is not None:
                    recorder.async_import_statistics(metadata, stats, Statistics)
                else:
                    recorder.async_import_statistics(metadata, stats)
            except TypeError as err:
                _LOGGER.debug("Falling back to 2-arg async_import_statistics: %s", err)
                recorder.async_import_statistics(metadata, stats)
