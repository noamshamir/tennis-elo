import pandas as pd
import glob
import os
import mysql.connector
from tqdm import tqdm
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
INPUT_DIR    = "../data/matches"
K            = 32
INITIAL_ELO  = 1500
OVERALL_FROM = 1968
OVERALL_TO   = 2024
SURF_FROM    = 2000
SURF_TO      = 2020

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
    exp   = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
    delta = K * (1 - exp)
    return w_elo + delta, l_elo - delta

# ─── LOAD ALL SINGLES MATCHES INTO ONE DF ───────────────────────────────────────
all_singles = []
for path in glob.glob(os.path.join(INPUT_DIR, "atp_matches_*.csv")):
    if "doubles" in path.lower():
        continue
    df = pd.read_csv(path, usecols=[
        "tourney_date", "match_num", "winner_id", "loser_id", "surface"
    ])
    df["tourney_date"] = df["tourney_date"].apply(parse_date)
    df = df.dropna(subset=["tourney_date", "winner_id", "loser_id"])
    # cast IDs to int
    df["winner_id"] = df["winner_id"].astype(int)
    df["loser_id"]  = df["loser_id"].astype(int)
    all_singles.append(df)

matches = pd.concat(all_singles, ignore_index=True)
matches = matches.sort_values(by=["tourney_date", "match_num"])
print(f"Total singles matches loaded: {len(matches)}")

# ─── FIGURE OUT UNIQUE SURFACES ────────────────────────────────────────────────
surfaces = (
    matches["surface"]
    .dropna()
    .unique()
    .tolist()
)

# ─── BUILD COMBO LIST ───────────────────────────────────────────────────────────
jobs = []
# overall
for start in range(OVERALL_FROM, OVERALL_TO):
    for end in range(start + 1, OVERALL_TO + 1):
        jobs.append(("overall", start, end))
# per-surface
for surf in surfaces:
    for start in range(SURF_FROM, SURF_TO):
        for end in range(start + 1, SURF_TO + 1):
            jobs.append((surf, start, end))

print(f"Total (surface, range) jobs: {len(jobs)}")

# ─── SET UP DATABASE & NEW TABLE ───────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="noamshamir",
    password="noampass",
    database="noams"
)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS player_range_elo")
cur.execute("""
CREATE TABLE player_range_elo (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  player_id       INT         NOT NULL,
  range_from      INT         NOT NULL,
  range_to        INT         NOT NULL,
  elo             INT         NOT NULL,
  peak_elo        INT         NOT NULL,
  last_match_date DATE,
  is_active       BOOLEAN     NOT NULL,
  surface         VARCHAR(20) NOT NULL,
  INDEX(player_id),
  INDEX(range_from),
  INDEX(range_to),
  INDEX(surface)
)
""")
conn.commit()

# ─── MAIN LOOP WITH PROGRESS BAR ────────────────────────────────────────────────
for surface, yr_from, yr_to in tqdm(jobs, desc="Building range Elo"):
    # filter by date range
    sub = matches[
        (matches["tourney_date"].dt.year >= yr_from) &
        (matches["tourney_date"].dt.year <= yr_to)
    ]
    # filter by surface if not overall
    if surface != "overall":
        sub = sub[sub["surface"] == surface]

    # initialize trackers
    last_elo = {}
    peak_elo = {}
    last_date = {}

    # process each match in chronological order
    for _, row in sub.iterrows():
        d = row["tourney_date"]
        w = row["winner_id"]
        l = row["loser_id"]

        # seed players at INITIAL_ELO
        if w not in last_elo:
            last_elo[w]  = INITIAL_ELO
            peak_elo[w]  = INITIAL_ELO
            last_date[w] = d
        if l not in last_elo:
            last_elo[l]  = INITIAL_ELO
            peak_elo[l]  = INITIAL_ELO
            last_date[l] = d

        # compute new ratings
        new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])

        # update trackers
        last_elo[w]  = new_w
        last_elo[l]  = new_l
        peak_elo[w]  = max(peak_elo[w], new_w)
        peak_elo[l]  = max(peak_elo[l], new_l)
        last_date[w] = max(last_date[w], d)
        last_date[l] = max(last_date[l], d)

    # now insert one row per player_id
    for pid, elo_val in last_elo.items():
        pk   = peak_elo[pid]
        lmd  = last_date[pid].strftime("%Y-%m-%d")
        # active = did they play at or after the start of the range?
        active_flag = 1 if last_date[pid].year >= yr_from else 0

        cur.execute("""
          INSERT INTO player_range_elo
            (player_id, range_from, range_to,
             elo, peak_elo, last_match_date,
             is_active, surface)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
          pid,
          yr_from,
          yr_to,
          round(elo_val),
          round(pk),
          lmd,
          active_flag,
          surface
        ))

# final commit
conn.commit()
cur.close()
conn.close()
print("Done — all ranges & surfaces populated!")