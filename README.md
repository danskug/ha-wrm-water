# WRM Systems Water for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/v/release/danskug/ha-wrm-water)](https://github.com/danskug/ha-wrm-water/releases)

Home Assistant integration for remote-read smart water meters connected to **WRM Systems** (`wmd.wrm-systems.fi`), such as **Kaarinan Vesihuolto** and other Finnish water utilities using Axioma Qalcosonic W1 ultrasonic meters.

---

## Key Features

- 💧 **Automated Hourly Long-Term Statistics (LTS)**:
  Water utilities report data in daily batches. Unlike standard scrapers that dump the entire day's consumption as a single clump when polled, this integration automatically backfills every single past hour (`async_import_statistics`) to its exact historical timestamp.
- ⚡ **Seamless Energy Dashboard Integration**:
  The main water meter reading (`sensor.kaarina_water_meter_reading` or configured entity) plugs directly into Home Assistant's official Energy Dashboard (`m³`).
- 📊 **Dedicated Daily & Monthly Sensors**:
  - `sensor.kaarina_water_yesterday_liters`: Total consumption yesterday (L) — perfect for wall tablets and dashboard cards (*"Eilen: 337 L"*).
  - `sensor.kaarina_water_daily_liters`: Today's preliminary consumption (L).
  - `sensor.kaarina_water_monthly`: Current month's consumption ($m^3$).
  - `sensor.kaarina_water_last_hour_liters`: Consumption in the last reported hour (L).
- 🔒 **Zero External Dependencies**:
  Built using Python standard library tools (`html.parser`, `urllib`, `http.cookiejar`) with automatic CSRF token handling and session re-authentication.
- 🇫🇮 **Full Localization**:
  Complete English and Finnish translations (`en.json`, `fi.json`) for UI dialogs and entity names.

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In Home Assistant, open **HACS**.
3. Click the three dots (top right) $\rightarrow$ **Custom repositories**.
4. Add repository URL:
   ```
   https://github.com/danskug/ha-wrm-water
   ```
5. Select Type: **Integration** and click **Add**.
6. Find **WRM Systems Water** in HACS and click **Download**.
7. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Add Integration**.
2. Search for **WRM Systems Water** (or **WRM Systems Vesi**).
3. Enter your portal credentials:
   - **Customer / Payer Number (Maksajan numero)**: Found on your water bill (e.g. `12345`).
   - **Meter Serial Number (Mittarin sarjanumero)**: Printed on your Axioma water meter (e.g. `01234567`).
   - **Portal Subdomain**: Your utility's subdomain on `wmd.wrm-systems.fi` (default: `kaarinanvesihuolto`).
4. Click **Submit**.

---

## Entities

| Entity ID | Unit | Description |
| :--- | :--- | :--- |
| `sensor.kaarina_water_meter_reading` | $m^3$ | Cumulative water meter reading. Configurable in Energy Dashboard. |
| `sensor.kaarina_water_yesterday_liters` | L | Yesterday's verified total consumption in liters. |
| `sensor.kaarina_water_daily_liters` | L | Today's consumption in liters. |
| `sensor.kaarina_water_monthly` | $m^3$ | Current month's consumption. |
| `sensor.kaarina_water_last_hour_liters` | L | Consumption during the latest reported hour. |

---

## Energy Dashboard Setup

1. Go to **Settings $\rightarrow$ Dashboards $\rightarrow$ Energy**.
2. Under **Water consumption**, click **Add water source**.
3. Select `sensor.kaarina_water_meter_reading`.
4. (Optional) Set your water price per $m^3$ (e.g. `6.15` EUR/$m^3$ in Kaarina).

---

## License

MIT License
