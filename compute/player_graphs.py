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

if __name__ == "__main__":
    start_year = 1968
    end_year = 2024
    input_directory = "../data/matches"

    matches = get_all_matches(start_year, end_year, input_directory)

    elo_scores.clear()
    elo_differences.clear()
    atp_differences.clear()
    last_elo.clear()
    peak_elo_tracker.clear()
    last_match_date.clear()

    if not matches.empty:
        print("Columns found in match data:", matches.columns.tolist())

        if 'match_num' not in matches.columns:
            matches['match_num'] = range(len(matches))

        if 'tourney_date' not in matches.columns:
            print("Error: 'tourney_date' column not found in the data.")
        else:
            matches = matches.sort_values(by=['tourney_date', 'match_num'])

            for _, row in matches.iterrows():
                d = row['tourney_date']
                w, l = row['winner_id'], row['loser_id']
                w_pts = row.get('winner_rank_points', None)
                l_pts = row.get('loser_rank_points', None)

                if w not in last_elo:
                    update_elo(w, d, 1500, row['winner_age'], w_pts if pd.notna(w_pts) else None)
                if l not in last_elo:
                    update_elo(l, d, 1500, row['loser_age'], l_pts if pd.notna(l_pts) else None)

                diff_elo = round(last_elo[w] - last_elo[l])
                diff_atp = round((w_pts if pd.notna(w_pts) else 0) - (l_pts if pd.notna(l_pts) else 0))

                elo_differences.setdefault(diff_elo, {'wins': 0, 'total': 0})
                elo_differences[diff_elo]['wins'] += 1
                elo_differences[diff_elo]['total'] += 1

                atp_differences.setdefault(diff_atp, {'wins': 0, 'total': 0})
                atp_differences[diff_atp]['wins'] += 1
                atp_differences[diff_atp]['total'] += 1

                new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])
                update_elo(w, d, new_w, row['winner_age'], w_pts if pd.notna(w_pts) else None)
                update_elo(l, d, new_l, row['loser_age'], l_pts if pd.notna(l_pts) else None)

            elo_df = win_chance_by_elo(elo_differences)
            atp_df = win_chance_by_atp(atp_differences)

            elo_series = pd.Series(elo_df)
            atp_series = pd.Series(atp_df)

            plt.figure(figsize=(12, 6))
            elo_series.plot(label="ELO Difference", linewidth=2)
            atp_series.plot(label="ATP Points Difference", linewidth=2)
            plt.xlabel("Rating Difference")
            plt.ylabel("Favored Player Winning Chance (%)")
            plt.title("Win % Correlation: ELO vs ATP Points")
            plt.legend()
            plt.grid(True)
            plt.show()
    else:
        print("No match data found in the given year range.")