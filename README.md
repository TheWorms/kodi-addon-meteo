**English** · [Français](readme.fr.md)

# Météo Concept — `weather.meteoconcept`

**Kodi weather provider for France**, based on the
[Météo Concept](https://api.meteo-concept.com) API (Météo-France data).
Single location, **French** labels, and icons rendered by your skin
(Arctic Zephyr, Estuary…).

> Add-on id: `weather.meteoconcept` · Type: `xbmc.python.weather` ·
> Kodi ≥ 19 (Matrix), Python 3.

---

## Installation

**Recommended — TheWorms repository** (automatic updates).

Download the repository by clicking **[HERE](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, then in Kodi:

1. **Add-ons** → **Install from zip file** → select the downloaded zip
   *(if Kodi blocks it, enable **Unknown sources** under Settings → Add-ons)*
2. **Install from repository** → **TheWorms Repository** → pick the add-on
3. Updates will then be automatic

**Manual install (alternative):** download the add-on zip from the [Releases](../../releases) page, then **Add-ons** → **Install from zip file**.

---

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [How it works](#how-it-works)
- [Quota and cache](#quota-and-cache)
- [Weather codes and icons](#weather-codes-and-icons)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Project structure](#project-structure)
- [Contributing](#contributing)
- [License and credits](#license-and-credits)

---

## Features

- **Current conditions**: temperature, wind (speed + direction in plain text),
  humidity, condition.
- **Daily forecast** over 7 days (min/max, condition, rain probability, wind).
- **Hourly forecast** for the next 12 hours.
- **French labels** from Météo Concept's "sensible weather" table.
- **Skin icons**: the add-on publishes the Kodi condition code (0–47); your skin
  shows its own pictograms, consistent with its theme.
- **Automatic day / night** handling (moon icon after sunset), via the town's
  ephemeris.
- **Town search** by name or postal code, directly in Kodi.
- **"Save and test token" button** that validates the key with a real API call.
- **Configurable file cache** to stay well below the free quota.

## Requirements

- **Kodi 19 (Matrix) or later** (tested up to Omega), Python 3.
- A **free Météo Concept token**: create an account at
  <https://api.meteo-concept.com>, *Basic* plan (500 requests/day).
- A town in **mainland France** (Belgium, Luxembourg and Andorra are also
  covered by the API via coordinates).

## Configuration

1. **Settings → Add-ons → My add-ons → Services → Météo Concept → Configure**.
2. Paste your **token** in the dedicated field.
3. Click **"Save and test token"**: type/paste the token in the window and
   confirm. The add-on saves it, tests it, and reports "valid ✓" or shows the
   error returned by the API.
4. Click **"Search a town…"**, type the name or postal code, and select the
   town (the INSEE code is saved automatically).
5. Enable the add-on as provider: **Settings → Weather → Weather information
   service → Météo Concept**.

> Some skins (including Arctic Zephyr) have **their own** weather provider
> setting: check the skin side too if the home widget doesn't update.

## How it works

Kodi calls the add-on in several ways:

- `RunScript(weather.meteoconcept,Location1)` → search/select the town.
- `RunScript(weather.meteoconcept,TestToken)` → save + test the token.
- with a numeric index (`1`) → fetch the weather.

On each fetch, the add-on queries three Météo Concept routes
(`/forecast/nextHours`, `/forecast/daily`, `/ephemeride/0`), then writes
**window properties** to Kodi's weather window (`Window(12600)`), which the skin
reads for display:

- `Current.*` (current conditions),
- `Daily.N.*` and `Day0..6.*` (daily forecast, extended + legacy format),
- `Hourly.N.*` (hourly forecast),
- `Location1` + `Locations`, `Forecast.City`, `Today.Sunrise`/`Sunset`.

> ⚠️ The `Location1` window property is **essential**: it is what the home widget
> and the `Weather.Location` infolabel read. Without it, the widget would keep
> the location left by a previous provider.

The add-on **clears all categories** before writing, so it never leaves residual
values from another provider.

## Quota and cache

The *Basic* plan is limited to **500 requests/day**. Each refresh consumes
**3 calls** (hourly + daily + ephemeris). With the **cache** (30 min by default,
adjustable from 10 to 120 min) and a reasonable Kodi refresh interval, usage
stays around a hundred calls per day — far below the cap. The cache is stored in
the add-on profile (`~/.kodi/userdata/addon_data/weather.meteoconcept/`).

## Weather codes and icons

The API's `weather` field is a "sensible weather" integer (codes 0 to 235).
The `resources/lib/meteo_concept_mapping.py` module translates it into:

- a **French label** (official Météo Concept table),
- a **Kodi condition code 0–47** = the skin icon name (`28.png`…).

To use a bundled icon set instead of the skin's, the function
`get_icon_path(code, is_day, icons_dir=…)` returns a full path. A free and
complete set: [Erik Flowers' Weather Icons](https://erikflowers.github.io/weather-icons/)
(SIL OFL license).

## Troubleshooting

**The home widget keeps the old provider (frozen location).**
Window properties persist in memory until rewritten. After changing provider,
**restart Kodi** (or disable/re-enable the add-on) to force a clean rewrite.

**"Missing token" right after I entered it.**
Kodi only saves a field's value when the settings dialog **closes**. Use the
**"Save and test token"** button (which saves immediately), or type the token
then close with **OK** before doing anything else.

**Check what the add-on reads / writes.**
Enable debugging (Settings → System → Logging → Enable debug logging), then:

```bash
tail -f ~/.kodi/temp/kodi.log | grep meteoconcept
```

**Check that the token is saved:**

```bash
cat ~/.kodi/userdata/addon_data/weather.meteoconcept/settings.xml
```

## Development

Build the installable zip (named after the version in `addon.xml`):

```bash
./build.sh          # -> dist/weather.meteoconcept-x.y.z.zip
```

The `resources/lib/` modules are Kodi-independent and can be tested outside Kodi
(the mapping and the API client don't import `xbmc*`):

```bash
python3 weather.meteoconcept/resources/lib/meteo_concept_mapping.py
```

To change the add-on **id**, update three consistent elements: the
`weather.meteoconcept/` folder, the `id` attribute of `addon.xml`, and the
`RunScript(...)` actions in `settings.xml`.

## Project structure

```
kodi-addon-meteo/
├── README.md / readme.fr.md
├── LICENSE                         # GPL-2.0
├── .gitignore
├── build.sh                        # produces dist/weather.meteoconcept-x.y.z.zip
└── weather.meteoconcept/           # the add-on (id: weather.meteoconcept)
    ├── addon.xml
    ├── default.py                  # Kodi entry point
    ├── icon.png
    ├── LICENSE.txt
    ├── changelog.txt
    └── resources/
        ├── settings.xml
        ├── icons/logo.png
        ├── language/resource.language.fr_fr/strings.po
        └── lib/
            ├── meteoconcept.py            # API client + cache
            └── meteo_concept_mapping.py   # weather codes -> FR label + icon
```

## Contributing

Contributions are welcome: open an *issue* or a *pull/merge request*. Please keep
the `resources/lib/` modules testable outside Kodi and update `changelog.txt` as
well as the version in `addon.xml`.

## License and credits

- Code under **GPL-2.0-only** — see [`LICENSE`](LICENSE).
- Weather data © **Météo Concept** (<https://api.meteo-concept.com>), based on
  **Météo-France** data. Use of the data is subject to Météo Concept's terms.
  This project is neither affiliated with nor endorsed by Météo Concept or
  Météo-France.
- Kodi weather provider template inspired by the open-source add-on
  [`weather.gismeteo`](https://github.com/vlmaksime/weather.gismeteo) (GPL).
