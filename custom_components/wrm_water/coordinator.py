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
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
try:
    from homeassistant.components.recorder.models import StatisticMeanType
except ImportError:
    StatisticMeanType = None
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BASE_URL,
    CONF_CUSTOMER_ID,
    CONF_HISTORY_DAYS,
    CONF_METER_SERIAL,
    CONF_STATISTIC_ID,
    CONF_SUBDOMAIN,
    DEFAULT_HISTORY_DAYS,
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
        clean_subdomain = subdomain.lower().replace("-", "_").replace(".", "_")
        if clean_subdomain == "kaarinanvesihuolto":
            default_stat_id = f"{DOMAIN}:kaarina_water_meter_reading"
        else:
            default_stat_id = f"{DOMAIN}:{clean_subdomain}_water_meter_reading"
        self.statistic_id = entry.data.get(CONF_STATISTIC_ID, default_stat_id)
        if not self.statistic_id.startswith(f"{DOMAIN}:"):
            self.statistic_id = default_stat_id
        self._initial_import_done = False

        self.client = WRMClient(subdomain, customer_id, meter_serial)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{meter_serial}",
            update_interval=datetime.timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from WRM Systems and inject hourly statistics into recorder."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if not self._initial_import_done:
            history_days = str(
                self.entry.options.get(
                    CONF_HISTORY_DAYS,
                    self.entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS),
                )
            )
            if history_days == "all":
                start_date = "2010-01-01"
            elif history_days == "365":
                start_date = (now_utc - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            elif history_days == "90":
                start_date = (now_utc - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
            elif history_days == "30":
                start_date = (now_utc - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            else:
                start_date = (now_utc - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            self._initial_import_done = True
            _LOGGER.info(
                "Initial historical import: fetching readings from %s (mode: %s)",
                start_date,
                history_days,
            )
        else:
            # Routine periodic poll: rolling 2-day window (48 hours) to catch new readings
            start_date = (now_utc - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            _LOGGER.debug(
                "Routine periodic poll: fetching rolling 2-day readings from %s",
                start_date,
            )

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

        # Automatically import hourly statistics into Home Assistant LTS
        try:
            await self._async_import_lts_statistics(chronological_data)
        except Exception as err:
            _LOGGER.error("Failed to import hourly LTS statistics: %s", err, exc_info=True)

        return {
            "current_reading_m3": current_reading_m3,
            "last_reported": last_reported,
            "last_timestamp": last_timestamp,
            "last_hour_liters": last_hour_liters,
            "readings": chronological_data,
        }

    async def _async_import_lts_statistics(self, chronological_data: list[list[Any]]) -> None:
        """Import hourly readings into Home Assistant Long-Term Statistics."""
        stats: list[StatisticData] = []
        prev_dt: datetime.datetime | None = None
        prev_cum: float | None = None

        for row in chronological_data:
            try:
                _, cum_m3, _, epoch_s = row
                dt_utc = datetime.datetime.fromtimestamp(
                    int(epoch_s), tz=datetime.timezone.utc
                ).replace(minute=0, second=0, microsecond=0)
                cum_float = round(float(cum_m3), 3)

                # Ensure cumulative reading is monotonically non-decreasing
                if prev_cum is not None and cum_float < prev_cum:
                    cum_float = prev_cum

                # Fill any hourly gaps to overwrite legacy recorder artifacts and ensure continuity
                if prev_dt is not None and prev_cum is not None:
                    gap_hours = int((dt_utc - prev_dt).total_seconds() // 3600)
                    if 1 < gap_hours <= 48:
                        for step in range(1, gap_hours):
                            fill_dt = prev_dt + datetime.timedelta(hours=step)
                            stats.append(
                                StatisticData(
                                    start=fill_dt,
                                    state=prev_cum,
                                    sum=prev_cum,
                                )
                            )

                stats.append(
                    StatisticData(
                        start=dt_utc,
                        state=cum_float,
                        sum=cum_float,
                    )
                )
                prev_dt = dt_utc
                prev_cum = cum_float
            except Exception as e:
                _LOGGER.warning("Skipping malformed row for LTS: %s (%s)", row, e)

        if stats:
            metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name="Kaarina Water Meter Reading",
                source=DOMAIN,
                statistic_id=self.statistic_id,
                unit_of_measurement=UnitOfVolume.CUBIC_METERS,
            )
            metadata["unit_class"] = "volume"
            if StatisticMeanType is not None:
                metadata["mean_type"] = StatisticMeanType.NONE

            _LOGGER.debug(
                "Importing %d hourly external water statistics into LTS for %s",
                len(stats),
                self.statistic_id,
            )
            chunk_size = 500
            for i in range(0, len(stats), chunk_size):
                chunk = stats[i : i + chunk_size]
                try:
                    async_add_external_statistics(self.hass, metadata, chunk)
                except Exception as err:
                    _LOGGER.error("Failed to add external statistics: %s", err)
