<p align="center">
  <img src="images/logo.png" alt="WRM Systems" width="420">
</p>

# WRM Systems Water for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/v/release/danskug/ha-wrm-water)](https://github.com/danskug/ha-wrm-water/releases)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=danskug&repository=ha-wrm-water&category=integration)

Home Assistant integration for remote-read smart water meters connected to **WRM Systems** (`wmd.wrm-systems.fi`). **Tested and verified in production with Kaarinan Vesihuolto**, and supports numerous Finnish municipal water utilities and cooperatives using Axioma Qalcosonic W1 ultrasonic meters.

- 🇫🇮 **Suomeksi**: Home Assistant (HACS) -integraatio **WRM Systems Oy:n** (`wmd.wrm-systems.fi`) etäluettaville vesimittareille (esim. *Axioma Qalcosonic W1*). Tuo tuntikohtaisen vedenkulutuksen ja mittarilukeman ($\text{m}^3$) suoraan Home Assistantin Energianäkymään (*Energy Dashboard* / *Long-Term Statistics*). Toimii mm. seuraavien vesilaitosten kulutusseurannassa: *Kaarinan Vesihuolto, Oulun Vesi, Kangasalan Vesi, Kirkkonummen Vesi, Salon Vesi, Seinäjoen Vesi, Ylöjärven Vesi, Vihdin Vesi, Kajaanin Vesi, Sastamalan Vesi, Loimaan Vesi, Orimattilan Vesi, Keski-Savon Vesi, Suonenjoen Vesi, Lumijoen Vesi, Vaalan Vesi ja Lämpö* sekä *Pyhä-Luosto Vesi*.
- 🇸🇪 **På svenska**: Home Assistant (HACS)-integration för fjärravlästa smarta vattenmätare anslutna till **WRM Systems** (`wmd.wrm-systems.fi`, t.ex. *Axioma Qalcosonic W1*). Importerar timvis vattenförbrukning och mätarställning ($\text{m}^3$) direkt till Home Assistants Energipanel (*Långtidsstatistik / LTS*).

> [!WARNING]
> **Use at Your Own Risk — Unofficial & Unmaintained Personal Project**
> - **English**: This is an unofficial personal hobby project shared **"AS IS" without warranty of any kind**. Use it entirely **at your own risk**. The author **does not actively maintain** this repository, does not guarantee compatibility with future Home Assistant or WRM Systems updates, and does not provide technical support.
> - **Suomeksi**: Tämä on epävirallinen, omaan käyttöön tehty harrasteprojekti, joka jaetaan **sellaisenaan ("AS IS") ilman minkäänlaista takuuta**. Käyttö tapahtuu täysin **omalla vastuulla**. Tekijä **ei ylläpidä** projektia aktiivisesti eikä tarjoa sille tukea.
> - **Svenska**: Detta är ett inofficiellt privat hobbyprojekt som delas **i befintligt skick ("AS IS") utan några garantier**. Användning sker helt **på egen risk**. Upphovsmannen **underhåller inte** repot aktivt och erbjuder ingen support.

---

## Key Features

- 💧 **Automated Hourly Long-Term Statistics (LTS)**:
  Water utilities report data in periodic batches (typically every 8 hours around 06:00, 14:00, and 22:00). Unlike standard scrapers that dump an entire batch's consumption as a single clump when polled, this integration automatically backfills every single past hour (`async_import_statistics`) to its exact historical timestamp with strict recorder compilation guardrails (`compile_safe_cutoff`).
- ⚡ **Seamless Energy Dashboard Integration**:
  The main water meter reading (`m³`, 3-decimal 1-liter precision) plugs directly into Home Assistant's official Energy Dashboard for hourly, daily, monthly, and yearly consumption and tariff tracking.
- 🕒 **One-Shot History Backfill & Lightweight 1-Hour Polling**:
  Choose how much history to import on initial setup or via Options Flow (7 days, 30 days, 90 days, 1 year, or All history since meter installation). Once imported, subsequent Home Assistant restarts and routine 1-hour polls fetch only a lightweight rolling 2-day (48-hour) window (~2.5 KB) for instant startup and minimal portal load.
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

For `kaarinanvesihuolto`, the entities are named `sensor.kaarina_water_*` (for other utilities, `sensor.<subdomain>_*`):

| Entity ID | Unit | Description |
| :--- | :--- | :--- |
| `sensor.kaarina_water_meter_reading` | $\text{m}^3$ | Cumulative water meter reading (`total_increasing`, 3 decimals). Exposes attributes `today_consumption_l`, `yesterday_consumption_l`, `last_24h_consumption_l`, `last_hour_consumption_l`, and `last_reported`. |
| `sensor.kaarina_water_last_reported` | timestamp | Timestamp when the water meter last transmitted data to the portal. |

---

## Energy Dashboard Setup

1. Go to **Settings $\rightarrow$ Dashboards $\rightarrow$ Energy**.
2. Under **Water consumption**, click **Add water source**.
3. Select `sensor.kaarina_water_meter_reading`.
4. (Optional) Set your static water price per $\text{m}^3$ (e.g. `6.15` EUR/$\text{m}^3$ in Kaarina).

---

## Disclaimer & Support (Ansvarsfriskrivning / Vastuuvapauslauseke)

> [!CAUTION]
> - ⚠️ **Use at Your Own Risk (Omalla vastuulla / På egen risk)**: This integration is not affiliated with, endorsed by, or supported by WRM Systems Oy or any water utility. It is provided **"AS IS" without warranty of any kind**. You are solely responsible for any use of this integration and any impact on your Home Assistant database or utility account.
> - 🛠️ **No Active Maintenance or Support**: This is a personal project built for the author's own household (with AI assistance) and shared openly in case others find it useful. **The author does not actively maintain this repository**, does not monitor issues, and does not provide user support or bug fixes unless they directly affect the author's own setup. If you need changes or fixes, please fork the repository.

---

## License & Trademarks

- **Source Code**: Licensed under the [MIT License](LICENSE) — provided "AS IS", without warranty of any kind.
- **Trademarks & Logos**: *WRM Systems* and the WRM Systems logo are trademarks/property of **WRM Systems Oy** (and *Axioma Qalcosonic* is a trademark of **Axioma Metering UAB**). They are used here solely for identification purposes within the Home Assistant interface and are not covered by the MIT License. This project is independent and not affiliated with or endorsed by WRM Systems Oy.
