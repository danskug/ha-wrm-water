"""Constants for the WRM Systems Water integration."""

DOMAIN = "wrm_water"

DEFAULT_NAME = "Kaarina Water"
DEFAULT_SUBDOMAIN = "kaarinanvesihuolto"
DEFAULT_SCAN_INTERVAL_HOURS = 4

CONF_SUBDOMAIN = "subdomain"
CONF_CUSTOMER_ID = "customer_id"  # login-input-a
CONF_METER_SERIAL = "meter_serial"  # login-input-b
CONF_STATISTIC_ID = "statistic_id"  # default: sensor.kaarina_water_meter_reading

BASE_URL = "https://wmd.wrm-systems.fi"
LOGIN_PATH = "/{subdomain}/login"
READINGS_PATH = "/data/readings"
