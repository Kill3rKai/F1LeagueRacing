"""
F1 26 League Results Updater
============================
Reads a race/sprint CSV export from F1 26 and updates the league Google Sheet.

Requirements:
    pip install gspread google-auth pandas

Setup:
    1. Ask your host to create a Google Service Account and share the sheet with it.
    2. Place the downloaded JSON key file next to this script.
    3. Set SERVICE_ACCOUNT_FILE below to match the filename.
"""

import sys
import re
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------
# CONFIG — edit these to match league conf
# ----------------------------

SERVICE_ACCOUNT_FILE = "service_account.json"   # JSON key from host
SPREADSHEET_ID       = "1Ext0YgS-UOCa_P-gEOvurkRziF7OcoBS8Y7M6UVMtug" # Google Sheet ID (from URL)
SHEET_TAB_NAME       = "Race Stats"                 # Change if tab has a different name

# Human players: team name (as it appears in CSV) -> sheet row name
# "Player" entries are resolved at runtime by team
# Named entries (like Kaiser/Téo) are matched directly
PLAYER_MAP = {
    "Scuderia Ferrari HP": ["Kai", "Deshy"],
    "McLaren":             ["Tom"],
    "Oracle Red Bull Racing": ["Téo"],
    "Mercedes-AMG F1 Team":["Rehan"],
    # Add 5th player here when confirmed:
    # "Team": ["PlayerName"],
}

# Named player aliases in CSV (not listed as "Player")
NAMED_PLAYERS = {
    "Kill3rKai": "Kai",   # Kill3rKai in CSV = Kai in sheet
}

# AI driver name -> sheet row name (direct 1:1 mapping, case-insensitive last name match)
# The script auto-matches by last name, but you can add overrides here if needed
# "SOME NAME": "SheetRowName",
AI_OVERRIDES = {
# "SOME NAME": "SheetRowName",
}

# Points tables
RACE_POINTS   = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}
SPRINT_POINTS = {1:8,  2:7,  3:6,  4:5,  5:4,  6:3, 7:2, 8:1}

# Sheet layout
DRIVER_START_ROW = 2    # Row where driver list starts (Russel = row 2)
DRIVER_COL       = "A"  # Column with driver names
TOTAL_COL        = "AF" # Total points column

# Race columns: maps race label -> sheet column letter
# Sprints are labelled e.g. "2S" -> column D (the "2 (S)" column)
RACE_COLUMNS = {
    "1":   "B",
    "2":   "C",
    "2S":  "D",
    "3":   "E",
    "4":   "F",
    "5":   "G",
    "6":   "H",
    "6S":  "I",
    "7":   "J",
    "7S":  "K",
    "8":   "L",
    "9":   "M",
    "10":  "N",
    "11":  "O",
    "11S": "P",
    "12":  "Q",
    "13":  "R",
    "14":  "S",
    "14S": "T",
    "15":  "U",
    "16":  "V",
    "17":  "W",
    "18":  "X",
    "18S": "Y",
    "19":  "Z",
    "20":  "AA",
    "21":  "AB",
    "22":  "AC",
    "23":  "AD",
    "24":  "AE",
}

# WCC table layout (same sheet tab)
# Team name cells are in cols U–X, starting at row 27
WCC_START_ROW     = 27   # Row of "1st" in WCC table
WCC_TEAM_COL      = "U"  # Column where team name text lives (the colored cell)
WCC_TEAM_COL_END  = "X"  # Merged to here

# WDC table layout (same sheet tab)
WDC_START_ROW    = 27   # Row of "1st" in WDC table
WDC_NAME_COL     = "K"  # Driver name column
WDC_NAME_COL_END = "M"  # Name merged to here
WDC_PTS_COL      = "N"  # Points column
WDC_PTS_COL_END  = "O"  # Points merged to here


