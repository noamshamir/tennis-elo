import pandas as pd
import glob
import os
import mysql.connector
from datetime import datetime

K = 32

last_elo = {}
peak_elo_tracker = {}
last_match_date = {}

def parse_date(date):
    if isinstance(date, (int, float)):
        return pd.to_datetime(str(int(date)), format='%Y%m%d')
    if isinstance(date, str) and date.isdigit() and len(date) == 8:
        return pd.to_datetime(date, format='%Y%m%d')
    return pd.to_datetime(date)

def update_elo(player_id, date, new_elo):
    date_ts = parse_date(date)
    last_elo[player_id] = new_elo
    peak_elo_tracker[player_id] = max(peak_elo_tracker.get(player_id, new_elo), new_elo)
    last_match_date[player_id] = max(last_match_date.get(player_id, date_ts), date_ts)
    return date_ts, round(new_elo)

def compute_new_elo(w_elo, l_elo):
    expected = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
    delta = K * (1 - expected)
    return w_elo + delta, l_elo - delta

def get_all_matches(start_year, end_year, input_directory):
    files = glob.glob(os.path.join(input_directory, "*"))
    dfs = []
    for f in files:
        try:
            year = int(os.path.basename(f)[-8:-4])
        except ValueError:
            continue
        if start_year <= year <= end_year:
            df = pd.read_csv(f)
            df['tourney_date'] = df['tourney_date'].apply(parse_date)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

conn = mysql.connector.connect(
    host="localhost",
    user="noamshamir",
    password="noampass",
    database="noams"
)
cursor = conn.cursor()

# -- Recreate player_entries table --
cursor.execute("DROP TABLE IF EXISTS player_entry")
cursor.execute("""
CREATE TABLE player_entry (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  player_id   INT NOT NULL,
  date  DATE    NOT NULL,
  elo_before  INT     NOT NULL,
  elo_after   INT     NOT NULL,
  won         BOOLEAN NOT NULL,
  match_id    VARCHAR(100) NOT NULL,
  score       VARCHAR(50),
  INDEX (player_id),
  INDEX (date),
  INDEX (match_id)
);
""")
conn.commit()

matches = get_all_matches(1968, 2024, "../data/matches")
if matches.empty:
    print("No matches found for full range.")
    cursor.close()
    conn.close()
    exit()

matches = matches.sort_values(by=['tourney_date','match_num'])

last_elo.clear()
peak_elo_tracker.clear()
last_match_date.clear()

for i, row in matches.iterrows():
    d     = row['tourney_date']
    w     = row['winner_id']
    l     = row['loser_id']
    score = row['score']
    if pd.isna(score):
        score = ''
    match_id = i

    if w not in last_elo:
        date_ts, elo_val = update_elo(w, d, 1500)
        
    if l not in last_elo:
        date_ts, elo_val = update_elo(l, d, 1500)

    before_w = last_elo[w]
    before_l = last_elo[l]
    new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])

    date_ts, elo_val = update_elo(w, d, new_w)
    cursor.execute(
        "INSERT INTO player_entry (player_id, date, elo_before, elo_after, won, match_id, score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (w, date_ts.strftime("%Y-%m-%d"), before_w, elo_val, True, match_id, score)
    )

    date_ts, elo_val = update_elo(l, d, new_l)
    cursor.execute(
        "INSERT INTO player_entry (player_id, date, elo_before, elo_after, won, match_id, score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (l, date_ts.strftime("%Y-%m-%d"), before_l, elo_val, False, match_id, score)
    )

conn.commit()
print(f"Inserted {cursor.rowcount} total entries into player_entries.")

cursor.close()
conn.close()
print("Done.")