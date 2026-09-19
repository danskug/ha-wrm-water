"""Constants for the WRM Systems Water integration."""

DOMAIN = "wrm_water"

DEFAULT_NAME = "Kaarina Water"
DEFAULT_SUBDOMAIN = "kaarinanvesihuolto"
DEFAULT_SCAN_INTERVAL_HOURS = 4

CONF_SUBDOMAIN = "subdomain"
CONF_CUSTOMER_ID = "customer_id"  # login-input-a
CONF_METER_SERIAL = "meter_serial"  # login-input-b
CONF_STATISTIC_ID = "statistic_id"  # default: sensor.kaarina_water_meter_reading
CONF_HISTORY_DAYS = "history_days"

DEFAULT_HISTORY_DAYS = "7"
HISTORY_DAYS_OPTIONS = ["7", "30", "90", "365", "all"]

from homeassistant.helpers import selector

SUBDOMAIN_OPTIONS: list[selector.SelectOptionDict] = [
    selector.SelectOptionDict(value="kaarinanvesihuolto", label="Kaarinan Vesihuolto (kaarinanvesihuolto)"),
    selector.SelectOptionDict(value="kajaaninvesi", label="Kajaanin Vesi (kajaaninvesi)"),
    selector.SelectOptionDict(value="kangasalanvesi", label="Kangasalan Vesi (kangasalanvesi)"),
    selector.SelectOptionDict(value="keskisavonvesi", label="Keski-Savon Vesi (keskisavonvesi)"),
    selector.SelectOptionDict(value="kirkkonummenvesi", label="Kirkkonummen Vesi (kirkkonummenvesi)"),
    selector.SelectOptionDict(value="loimaanvesi", label="Loimaan Vesi (loimaanvesi)"),
    selector.SelectOptionDict(value="lumijoenvesi", label="Lumijoen Vesi Oy (lumijoenvesi)"),
    selector.SelectOptionDict(value="orimattilanvesi", label="Orimattilan Vesi (orimattilanvesi)"),
    selector.SelectOptionDict(value="oulunvesi", label="Oulun Vesi (oulunvesi)"),
    selector.SelectOptionDict(value="pyhaluostovesi", label="Pyhä-Luosto Vesi Oy (pyhaluostovesi)"),
    selector.SelectOptionDict(value="salonvesi", label="Salon Vesi (salonvesi)"),
    selector.SelectOptionDict(value="sastamalanvesi", label="Sastamalan Vesi (sastamalanvesi)"),
    selector.SelectOptionDict(value="seinajoenvesi", label="Seinäjoen Vesi (seinajoenvesi)"),
    selector.SelectOptionDict(value="suonenjoenvesi", label="Suonenjoen Vesi (suonenjoenvesi)"),
    selector.SelectOptionDict(value="vaalanvesijalampo", label="Vaalan Vesi ja Lämpö (vaalanvesijalampo)"),
    selector.SelectOptionDict(value="vihdinvesi", label="Vihdin Vesi (vihdinvesi)"),
    selector.SelectOptionDict(value="ylojarvenvesi", label="Ylöjärven Vesi (ylojarvenvesi)"),
]

BASE_URL = "https://wmd.wrm-systems.fi"
LOGIN_PATH = "/{subdomain}/login"
READINGS_PATH = "/data/readings"