# Teams: CSV team name -> sheet display name + background color (hex)
TEAMS = {
    "Alpine":                    {"name": "Alpine",        "color": {"red": 0.957, "green": 0.514, "blue": 0.635}},  # pink
    "Aston Martin Aramco":       {"name": "Aston Martin",  "color": {"red": 0.204, "green": 0.659, "blue": 0.325}},  # green
    "Audi Revolut F1 Team":      {"name": "Audi",          "color": {"red": 0.753, "green": 0.753, "blue": 0.753}},  # grey
    "Cadillac Formula 1® Team":  {"name": "Cadillac",      "color": {"red": 0.0,   "green": 0.0,   "blue": 0.0}},    # black
    "Scuderia Ferrari HP":       {"name": "Ferrari",       "color": {"red": 0.918, "green": 0.0,   "blue": 0.0}},    # red
    "Haas":                      {"name": "Haas",          "color": {"red": 0.753, "green": 0.753, "blue": 0.753}},  # grey
    "McLaren":                   {"name": "McLaren",       "color": {"red": 1.0,   "green": 0.647, "blue": 0.0}},    # orange
    "Mercedes-AMG F1 Team":      {"name": "Mercedes",      "color": {"red": 0.0,   "green": 0.898, "blue": 0.988}},  # cyan
    "Visa Cash App Racing Bulls": {"name": "Racing Bulls",  "color": {"red": 0.8,   "green": 0.8,   "blue": 0.9}},   # light blue/grey
    "Oracle Red Bull Racing":    {"name": "Red Bull",      "color": {"red": 0.067, "green": 0.067, "blue": 0.8}},    # blue
    "Atlassian Williams F1 Team":{"name": "Williams",      "color": {"red": 0.529, "green": 0.741, "blue": 0.953}},  # light blue
}

# ----------------------------
# CSV PARSING
# ----------------------------

def parse_csv(filepath):
    """Parse the F1 26 export CSV. Returns (race_df, incidents_df)."""
    with open(filepath, "rb") as f:
        raw = f.read().decode("utf-8-sig")

    # normalize line endings (handle \r\n \n)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.strip().split("\r\n")

    # Debug
    print(f"[Debug] First line: {lines[0][:80]}")

    # Find the blank line separating race results from incident log
    separator = None
    for i, line in enumerate(lines):
        stripped = line.strip().strip(",").strip("\t")
        if stripped == "" and i > 1:
            separator = i
            break

    race_lines     = lines[:separator] if separator else lines
    incident_lines = lines[separator + 1:] if separator else []

    race_df = pd.read_csv(
        __import__("io").StringIO("\n".join(race_lines)),
        sep=None,
        engine="python",
        encoding="latin-1"
    )
    race_df.columns = [c.strip().strip('"') for c in race_df.columns]

    print(f"[Debug] Cols Found {list(race_df.columns)}")

    # Clean up Pos column — DSQ/DNF rows still have a numeric Pos
    race_df["Pos."] = pd.to_numeric(race_df["Pos."], errors="coerce")

    incidents_df = None
    if incident_lines:
        # Skip the empty separator line, find the incident header
        for i, line in enumerate(incident_lines):
            if "Time" in line and "Incident" in line:
                incident_lines = incident_lines[i:]
                break
        incidents_df = pd.read_csv(
            __import__("io").StringIO("\n".join(incident_lines)),
            sep=None,
            engine="python",
            encoding="latin-1"
        )
        incidents_df.columns = [c.strip().strip('"') for c in incidents_df.columns]

    return race_df, incidents_df


# ----------------------------
# PLAYER RESOLUTION
# ----------------------------

