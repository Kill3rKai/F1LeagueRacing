"""
VSM F1 League — Results Updater
================================
Reads a single race/sprint CSV export from F1 26 and updates that
season's local points database, then regenerates the website's
standings data file (Scripts/standings-data.js).

There is no Google Sheet in this version — this script's local JSON
files under data/ ARE the source of truth. The website reads the
generated JS file directly.

Requirements:
    pip install pandas

Usage:
    # Normal race update — one CSV = one race's results
    python update_results.py path/to/race.csv --race 3
    python update_results.py path/to/race.csv --race 3S          # sprint
    python update_results.py path/to/race.csv --race 5 --season 2 # season 2

    # Create/reset a season's data file from its roster, all at zero,
    # without processing any race (do this once when a season starts)
    python update_results.py --init-season 2
"""

import sys
import io
import json
import argparse
import unicodedata
from pathlib import Path


def _fold(s):
    """Strip accents so 'Hülkenberg' and 'HULKENBERG' compare equal."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()

# ----------------------------
# PATHS
# ----------------------------

SCRIPT_DIR   = Path(__file__).resolve().parent
DATA_DIR     = SCRIPT_DIR / "data"
WEBSITE_ROOT = SCRIPT_DIR               # update.py lives at the site root, next to Scripts/
STANDINGS_JSON = WEBSITE_ROOT / "Scripts" / "standings.json"

DATA_DIR.mkdir(exist_ok=True)

# ----------------------------
# TEAMS — CSV team name -> display name, CSS slug
# (slug must match the tc-<slug> / [data-team] classes in main.css)
# ----------------------------

TEAMS = {
    "Alpine":                     {"name": "Alpine",        "slug": "alpine"},
    "Aston Martin Aramco":        {"name": "Aston Martin",  "slug": "astonmartin"},
    "Audi Revolut F1 Team":       {"name": "Audi",          "slug": "audi"},
    "Cadillac Formula 1® Team":   {"name": "Cadillac",      "slug": "cadillac"},
    "Scuderia Ferrari HP":        {"name": "Ferrari",       "slug": "ferrari"},
    "Haas":                       {"name": "Haas",          "slug": "haas"},
    "McLaren":                    {"name": "McLaren",       "slug": "mclaren"},
    "Mercedes-AMG F1 Team":       {"name": "Mercedes",      "slug": "mercedes"},
    "Visa Cash App Racing Bulls": {"name": "Racing Bulls",  "slug": "racingbulls"},
    "Oracle Red Bull Racing":     {"name": "Red Bull",      "slug": "redbull"},
    "Atlassian Williams F1 Team": {"name": "Williams",      "slug": "williams"},
}

# ----------------------------
# SEASON CONFIG
# Add a new SEASONS[N] block when a new season's roster is confirmed.
# ----------------------------

SEASONS = {
    1: {
        # Human players: CSV team name -> sheet names, in no particular
        # order (order is resolved per-race if more than one player
        # shares a team — the script will ask).
        "player_map": {
            "Scuderia Ferrari HP":  ["Kai", "Deshy"],
            "McLaren":              ["Tom"],
            "Oracle Red Bull Racing": ["Téo"],
            "Mercedes-AMG F1 Team": ["Rehan"],
        },
        # Named player aliases as they appear in the CSV, if different
        # from their sheet/website name
        "named_players": {
            "Kill3rKai": "Kai",
        },
        # Full grid at season start: name -> CSV team name.
        # Used to seed the season file and to match AI drivers by
        # last name. is_player marks the ★ human rows.
        "roster": [
            ("Kai",         "Scuderia Ferrari HP",        True),
            ("Deshy",       "Scuderia Ferrari HP",        True),
            ("Tom",         "McLaren",                    True),
            ("Téo",         "Oracle Red Bull Racing",     True),
            ("Rehan",       "Mercedes-AMG F1 Team",       True),
            ("Antonelli",   "Mercedes-AMG F1 Team",       False),
            ("Verstappen",  "Oracle Red Bull Racing",     False),
            ("Norris",      "McLaren",                    False),
            ("Sainz",       "Atlassian Williams F1 Team", False),
            ("Albon",       "Atlassian Williams F1 Team", False),
            ("Hülkenberg",  "Audi Revolut F1 Team",       False),
            ("Bortoleto",   "Audi Revolut F1 Team",       False),
            ("Bearman",     "Haas",                       False),
            ("Ocon",        "Haas",                       False),
            ("Alonso",      "Aston Martin Aramco",        False),
            ("Stroll",      "Aston Martin Aramco",        False),
            ("Pérez",       "Cadillac Formula 1® Team",   False),
            ("Bottas",      "Cadillac Formula 1® Team",   False),
            ("Lawson",      "Visa Cash App Racing Bulls", False),
            ("Lindblad",    "Visa Cash App Racing Bulls", False),
            ("Gasly",       "Alpine",                     False),
            ("Colapinto",   "Alpine",                     False),
        ],
    },
    # 2: { ... add when Season 2's roster is confirmed ... },
}

RACE_POINTS   = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
SPRINT_POINTS = {1: 8,  2: 7,  3: 6,  4: 5,  5: 4,  6: 3, 7: 2, 8: 1}


# ----------------------------
# SEASON DATA FILE (data/seasonN.json)
# ----------------------------

def season_file(season_num):
    return DATA_DIR / f"season{season_num}.json"


def load_season(season_num):
    path = season_file(season_num)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return init_season_data(season_num)


def init_season_data(season_num):
    """Build a fresh, all-zero season file from that season's roster."""
    if season_num not in SEASONS:
        print(f"[ERROR] No roster configured for season {season_num}. "
              f"Add a SEASONS[{season_num}] block first.")
        sys.exit(1)

    config = SEASONS[season_num]
    drivers = {}
    for name, csv_team, is_player in config["roster"]:
        team = TEAMS.get(csv_team, {"name": csv_team, "slug": "unknown"})
        drivers[name] = {
            "team_slug": team["slug"],
            "team_name": team["name"],
            "is_player": is_player,
            "races": {},   # race_id -> points
        }
    return {"drivers": drivers}


