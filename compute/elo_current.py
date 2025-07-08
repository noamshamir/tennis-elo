import pandas as pd
import glob
import os
import math
import matplotlib.pyplot as plt
from datetime import datetime

K = 32

elo_scores        = []
elo_differences   = {}
atp_differences   = {}
last_elo          = {}
peak_elo_tracker  = {}
last_match_date   = {}

def parse_date(date):
    if isinstance(date, (int, float)):
        return pd.to_datetime(str(int(date)), format='%Y%m%d')
    if isinstance(date, str) and date.isdigit() and len(date) == 8:
        return pd.to_datetime(date, format='%Y%m%d')
    return pd.to_datetime(date)

def update_elo(player_id, date, new_elo, age, atp_points=None):
    date_ts = parse_date(date)
    last_elo[player_id] = new_elo
    peak_elo_tracker[player_id] = max(peak_elo_tracker.get(player_id, new_elo), new_elo)
    last_match_date[player_id] = max(last_match_date.get(player_id, date_ts), date_ts)

def compute_new_elo(w_elo, l_elo):
    expected = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
    delta    = K * (1 - expected)
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

def win_chance_by_elo(elo_differences):
    elo_diff_avgs = {}
    for elo_diff, results in elo_differences.items():
        elo_diff_avgs[elo_diff] = round((results['wins'] / results['total']) * 100)
    return dict(sorted(elo_diff_avgs.items()))

def win_chance_by_atp(atp_differences):
    atp_diff_avgs = {}
    for atp_diff, results in atp_differences.items():
        atp_diff_avgs[atp_diff] = round((results['wins'] / results['total']) * 100)
    return dict(sorted(atp_diff_avgs.items()))

years = list(range(1968, 2025))

for start_year in years:
    end_year = start_year
    if start_year >= end_year:
        continue

    print(f"\nProcessing {start_year}–{end_year}...")

    matches = get_all_matches(start_year, end_year, "../data/matches")
    if matches.empty:
        print("  No matches; skipping.")
        continue

    matches = matches.sort_values(by=['tourney_date', 'match_num'])

    elo_scores.clear()
    elo_differences.clear()
    atp_differences.clear()
    last_elo.clear()
    peak_elo_tracker.clear()
    last_match_date.clear()

    for _, row in matches.iterrows():
        d = row['tourney_date']
        w, l = row['winner_id'], row['loser_id']
        w_pts = row.get('winner_rank_points', None)
        l_pts = row.get('loser_rank_points', None)

        if w not in last_elo:
            update_elo(w, d, 1500, row['winner_age'], w_pts if pd.notna(w_pts) else None)
        if l not in last_elo:
            update_elo(l, d, 1500, row['loser_age'], l_pts if pd.notna(l_pts) else None)
        elo_diff = round(last_elo[w] - last_elo[l])
        if elo_diff != 0:
            favored_elo = w if elo_diff > 0 else l
            favored_elo_won = (favored_elo == w)

            elo_dif = abs(elo_diff)
            elo_differences.setdefault(elo_dif, {'wins': 0, 'total': 0})
            elo_differences[elo_dif]['wins'] += int(favored_elo_won)
            elo_differences[elo_dif]['total'] += 1

        if pd.notna(w_pts) and pd.notna(l_pts):
            atp_diff = round(w_pts - l_pts)
            if atp_diff != 0:
                favored_atp = w if atp_diff > 0 else l
                favored_atp_won = (favored_atp == w)

                atp_dif = abs(atp_diff)
                atp_differences.setdefault(atp_dif, {'wins': 0, 'total': 0})
                atp_differences[atp_dif]['wins'] += int(favored_atp_won)
                atp_differences[atp_dif]['total'] += 1

        new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])
        update_elo(w, d, new_w, row['winner_age'], w_pts)
        update_elo(l, d, new_l, row['loser_age'], l_pts)

win_chance_by_elo_df = win_chance_by_elo(elo_differences)
win_chance_by_atp_df = win_chance_by_atp(atp_differences)

elo_series = pd.Series(win_chance_by_elo_df)
atp_series = pd.Series(win_chance_by_atp_df)

plt.figure(figsize=(12, 6))
elo_series.plot(label="ELO Difference", linewidth=2)
atp_series.plot(label="ATP Points Difference", linewidth=2)
plt.xlabel("Rating Difference")
plt.ylabel("Favored Player Winning Chance (%)")
plt.title("Win % Correlation: ELO vs ATP Points")
plt.legend()
plt.grid(True)
plt.show()