def resolve_players(race_df):
    """
    Returns a dict: { sheet_driver_name -> points_earned }
    Prompts user for shared-team ordering when needed.
    """
    results = {}

    for _, row in race_df.iterrows():
        csv_name    = str(row["Driver"]).strip()
        team        = str(row["Team"]).strip()
        driver_type = str(row["driver type"]).strip()
        pos         = row["Pos."]

        # Resolve sheet name
        sheet_name = resolve_name(csv_name, team, driver_type, race_df)
        if sheet_name is None:
            continue  # Skip if we couldn't resolve (shouldn't happen)

        # Calculate points
        pts = calc_points(pos, is_sprint=False)  # is_sprint passed in from caller
        results[sheet_name] = pts

    return results


def resolve_name(csv_name, team, driver_type, race_df):
    """Map a CSV driver entry to their sheet row name."""

    # 1. Named player alias (e.g. Kaiser -> Téo)
    if csv_name in NAMED_PLAYERS:
        return NAMED_PLAYERS[csv_name]

    # 2. AI driver — match by last name to sheet row names
    if driver_type == "AI":
        last_name = csv_name.split()[-1].upper()
        for sheet_name in get_all_sheet_names():
            if sheet_name.upper() in last_name or last_name in sheet_name.upper():
                return sheet_name
        # Fallback: return None and warn
        print(f"  [WARN] Could not match AI driver '{csv_name}' to a sheet row — skipping.")
        return None

    # 3. Player — resolve by team
    if driver_type == "Player":
        if team not in PLAYER_MAP:
            print(f"  [WARN] Team '{team}' not in PLAYER_MAP — skipping Player entry.")
            return None

        players_on_team = PLAYER_MAP[team]

        if len(players_on_team) == 1:
            return players_on_team[0]

        # Multiple humans on same team — need to ask
        return None  # Handled in batch below


def resolve_shared_teams(race_df):
    """
    For teams with 2 human players, prompt the user to identify who finished ahead.
    Returns dict: { (team, finishing_position) -> sheet_name }
    """
    resolution = {}

    for team, players in PLAYER_MAP.items():
        if len(players) < 2:
            continue

        # Find all Player rows on this team, sorted by Pos
        team_players = race_df[
            (race_df["Team"] == team) & (race_df["driver type"] == "Player")
        ].sort_values("Pos.")

        if team_players.empty:
            continue

        print(f"\n  Two players detected in {TEAMS.get(team, {}).get('name', team)}:")
        for _, r in team_players.iterrows():
            pos_label = int(r["Pos."]) if not pd.isna(r["Pos."]) else "DNF/DSQ"
            print(f"    Position {pos_label}")

        print(f"  Players available: {', '.join(players)}")
        first = input(f"  Who finished AHEAD (better position)? ").strip()

        if first not in players:
            print(f"  [WARN] '{first}' not recognised, defaulting to {players[0]}")
            first = players[0]

        second = [p for p in players if p != first][0]

        positions = list(team_players["Pos."])
        if len(positions) >= 1:
            resolution[(team, positions[0])] = first
        if len(positions) >= 2:
            resolution[(team, positions[1])] = second

    return resolution


def get_all_sheet_names():
    """All known names that appear in the sheet driver column."""
    names = []
    for players in PLAYER_MAP.values():
        names.extend(players)
    names.extend(NAMED_PLAYERS.values())
    # AI driver sheet names (same as their last name in most cases)
    ai_names = [
        "Russel", "Antonelli", "Verstappen", "Norris", "Sainz", "Albon",
        "Hulkenberg", "Borteleto", "Bearman", "Ocon", "Alonso", "Stroll",
        "Perez", "Bottas", "Lawson", "Lindblad", "Gasly", "Colapinto",
    ]
    names.extend(ai_names)
    return names


# ----------------------------
# POINTS CALCULATION
# ----------------------------

def calc_points(pos, is_sprint):
    """Return points for a finishing position. DNF/DSQ = 0."""
    if pd.isna(pos):
        return 0
    pos = int(pos)
    table = SPRINT_POINTS if is_sprint else RACE_POINTS
    return table.get(pos, 0)