def save_season(season_num, data):
    path = season_file(season_num)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   Saved {path}")


# ----------------------------
# CSV PARSING  (same shape as the old F1 26 export)
# ----------------------------

def parse_csv(filepath):
    import pandas as pd

    with open(filepath, "rb") as f:
        raw = f.read().decode("utf-8-sig")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.strip().split("\n")

    separator = None
    for i, line in enumerate(lines):
        if line.strip().strip(",").strip(";").strip("\t") == "" and i > 1:
            separator = i
            break

    race_lines = lines[:separator] if separator else lines
    race_df = pd.read_csv(
        io.StringIO("\n".join(race_lines)),
        sep=None, engine="python", encoding="latin-1"
    )
    race_df.columns = [c.strip().strip('"') for c in race_df.columns]
    race_df["Pos."] = pd.to_numeric(race_df["Pos."], errors="coerce")
    return race_df


# ----------------------------
# POINTS
# ----------------------------

def calc_points(pos, is_sprint):
    if pos is None or pos != pos:  # NaN check without importing numpy/pandas here
        return 0
    table = SPRINT_POINTS if is_sprint else RACE_POINTS
    return table.get(int(pos), 0)


# ----------------------------
# DRIVER RESOLUTION
# ----------------------------

def resolve_shared_teams(race_df, config, csv_team):
    """
    When >1 player shares a team, ask which finishing position belongs
    to which player for THIS race. Returns {position: sheet_name}.
    """
    players = config["player_map"][csv_team]
    named = config["named_players"]
    rows = race_df[race_df["Team"].astype(str).str.strip() == csv_team]
    rows = rows[rows["Driver"].astype(str).str.strip() == "Player"]

    resolution = {}
    print(f"\n  {csv_team} has {len(players)} players on the same team: {', '.join(players)}")
    for _, row in rows.iterrows():
        pos = row["Pos."]
        pos_label = f"P{int(pos)}" if pos == pos else "DNF/DSQ"
        print(f"    Who finished {pos_label} ({row['Driver']})?")
        for i, p in enumerate(players, 1):
            print(f"      {i}) {p}")
        choice = input("    > ").strip()
        try:
            resolution[pos] = players[int(choice) - 1]
        except (ValueError, IndexError):
            print("    [WARN] Invalid choice, skipping this driver.")
    return resolution


def resolve_all_drivers(race_df, config, is_sprint):
    """Returns {sheet_name: (points, csv_team)} for this race."""
    named_players = config["named_players"]
    player_map    = config["player_map"]
    roster_names  = [name for name, _, _ in config["roster"]]

    shared_cache = {}
    results = {}

    for _, row in race_df.iterrows():
        csv_name    = str(row["Driver"]).strip()
        team        = str(row["Team"]).strip()
        driver_type = str(row["driver type"]).strip()
        pos         = row["Pos."]
        pts         = calc_points(pos, is_sprint)

        if csv_name in named_players:
            sheet_name = named_players[csv_name]

        elif csv_name == "Player" and team in player_map and len(player_map[team]) == 1:
            # Generic "Player" name always means a human seat for that team,
            # regardless of what the "driver type" column says — F1 26 mislabels
            # this during AFK/takeover swaps, so we don't trust that column here.
            sheet_name = player_map[team][0]

        elif csv_name == "Player" and team in player_map and len(player_map[team]) > 1:
            if team not in shared_cache:
                shared_cache[team] = resolve_shared_teams(race_df, config, team)
            sheet_name = shared_cache[team].get(pos)
            if sheet_name is None:
                print(f"  [WARN] Could not resolve shared player on {team} — skipping")
                continue

        else:
            # A real name (not the literal "Player") — match by surname against
            # the roster, same as before. This covers normal AI rows and also
            # the reverse takeover glitch (an AI driver's name tagged "Player").
            last = csv_name.split()[-1]
            match = next((n for n in roster_names if _fold(last) in _fold(n)), None)
            if match is None:
                print(f"  [WARN] No roster match for '{csv_name}' — skipping")
                continue
            sheet_name = match

        results[sheet_name] = (pts, team)
        status = f"P{int(pos)} -> {pts}pts" if pos == pos else "DNF/DSQ -> 0pts"
        print(f"  {csv_name:<28} -> {sheet_name:<14} {status}")

    return results


