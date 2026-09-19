<p align="center">
  <img src="images/logo.png" alt="WRM Systems" width="420">
</p>

# WRM Systems Water for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/v/release/danskug/ha-wrm-water)](https://github.com/danskug/ha-wrm-water/releases)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=danskug&repository=ha-wrm-water&category=integration)

Home Assistant integration for remote-read smart water meters connected to **WRM Systems** (`wmd.wrm-systems.fi`). **Tested and verified in production with Kaarinan Vesihuolto**, and supports numerous Finnish municipal water utilities and cooperatives using Axioma Qalcosonic W1 ultrasonic meters.

---

## Key Features

- 💧 **Automated Hourly Long-Term Statistics (LTS)**:
  Water utilities report data in daily batches. Unlike standard scrapers that dump the entire day's consumption as a single clump when polled, this integration automatically backfills every single past hour (`async_import_statistics`) to its exact historical timestamp.
- ⚡ **Seamless Energy Dashboard Integration**:
  The main water meter reading (`m³`) plugs directly into Home Assistant's official Energy Dashboard.
- 📊 **Dedicated Daily & Monthly Sensors**:
  - Yesterday's total consumption in liters (L) — perfect for wall tablets and dashboard cards (*"Eilen: 337 L"*).
  - Current month's consumption ($m^3$).
  - Timestamp when the water meter last transmitted data.
- 🕒 **Smart History Backfill & Lightweight Periodic Polling**:
  Choose how much history to import on setup or in Options Flow (7 days, 30 days, 90 days, 1 year, or All history since meter installation). Routine 4-hour polling only fetches a rolling 7-day window to minimize network traffic and portal load.
- 🔒 **Zero External Dependencies**:
  Built using Python standard library tools (`html.parser`, `urllib`, `http.cookiejar`) with automatic CSRF token handling and session re-authentication.
- 🌐 **Full Localization**:
  Complete English, Finnish, and Swedish translations (`en.json`, `fi.json`, `sv.json`) for UI dialogs and entity names.

---

## Installation via HACS

### 1-Click Install
Click the button below to add this repository directly to your Home Assistant instance:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=danskug&repository=ha-wrm-water&category=integration)

### Manual HACS Install
1. Make sure [HACS](https://hacs.xyz/) is installed.
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
   - **Water Utility / Subdomain**: Select your water utility from the searchable dropdown list, or type a custom subdomain if your utility is not in the list.
   - **History to Import**: Choose how far back in time to import hourly history into Home Assistant.
4. Click **Submit**.

---

## Supported Water Utilities & Subdomains

Any water utility using the WRM Systems platform (`wmd.wrm-systems.fi`) is supported. Subdomains on WRM Systems are all lowercase and do not contain hyphens or spaces. To find your subdomain, open your water utility's consumption portal login page in your browser — the subdomain is the part of the web address immediately following `wmd.wrm-systems.fi/`.

> [!NOTE]
> The integration is **tested and verified in production with Kaarinan Vesihuolto**.

The following 17 water utilities are verified and available directly in the setup dropdown:

| Subdomain | Water Utility / Municipality | Status / Notes |
| :--- | :--- | :--- |
| `kaarinanvesihuolto` | Kaarinan Vesihuolto | **Tested & verified in production** |
| `kajaaninvesi` | Kajaanin Vesi | Verified portal |
| `kangasalanvesi` | Kangasalan Vesi | Verified portal |
| `keskisavonvesi` | Keski-Savon Vesi | Verified portal |
| `kirkkonummenvesi` | Kirkkonummen Vesi | Verified portal |
| `loimaanvesi` | Loimaan Vesi | Verified portal |
| `lumijoenvesi` | Lumijoen Vesi Oy | Verified portal |
| `orimattilanvesi` | Orimattilan Vesi | Verified portal |
| `oulunvesi` | Oulun Vesi | Verified portal |
| `pyhaluostovesi` | Pyhä-Luosto Vesi Oy | Verified portal |
| `salonvesi` | Salon Vesi -liikelaitos | Verified portal |
| `sastamalanvesi` | Sastamalan Vesi Liikelaitos | Verified portal |
| `seinajoenvesi` | Seinäjoen Vesi | Verified portal |
| `suonenjoenvesi` | Suonenjoen Vesi | Verified portal |
| `vaalanvesijalampo` | Vaalan Vesi ja Lämpö | Verified portal |
| `vihdinvesi` | Vihdin Vesi | Verified portal |
| `ylojarvenvesi` | Ylöjärven Vesi | Verified portal |

---

## Entities

| Entity ID | Unit | Description |
| :--- | :--- | :--- |
| `sensor.kaarina_water_meter_reading` | $m^3$ | Cumulative water meter reading. Configurable in Energy Dashboard. |
| `sensor.kaarina_water_yesterday_liters` | L | Yesterday's verified total consumption in liters. |
| `sensor.kaarina_water_monthly` | $m^3$ | Current month's consumption. |
| `sensor.kaarina_water_last_reported` | timestamp | Timestamp when the water meter last transmitted data. |

---

## Energy Dashboard Setup

1. Go to **Settings $\rightarrow$ Dashboards $\rightarrow$ Energy**.
2. Under **Water consumption**, click **Add water source**.
3. Select `sensor.kaarina_water_meter_reading`.
4. (Optional) Set your water price per $m^3$ (e.g. `6.15` EUR/$m^3$ in Kaarina).

---

## License

MIT License