def col_letter_to_index(col):
    """Convert column letter(s) to 0-based index. e.g. A->0, Z->25, AA->26"""
    result = 0
    for char in col.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1


# ----------------------------
# GOOGLE SHEETS
# ----------------------------

def connect_sheets():
    """Authenticate and return the worksheet."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SPREADSHEET_ID)
    return sheet.worksheet(SHEET_TAB_NAME)


def get_driver_rows(ws):
    """
    Returns dict: { sheet_name_lowercase -> row_number }
    Reads column A from the sheet.
    """
    col_a = ws.col_values(1)  # 1-indexed
    mapping = {}
    for i, name in enumerate(col_a):
        if name.strip() and name.strip().lower() != "driver":
            mapping[name.strip().lower()] = i + 1  # 1-indexed row
    return mapping


def update_race_points(ws, driver_rows, points_by_name, race_col):
    """Write each driver's points for this race into the correct column."""
    col_idx = col_letter_to_index(race_col) + 1  # gspread is 1-indexed

    updates = []
    for name, pts in points_by_name.items():
        row = driver_rows.get(name.lower())
        if row is None:
            print(f"  [WARN] '{name}' not found in sheet — skipping.")
            continue
        updates.append({
            "range": gspread.utils.rowcol_to_a1(row, col_idx),
            "values": [[pts]],
        })

    if updates:
        ws.batch_update(updates)
        print(f"   Written {len(updates)} driver results to column {race_col}")

def calc_wcc_points(ws, driver_rows):
    """
    Calculate WCC points per team.
    Every driver on the team contributes (AI + human).
    Returns dict: { csv_team_name -> total_points }
    """
    all_values = ws.get_all_values()
    total_col_idx = col_letter_to_index(TOTAL_COL)  # 0-based

    # Build reverse map: sheet_name_lower -> csv_team_name
    # We need to know which team each sheet driver belongs to
    sheet_name_to_team = {}

    # Human players
    for csv_team, players in PLAYER_MAP.items():
        for p in players:
            sheet_name_to_team[p.lower()] = csv_team

    # Named player aliases
    for csv_name, sheet_name in NAMED_PLAYERS.items():
        # Find their team from the player map
        for csv_team, players in PLAYER_MAP.items():
            if sheet_name in players:
                sheet_name_to_team[sheet_name.lower()] = csv_team

    # AI drivers — map by last name
    ai_to_team = {
        "russel":     "Mercedes-AMG F1 Team",
        "norris":     "McLaren",
        "verstappen": "Oracle Red Bull Racing",
        "sainz":      "Atlassian Williams F1 Team",
        "albon":      "Atlassian Williams F1 Team",
        "hulkenberg": "Audi Revolut F1 Team",
        "borteleto":  "Audi Revolut F1 Team",
        "bearman":    "Haas",
        "ocon":       "Haas",
        "alonso":     "Aston Martin Aramco",
        "stroll":     "Aston Martin Aramco",
        "perez":      "Cadillac Formula 1® Team",
        "bottas":     "Cadillac Formula 1® Team",
        "lawson":     "Visa Cash App Racing Bulls",
        "Lindblad":    "Visa Cash App Racing Bulls",
        "gasly":      "Alpine",
        "colapinto":  "Alpine",
    }
    sheet_name_to_team.update(ai_to_team)

    # Sum points per team
    team_points = {csv_team: 0 for csv_team in TEAMS}

    for sheet_name, row in driver_rows.items():
        if row - 1 >= len(all_values):
            continue
        row_data = all_values[row - 1]
        if total_col_idx < len(row_data):
            val = row_data[total_col_idx]
            pts = int(val) if val.strip().lstrip("-").isdigit() else 0
        else:
            pts = 0

        csv_team = sheet_name_to_team.get(sheet_name.lower())
        if csv_team and csv_team in team_points:
            team_points[csv_team] += pts

    return team_points


