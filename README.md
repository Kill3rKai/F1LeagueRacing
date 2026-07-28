# VSM F1 League

This repository contains a small static website for the VSM F1 League plus a Python updater script to keep season standings current.

## Overview

`update.py` reads a single race or sprint CSV export from F1 26 and updates the local season data in `data/season.json`. It then regenerates `scripts/standings.json`, which is the file the website reads to display driver and constructor standings.

The website itself is static HTML/CSS/JavaScript, so it can be hosted on GitHub Pages or any static web host.

## Requirements

- Python 3.x
- `pandas` Python package

Install the dependency with:

```bash
pip install pandas
```

## How to update driver and constructor standings

Run the updater from the root dir.

### Normal race update (3rd race of the season)

```bash
python update.py path/to/race.csv --race 3
```

This will:
- parse the race CSV
- assign points for the race
- update `data/season1.json` (or the selected season)
- regenerate `scripts/standings.json`

### Sprint update

```bash
python update.py path/to/race.csv --race 3S
```

Sprint races use the sprint points table instead of the full race points table.

### Update a different season

```bash
python update.py path/to/race.csv --race 5 --season 2
```

This uses the roster configuration for `season 2`. A season must be configured in `update.py` before it can be updated.

## Initialize a new season

To create or reset a season file with every driver at zero points, use:

```bash
python update.py --init-season 2
```

That command will:
- build `data/season2.json` from the roster defined in `update.py`
- reset all race data to zero
- regenerate `Scripts/standings.json`

Use this once when a new season begins.

## How this works

- `data/seasonN.json` is the source of truth for each season's driver records.
- `update.py` updates that JSON and then regenerates `Scripts/standings.json`.
- The website reads `Scripts/standings.json` to render both driver standings and constructor standings.

## Hosting the site

This website is static, so it can be hosted on GitHub Pages or any static web host.

### GitHub Pages

1. Push the repository to GitHub.
2. In the repository settings, enable GitHub Pages.
3. Choose the branch and root folder where `index.html` lives.
4. Visit the published site URL.

### Other static hosts

Upload the repository root contents to any static hosting service. The site expects the following paths:

- `index.html`
- `drivers.html`
- `season/1.html`
- `style/`
- `scripts/`
- `data/` (with generated `season.json` and `scripts/standings.json`)

### Local preview

You can preview the site locally with a simple HTTP server:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## Notes

- The script currently supports the seasons defined in the `SEASONS` dictionary inside `update.py`.
- If multiple human players share the same team in a race, the script will ask you to resolve those positions manually.
- If the repository uses a different filename than shown in examples, run `python update.py` from the repo root.
- VSM League [Link](https://kill3rkai.github.io/F1LeagueRacing/)