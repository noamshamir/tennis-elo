import pandas as pd
import glob
import os
from datetime import datetime
from tqdm import tqdm

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
INPUT_DIR   = "../data/matches"   # directory containing both singles and doubles CSVs
K           = 32
INITIAL_ELO = 1500

# ─── ELO TRACKERS ────────────────────────────────────────────────────────────────
elo_overall           = {}
peak_overall          = {}
last_match_date_overall = {}

elo_surface           = {}  # { surface: { player_id: elo } }
peak_surface          = {}
last_match_date_surface = {}

elo_doubles           = {}  # per-player doubles Elo
peak_doubles          = {}
last_match_date_doubles = {}

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def parse_date(val):
    """
    Try strict YYYYMMDD parse if exactly 8 digits;
    otherwise coerce to NaT.
    """
    s = str(val).strip()
    if s.isdigit() and len(s) == 8:
        try:
            return pd.to_datetime(s, format="%Y%m%d")
        except Exception:
            pass
    return pd.to_datetime(val, errors="coerce")


def compute_new_elo(w_elo, l_elo):
    expected = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
    delta    = K * (1 - expected)
    return w_elo + delta, l_elo - delta


def ensure_player(tracker, peak, pid):
    if pid not in tracker:
        tracker[pid] = INITIAL_ELO
        peak[pid]    = INITIAL_ELO


def update_tracker(tracker, peak, pid, new_elo):
    tracker[pid] = new_elo
    peak[pid]    = max(peak.get(pid, new_elo), new_elo)


def update_match_date(date_dict, pid, date):
    prev = date_dict.get(pid, pd.Timestamp.min)
    date_dict[pid] = max(prev, date)

# ─── LOAD & LABEL MATCHES ───────────────────────────────────────────────────────
all_matches = []
for path in glob.glob(os.path.join(INPUT_DIR, "atp_matches_*.csv")):
    fname = os.path.basename(path).lower()
    df    = pd.read_csv(path)
    df['tourney_date'] = df['tourney_date'].apply(parse_date)

    if 'doubles' in fname:
        # Doubles file
        for _, row in df.iterrows():
            date = row['tourney_date']
            if pd.isna(date):
                continue
            try:
                w1 = int(row['winner1_id'])
                w2 = int(row['winner2_id'])
                l1 = int(row['loser1_id'])
                l2 = int(row['loser2_id'])
            except Exception:
                continue

            all_matches.append({
                'type'     : 'doubles',
                'date'     : date,
                'match_num': row.get('match_num', 0),
                'surface'  : row['surface'],
                'w1'       : w1,
                'w2'       : w2,
                'l1'       : l1,
                'l2'       : l2,
            })
    else:
        # Singles file
        for _, row in df.iterrows():
            date = row['tourney_date']
            if pd.isna(date):
                continue
            try:
                winner = int(row['winner_id'])
                loser  = int(row['loser_id'])
            except Exception:
                continue

            all_matches.append({
                'type'     : 'singles',
                'date'     : date,
                'match_num': row.get('match_num', 0),
                'surface'  : row['surface'],
                'winner'   : winner,
                'loser'    : loser,
            })

# Sort chronologically
all_matches.sort(key=lambda m: (m['date'], m['match_num']))
max_date = max(m['date'] for m in all_matches)
cutoff   = max_date - pd.Timedelta(days=365)
print(f"Total matches to process: {len(all_matches)}")

# ─── PROCESS MATCHES WITH PROGRESS BAR ───────────────────────────────────────────
for match in tqdm(all_matches, desc="Processing matches"):
    date = match['date']
    if match['type'] == 'singles':
        s = match['surface']
        w = match['winner']
        l = match['loser']

        ensure_player(elo_overall, peak_overall, w)
        ensure_player(elo_overall, peak_overall, l)
        elo_surface.setdefault(s, {})
        peak_surface.setdefault(s, {})
        last_match_date_surface.setdefault(s, {})
        ensure_player(elo_surface[s], peak_surface[s], w)
        ensure_player(elo_surface[s], peak_surface[s], l)

        new_w_o, new_l_o = compute_new_elo(elo_overall[w], elo_overall[l])
        update_tracker(elo_overall, peak_overall, w, new_w_o)
        update_tracker(elo_overall, peak_overall, l, new_l_o)

        new_w_s, new_l_s = compute_new_elo(elo_surface[s][w], elo_surface[s][l])
        update_tracker(elo_surface[s], peak_surface[s], w, new_w_s)
        update_tracker(elo_surface[s], peak_surface[s], l, new_l_s)

        update_match_date(last_match_date_overall, w, date)
        update_match_date(last_match_date_overall, l, date)
        update_match_date(last_match_date_surface[s], w, date)
        update_match_date(last_match_date_surface[s], l, date)

    else:
        w1, w2 = match['w1'], match['w2']
        l1, l2 = match['l1'], match['l2']
        
        # after parsing IDs
        if any(pid < 100000 for pid in [w1, w2, l1, l2]):
            continue

        ensure_player(elo_doubles, peak_doubles, w1)
        ensure_player(elo_doubles, peak_doubles, w2)
        ensure_player(elo_doubles, peak_doubles, l1)
        ensure_player(elo_doubles, peak_doubles, l2)

        team1 = (elo_doubles[w1] + elo_doubles[w2]) / 2
        team2 = (elo_doubles[l1] + elo_doubles[l2]) / 2
        new_t1, new_t2 = compute_new_elo(team1, team2)
        delta = new_t1 - team1

        update_tracker(elo_doubles, peak_doubles, w1, elo_doubles[w1] + delta)
        update_tracker(elo_doubles, peak_doubles, w2, elo_doubles[w2] + delta)
        update_tracker(elo_doubles, peak_doubles, l1, elo_doubles[l1] - delta)
        update_tracker(elo_doubles, peak_doubles, l2, elo_doubles[l2] - delta)

        update_match_date(last_match_date_doubles, w1, date)
        update_match_date(last_match_date_doubles, w2, date)
        update_match_date(last_match_date_doubles, l1, date)
        update_match_date(last_match_date_doubles, l2, date)

# ─── OUTPUT TOP 10 LISTS ─────────────────────────────────────────────────────────
def print_top(title, current, peak, last_dates=None):
    print(f"\n=== {title} ===")
    print("Current Top 10:")
    items = current.items()
    if last_dates is not None:
        items = [(pid, elo) for pid, elo in items if last_dates.get(pid, pd.Timestamp.min) >= cutoff]
    for pid, elo in sorted(items, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  Player {pid}: {round(elo)}")
    print("All-Time Peak Top 10:")
    for pid, elo in sorted(peak.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  Player {pid}: {round(elo)}")

print_top("Overall Elo", elo_overall, peak_overall, last_match_date_overall)
for surf in elo_surface:
    print_top(f"{surf} Elo", elo_surface[surf], peak_surface[surf], last_match_date_surface[surf])
print_top("Doubles Elo", elo_doubles, peak_doubles, last_match_date_doubles)