def update_wcc_table(ws, team_points):
    """
    Re-sort the WCC table by points descending.
    Rewrites team names and background colors in rows WCC_START_ROW to WCC_START_ROW+10.
    Position labels (1st, 2nd...) stay fixed.
    """
    # Sort teams by points descending
    sorted_teams = sorted(
        [(pts, csv_team) for csv_team, pts in team_points.items()],
        reverse=True
    )

    # Build batch data: list of (team_display_name, color) in ranked order
    ranked = []
    for pts, csv_team in sorted_teams:
        team_info = TEAMS.get(csv_team, {"name": csv_team, "color": {"red":1,"green":1,"blue":1}})
        ranked.append((team_info["name"], team_info["color"]))

    # Determine column indices for WCC team cells
    start_col = col_letter_to_index(WCC_TEAM_COL) + 1   # 1-indexed
    end_col   = col_letter_to_index(WCC_TEAM_COL_END) + 1

    # We'll use the Sheets API directly via gspread's spreadsheet object
    # to update both values and background colors
    requests = []

    for i, (team_name, color) in enumerate(ranked):
        row = WCC_START_ROW + i  # 1-indexed sheet row

        # Value update
        cell = gspread.utils.rowcol_to_a1(row, start_col)
        ws.update(range_name=cell, values=[[team_name]])

        # Background color update via batchUpdate
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId":          ws.id,
                    "startRowIndex":    row - 1,      # 0-indexed
                    "endRowIndex":      row,
                    "startColumnIndex": start_col - 1,
                    "endColumnIndex":   end_col,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": color,
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.foregroundColor",
            }
        })

    if requests:
        ws.spreadsheet.batch_update({"requests": requests})
        print(f"   WCC table updated and re-sorted")

def update_wdc_table(ws, driver_rows):
    """
    Re-sort the WDC table by total points descending.
    Reads totals from AF (SUM formula), writes driver name + points to WDC table.
    """
    all_values = ws.get_all_values()
    total_col_idx = col_letter_to_index(TOTAL_COL)  # AF, 0-based

    # Build list of (points, display_name) for all drivers
    driver_totals = []
    for sheet_name, row in driver_rows.items():
        if row - 1 >= len(all_values):
            continue
        row_data = all_values[row - 1]
        if total_col_idx < len(row_data):
            val = row_data[total_col_idx]
            pts = int(val) if val.strip().lstrip("-").isdigit() else 0
        else:
            pts = 0
        # Get display name from sheet (preserves original casing)
        display_name = row_data[0] if row_data else sheet_name
        driver_totals.append((pts, display_name))

    # Sort by points descending
    driver_totals.sort(reverse=True)

    name_col  = col_letter_to_index(WDC_NAME_COL) + 1
    name_end  = col_letter_to_index(WDC_NAME_COL_END) + 1
    pts_col   = col_letter_to_index(WDC_PTS_COL) + 1
    pts_end   = col_letter_to_index(WDC_PTS_COL_END) + 1

    requests = []
    for i, (pts, name) in enumerate(driver_totals):
        row = WDC_START_ROW + i

        ws.update(range_name=gspread.utils.rowcol_to_a1(row, name_col), values=[[name]])
        ws.update(range_name=gspread.utils.rowcol_to_a1(row, pts_col), values=[[pts]])

        # Force black text on both name and points cells
        for col_start, col_end in [(name_col, name_end), (pts_col, pts_end)]:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId":          ws.id,
                        "startRowIndex":    row - 1,
                        "endRowIndex":      row,
                        "startColumnIndex": col_start - 1,
                        "endColumnIndex":   col_end,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.foregroundColor",
                }
            })

    if requests:
        ws.spreadsheet.batch_update({"requests": requests})

    print(f"   WDC table updated and re-sorted")

# ----------------------------
# MAIN
# ----------------------------

