import os
import json
import urllib.request

NOTES = {
    441550027: """### 🧹 Sensor Attribute Cleanup & Performance
- **Removed pseudo-realtime consumption attributes**: Removed `today_consumption_l`, `yesterday_consumption_l`, `last_24h_consumption_l`, and `last_hour_consumption_l` from `sensor.kaarina_water_meter_reading`. Water meters only transmit data 3 times per day in batches, so these attributes were incomplete or lagging.
- **Accurate Energy Dashboard**: All hourly, daily, monthly, and yearly consumption tracking is natively handled with 100% precision by Home Assistant's Energy Dashboard via Long-Term Statistics (LTS).
- **Reduced overhead**: Removed the 72-hour polling calculation loop in the background coordinator for faster execution and lower CPU usage.""",

    441547011: """### ✨ Pre-Search Discovery & Custom Date Picker
- **2-step setup flow**:
  1. **Credential verification & pre-search**: Automatically discovers the water meter's earliest recorded transmission date and initial meter reading from WRM Systems.
  2. **Flexible history selection**: Choose from **From the beginning** (all available data), **1 year**, **1 month**, or a **custom specified date** via calendar picker.
- **Move-in date support**: Perfect for new homeowners or ownership transfers to avoid importing previous owners' historical consumption into your Energy Dashboard.
- **Reconfigurable**: The same choices and calendar picker are available under *Configure* (Options Flow) without reinstalling.
- **Localization**: Added full English, Finnish, and Swedish translations for the new setup steps.""",

    441537103: """### 🎨 Marketplace UI & Formatting Improvements
- **Native Unicode formatting**: Replaced raw KaTeX syntax (`m³`, `→`) so text renders cleanly in Home Assistant and mobile apps.
- **Dark mode logo support**: Added theme-aware `<picture>` support that automatically loads `logo_white.png` with crisp white text in dark mode.
- **Reliable language tags**: Replaced flag emojis with robust language markers (`FI`, `SE`) that display properly across all devices and webviews.
- **Cleaner warning blocks**: Replaced GitHub-specific callout syntax with universal Markdown blockquotes.
- **Regional discovery**: Added `"country": ["FI"]` to `hacs.json` for enhanced discovery in Finland.""",

    433888667: """### 🐛 Long-Term Statistics (LTS) Collision Guard
- **Immediate hourly updates**: Adjusted `compile_safe_cutoff` to `now_hour` (after :00:25) so that `now_hour - 1h` updates immediately after compilation without negative temporary dips or SQLite constraint collisions.""",

    433686622: """### 🎉 Initial Stable Release
- **Hourly LTS injection**: Direct automated backfilling of historical hourly consumption into Home Assistant Long-Term Statistics.
- **Energy Dashboard**: Native water source integration with 1-liter (0.001 m³) precision.
- **Lightweight polling**: One-time historical backfill with fast 1-hour routine checks (~2.5 KB).
- **Multi-utility support**: Verified in production with Kaarinan Vesihuolto, with pre-configured support for 16+ Finnish municipal water utilities."""
}

token = os.environ.get("GH_TOKEN")
if not token:
    raise SystemExit("Missing GH_TOKEN")

for release_id, body in NOTES.items():
    url = f"https://api.github.com/repos/danskug/ha-wrm-water/releases/{release_id}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "ReleaseNotesUpdater"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Updated release {release_id} successfully (HTTP {resp.status})")
    except Exception as err:
        print(f"Failed to update release {release_id}: {err}")
