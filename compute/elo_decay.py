import pandas as pd
import glob
import os
import math

K = 96

elo_scores = []
frontend_data_latest = {}
elo_differences = {}
atp_differences = {}
last_elo = {}
peak_elo_tracker = {}
last_played_date = {}
last_match_date = {}
total_decay = {}


def parse_date(date):
    if isinstance(date, (int, float)):
        # numeric yyyymmdd
        return pd.to_datetime(str(int(date)), format='%Y%m%d')
    if isinstance(date, str) and date.isdigit() and len(date) == 8:
        return pd.to_datetime(date, format='%Y%m%d')
    return pd.to_datetime(date)


def apply_decay(player_id, current_date):
    if player_id not in last_played_date:
        return

    prev = last_played_date[player_id]
    curr = parse_date(current_date)
    days = (curr - prev).days

    # only decay past two years (730 days), and only if they still have Elo to lose
    if days > 730 and last_elo[player_id] > 0:
        decay_points = days - 730
        # never subtract more than they actually have
        actual_decay = min(decay_points, last_elo[player_id])

        last_elo[player_id] -= actual_decay
        total_decay[player_id] = total_decay.get(player_id, 0) + actual_decay

        # reset the baseline to today so we don't double-count
        last_played_date[player_id] = curr


def update_elo(player_id, date, new_elo, age, atp_points=None):

    date_ts = parse_date(date)

    # Set current Elo
    last_elo[player_id] = new_elo

    # Record history
    elo_scores.append({
        'player_id': player_id,
        'elo': new_elo,
        'atp_points': atp_points,
        'date': date_ts
    })

    # Track peak Elo
    if player_id not in peak_elo_tracker or new_elo > peak_elo_tracker[player_id]:
        peak_elo_tracker[player_id] = new_elo

    # Update decay baseline and final match date
    last_played_date[player_id] = date_ts
    last_match_date[player_id] = max(last_match_date.get(player_id, date_ts), date_ts)

    # Prepare frontend record
    frontend_data_latest[player_id] = {
        'player': player_id,
        'age': math.floor(age) if pd.notna(age) else 0,
        'elo': round(new_elo),
        'hardcourtElo': round(new_elo),
        'clayElo': round(new_elo),
        'grassElo': round(new_elo),
        'peakElo': round(peak_elo_tracker[player_id]),
        'decay': total_decay.get(player_id, 0),
        'active': True
    }

def compute_new_elo(w_elo, l_elo):
    expected = 1.0 / (1.0 + 10.0 ** ((l_elo - w_elo) / 400.0))
    change = K * (1 - expected)
    return w_elo + change, l_elo - change


def get_all_matches(start_year, end_year, input_directory):
    files = glob.glob(os.path.join("../data/matches", "*"))
    dfs = []
    for f in files:
        year = int(os.path.basename(f)[-8:-4])
        if start_year <= year <= end_year:
            df = pd.read_csv(f)
            df['tourney_date'] = df['tourney_date'].apply(parse_date)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def update_diff_stats(w_m, l_m, storage, div):
    diff = abs(w_m - l_m)
    interval = math.ceil(diff / div) if diff > 0 else 0
    if interval <= 0:
        return
    bucket = round(diff / interval) * interval
    won = (w_m > l_m)
    if bucket not in storage:
        storage[bucket] = {'wins': 0, 'total': 0}
    if won:
        storage[bucket]['wins'] += 1
    storage[bucket]['total'] += 1


# --- Main processing ---
matches = get_all_matches(1968, 2024, '../data/matches')
matches = matches.sort_values(by=['tourney_date', 'match_num'])

atp_upsets = 0
elo_upsets = 0
games = 0

for _, row in matches.iterrows():
    date = row['tourney_date']
    w_id, l_id = row['winner_id'], row['loser_id']
    w_pts, l_pts = row['winner_rank_points'], row['loser_rank_points']

    # Initialize if unseen
    if w_id not in last_elo:
        update_elo(w_id, date, 1500, row['winner_age'], w_pts if pd.notna(w_pts) else None)
    if l_id not in last_elo:
        update_elo(l_id, date, 1500, row['loser_age'], l_pts if pd.notna(l_pts) else None)

    # Decay before new match
    apply_decay(w_id, date)
    apply_decay(l_id, date)

    # Stats
    update_diff_stats(last_elo[w_id], last_elo[l_id], elo_differences, 100)
    if pd.notna(w_pts) and pd.notna(l_pts):
        update_diff_stats(w_pts, l_pts, atp_differences, 100)
        if l_pts > w_pts:
            atp_upsets += 1
        if last_elo[l_id] > last_elo[w_id]:
            elo_upsets += 1
        games += 1

    # Compute new Elos
    new_w, new_l = compute_new_elo(last_elo[w_id], last_elo[l_id])
    update_elo(w_id, date, new_w, row['winner_age'], w_pts if pd.notna(w_pts) else None)
    update_elo(l_id, date, new_l, row['loser_age'], l_pts if pd.notna(l_pts) else None)

print(f'Elo upsets: {elo_upsets}')
print(f'Atp upsets: {atp_upsets}')

# --- Final decay pass up to today ---
today = pd.Timestamp('2024-01-01')
for pid, match_date in last_match_date.items():
    # ensure decay baseline is last match date
    last_played_date[pid] = match_date
    apply_decay(pid, today)

    elo_now = last_elo[pid]
    rec = frontend_data_latest[pid]

    # calculate true age: age at last match + whole years elapsed since then
    years_since_last = (today - match_date).days / 365.25
    true_age = math.floor(rec['age'] + years_since_last)

    rec.update({
        'elo': math.ceil(elo_now),
        'decay': total_decay.get(pid, 0),
        'trueAge': true_age,
        'active': False if total_decay.get(pid, 0) > 0 else True
    })

# --- Output top 100 by peak Elo ---
final_frontend_data = list(frontend_data_latest.values())
final_frontend_data.sort(key=lambda x: x['peakElo'], reverse=True)
print(final_frontend_data[:100])