def main():
    print("=" * 50)
    print("  F1 26 League Updater")
    print("=" * 50)

    # 1. Get CSV path
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = input("\nPath to CSV file: ").strip().strip('"')

    # 2. Get race number
    race_input = input("Race number (e.g. 1, 2, 2S, 6S): ").strip().upper().replace(" ", "")
    if race_input not in RACE_COLUMNS:
        print(f"[ERROR] '{race_input}' is not a valid race number. Valid options: {list(RACE_COLUMNS.keys())}")
        sys.exit(1)

    race_col  = RACE_COLUMNS[race_input]
    is_sprint = race_input.endswith("S")
    print(f"\n  -> {'Sprint' if is_sprint else 'Race'} {race_input} -> column {race_col}")

    # 3. Parse CSV
    print("\n[1/4] Parsing CSV...")
    race_df, incidents_df = parse_csv(csv_path)
    print(f"   {len(race_df)} drivers found")

    # 4. Resolve shared-team players (prompt if needed)
    print("\n[2/4] Resolving player identities...")
    shared_resolution = resolve_shared_teams(race_df)

    # Build final points dict { sheet_name -> points }
    points_by_name = {}

    for _, row in race_df.iterrows():
        csv_name    = str(row["Driver"]).strip()
        team        = str(row["Team"]).strip()
        driver_type = str(row["driver type"]).strip()
        pos         = row["Pos."]

        pts = calc_points(pos, is_sprint)

        # Named player alias
        if csv_name in NAMED_PLAYERS:
            sheet_name = NAMED_PLAYERS[csv_name]

        # AI driver
        elif driver_type == "AI":
            last = csv_name.split()[-1].capitalize()
            # Try matching against known sheet names
            all_names = get_all_sheet_names()
            match = next(
                (n for n in all_names if n.lower() == last.lower() or last.lower() in n.lower()),
                None
            )
            if match is None:
                print(f"  [WARN] No sheet match for AI '{csv_name}' — skipping")
                continue
            sheet_name = match

        # Player — single on team
        elif driver_type == "Player" and team in PLAYER_MAP and len(PLAYER_MAP[team]) == 1:
            sheet_name = PLAYER_MAP[team][0]

        # Player — shared team (use resolved ordering)
        elif driver_type == "Player" and team in PLAYER_MAP and len(PLAYER_MAP[team]) > 1:
            sheet_name = shared_resolution.get((team, pos))
            if sheet_name is None:
                print(f"  [WARN] Could not resolve shared player on {team} — skipping")
                continue

        else:
            print(f"  [WARN] Unhandled driver: {csv_name} / {team} / {driver_type} — skipping")
            continue

        points_by_name[sheet_name] = pts
        status = f"P{int(pos)} -> {pts}pts" if not pd.isna(pos) else "DNF/DSQ -> 0pts"
        print(f"  {csv_name:<30} -> {sheet_name:<15} {status}")

    # 5. Connect to Google Sheets
    print("\n[3/4] Connecting to Google Sheets...")
    ws = connect_sheets()
    driver_rows = get_driver_rows(ws)
    print(f"   Connected. {len(driver_rows)} drivers found in sheet.")

    # 6. Write race points + update totals
    print(f"\n[4/4] Writing results...")
    update_race_points(ws, driver_rows, points_by_name, race_col)

    # 7. Update WCC table
    print("\n[WCC] Calculating constructor standings...")
    ws = connect_sheets()
    driver_rows = get_driver_rows(ws)
    team_points = calc_wcc_points(ws, driver_rows)
    for team, pts in sorted(team_points.items(), key=lambda x: -x[1]):
        print(f"  {TEAMS[team]['name']:<20} {pts} pts")
    update_wcc_table(ws, team_points)

    # 8. Update WDC
    print("\n[WDC] Calculating driver standings...")
    update_wdc_table(ws, driver_rows)



    print("\nDone! Sheet updated successfully.")

if __name__ == "__main__":
    main()
