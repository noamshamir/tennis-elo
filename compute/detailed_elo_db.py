import pandas as pd
import glob
import os
import mysql.connector
from tqdm import tqdm
from datetime import datetime

K = 32
INITIAL_ELO = 1500
INPUT_DIR = "../data/matches"  # folder with atp_matches_*.csv (singles + doubles)

# ─── ELO TRACKERS ────────────────────────────────────────────────────────────────
elo_overall         = {}
peak_overall        = {}
last_date_overall   = {}

elo_surface         = {}  # { surface: { player_id: elo } }
peak_surface        = {}
last_date_surface   = {}  # { surface: { player_id: last_date } }

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def parse_date(val):
    s = str(val).strip()
    if s.isdigit() and len(s) == 8:
        try:
            return pd.to_datetime(s, format="%Y%m%d")
        except:
            pass
    return pd.to_datetime(val, errors="coerce")

def compute_new_elo(w_elo, l_elo):
    expected = 1 / (1 + 10**((l_elo - w_elo) / 400))
    delta = K * (1 - expected)
    return w_elo + delta, l_elo - delta

def ensure_player(tracker, peak, last_date, pid, date):
    if pid not in tracker:
        tracker[pid]       = INITIAL_ELO
        peak[pid]          = INITIAL_ELO
        last_date[pid]     = date

def update_tracker(tracker, peak, last_date, pid, new_elo, date):
    tracker[pid]     = new_elo
    peak[pid]        = max(peak.get(pid, new_elo), new_elo)
    last_date[pid]   = max(last_date.get(pid, date), date)

# ─── LOAD ALL SINGLES MATCHES ──────────────────────────────────────────────────
all_matches = []
for path in glob.glob(os.path.join(INPUT_DIR, "atp_matches_*.csv")):
    fname = os.path.basename(path).lower()
    df = pd.read_csv(path)
    df['tourney_date'] = df['tourney_date'].apply(parse_date)

    if 'doubles' in fname:
        continue  # skip doubles entirely

    for idx, row in df.iterrows():
        date = row['tourney_date']
        if pd.isna(date):
            continue
        try:
            w = int(row['winner_id'])
            l = int(row['loser_id'])
        except:
            continue

        raw_score = row.get('score', None)
        score_txt = '' if pd.isna(raw_score) else str(raw_score)

        all_matches.append({
            'idx'       : idx,
            'date'      : date,
            'surface'   : row['surface'],
            'winner'    : w,
            'loser'     : l,
            'score'     : score_txt,
        })

all_matches.sort(key=lambda m: (m['date'], m['idx']))
print(f"Loaded {len(all_matches)} singles matches")

# ─── SET UP DATABASE ────────────────────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="noamshamir",
    password="noampass",
    database="noams"
)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS detailed_player_entry")
cursor.execute("""
CREATE TABLE detailed_player_entry (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  player_id     INT      NOT NULL,
  date          DATE     NOT NULL,
  elo_before    INT      NOT NULL,
  elo_after     INT      NOT NULL,
  won           BOOLEAN  NOT NULL,
  match_id      VARCHAR(100) NOT NULL,
  category      VARCHAR(20)  NOT NULL,
  score         VARCHAR(50),
  INDEX (player_id),
  INDEX (date),
  INDEX (match_id)
)""")
conn.commit()

# ─── PROCESS & WRITE TO DB ──────────────────────────────────────────────────────
for m in tqdm(all_matches, desc="Processing matches"):
    date      = m['date']
    match_id  = m['idx']
    w, l      = m['winner'], m['loser']
    score_txt = m['score']

    # --- OVERALL ELO UPDATE & INSERT ---
    ensure_player(elo_overall, peak_overall, last_date_overall, w, date)
    ensure_player(elo_overall, peak_overall, last_date_overall, l, date)
    before_w_o = elo_overall[w]
    before_l_o = elo_overall[l]
    new_w_o, new_l_o = compute_new_elo(before_w_o, before_l_o)
    update_tracker(elo_overall, peak_overall, last_date_overall, w, new_w_o, date)
    update_tracker(elo_overall, peak_overall, last_date_overall, l, new_l_o, date)

    cursor.execute("""
      INSERT INTO detailed_player_entry
        (player_id, date, elo_before, elo_after, won, match_id, category, score)
      VALUES (%s, %s, %s, %s, %s, %s, 'overall', %s)
    """, (w, date.strftime("%Y-%m-%d"), before_w_o, round(new_w_o), True, str(match_id), score_txt))

    cursor.execute("""
      INSERT INTO detailed_player_entry
        (player_id, date, elo_before, elo_after, won, match_id, category, score)
      VALUES (%s, %s, %s, %s, %s, %s, 'overall', %s)
    """, (l, date.strftime("%Y-%m-%d"), before_l_o, round(new_l_o), False, str(match_id), score_txt))

    # --- SURFACE ELO UPDATE & INSERT (only if surface defined) ---
    surface = m['surface']
    if pd.notna(surface):
        surf = str(surface)
        elo_surface.setdefault(surf, {})
        peak_surface.setdefault(surf, {})
        last_date_surface.setdefault(surf, {})

        ensure_player(elo_surface[surf], peak_surface[surf], last_date_surface[surf], w, date)
        ensure_player(elo_surface[surf], peak_surface[surf], last_date_surface[surf], l, date)

        before_w_s = elo_surface[surf][w]
        before_l_s = elo_surface[surf][l]
        new_w_s, new_l_s = compute_new_elo(before_w_s, before_l_s)
        update_tracker(elo_surface[surf], peak_surface[surf], last_date_surface[surf], w, new_w_s, date)
        update_tracker(elo_surface[surf], peak_surface[surf], last_date_surface[surf], l, new_l_s, date)

        cursor.execute("""
          INSERT INTO detailed_player_entry
            (player_id, date, elo_before, elo_after, won, match_id, category, score)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            w,
            date.strftime("%Y-%m-%d"),
            before_w_s,
            round(new_w_s),
            True,
            str(match_id),
            surf.lower(),
            score_txt
        ))
        cursor.execute("""
          INSERT INTO detailed_player_entry
            (player_id, date, elo_before, elo_after, won, match_id, category, score)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            l,
            date.strftime("%Y-%m-%d"),
            before_l_s,
            round(new_l_s),
            False,
            str(match_id),
            surf.lower(),
            score_txt
        ))

conn.commit()
print(f"Inserted rows, last cursor.rowcount={cursor.rowcount}")
cursor.close()
conn.close()
print("Done.")