# ----------------------------
# STANDINGS-DATA.JS GENERATION
# ----------------------------

def build_standings_block(season_num, season_data):
    drivers = []
    for name, d in season_data["drivers"].items():
        total = sum(d["races"].values())
        drivers.append({
            "name": name,
            "team": d["team_name"],
            "teamSlug": d["team_slug"],
            "isPlayer": d["is_player"],
            "pts": total,
        })
    drivers.sort(key=lambda d: (-d["pts"], d["name"]))

    leader_pts = drivers[0]["pts"] if drivers else 0
    for i, d in enumerate(drivers, 1):
        d["pos"] = i
        d["gap"] = "—" if i == 1 else f"-{leader_pts - d['pts']}"

    # Constructors: sum driver totals by team
    team_totals = {}
    for d in drivers:
        team_totals.setdefault(d["teamSlug"], {"team": d["team"], "teamSlug": d["teamSlug"], "pts": 0})
        team_totals[d["teamSlug"]]["pts"] += d["pts"]
    constructors = sorted(team_totals.values(), key=lambda c: (-c["pts"], c["team"]))

    leader_c_pts = constructors[0]["pts"] if constructors else 0
    for i, c in enumerate(constructors, 1):
        c["pos"] = i
        c["gap"] = "—" if i == 1 else f"-{leader_c_pts - c['pts']}"

    return {"drivers": drivers, "constructors": constructors}


def regenerate_standings_json():
    """Scan every data/seasonN.json and rebuild one combined public JSON file
    that the website fetches directly (Scripts/standings.json), keyed by
    season number as a string, e.g. {"1": {"drivers": [...], "constructors": [...]}}.
    """
    combined = {}
    for path in sorted(DATA_DIR.glob("season*.json")):
        season_num = int(path.stem.replace("season", ""))
        with open(path, "r", encoding="utf-8") as f:
            season_data = json.load(f)
        combined[str(season_num)] = build_standings_block(season_num, season_data)

    STANDINGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(STANDINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"   Wrote {STANDINGS_JSON}")


# ----------------------------
# MAIN
# ----------------------------

def main():
    parser = argparse.ArgumentParser(description="VSM F1 League results updater")
    parser.add_argument("csv", nargs="?", help="Path to the race/sprint CSV export")
    parser.add_argument("--race", help="Race identifier, e.g. 3 or 3S (sprint)")
    parser.add_argument("--season", type=int, default=1, help="Season number (default 1)")
    parser.add_argument("--init-season", type=int, metavar="N",
                         help="Create/reset season N's data file at zero, no CSV needed")
    args = parser.parse_args()

    if args.init_season is not None:
        data = init_season_data(args.init_season)
        save_season(args.init_season, data)
        regenerate_standings_json()
        print(f"\nSeason {args.init_season} initialised at zero. Done.")
        return

    if not args.csv or not args.race:
        parser.error("csv and --race are required unless using --init-season")

    if args.season not in SEASONS:
        print(f"[ERROR] No roster configured for season {args.season}. "
              f"Add a SEASONS[{args.season}] block in this script first.")
        sys.exit(1)

    race_id   = args.race.strip().upper()
    is_sprint = race_id.endswith("S")
    config    = SEASONS[args.season]

    print("=" * 50)
    print(f"  VSM F1 League Updater — Season {args.season}, Race {race_id}")
    print("=" * 50)

    print("\n[1/3] Parsing CSV...")
    race_df = parse_csv(args.csv)
    print(f"   {len(race_df)} drivers found")

    print("\n[2/3] Resolving drivers and points...")
    resolved = resolve_all_drivers(race_df, config, is_sprint)

    print("\n[3/3] Updating season data + website file...")
    season_data = load_season(args.season)
    for sheet_name, (pts, csv_team) in resolved.items():
        if sheet_name not in season_data["drivers"]:
            team = TEAMS.get(csv_team, {"name": csv_team, "slug": "unknown"})
            season_data["drivers"][sheet_name] = {
                "team_slug": team["slug"], "team_name": team["name"],
                "is_player": False, "races": {},
            }
        team = TEAMS.get(csv_team)
        if team:
            season_data["drivers"][sheet_name]["team_slug"] = team["slug"]
            season_data["drivers"][sheet_name]["team_name"] = team["name"]
        season_data["drivers"][sheet_name]["races"][race_id] = pts

    save_season(args.season, season_data)
    regenerate_standings_json()

    print(f"\nDone! Race {race_id} recorded for Season {args.season}.")
    print("If this site is served over http(s), the page will pick up Scripts/standings.json automatically.")


if __name__ == "__main__":
    main()