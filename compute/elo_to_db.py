import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
import math

K = 32

elo_scores = []
frontend_data_latest = {}
elo_differences = {}
atp_differences = {}
last_elo = {}
peak_elo_tracker = {}
last_played_date = {}

def update_elo(player_id, date, new_elo, age, atp_points=None):
    global elo_scores, frontend_data_latest, last_elo, peak_elo_tracker, last_played_date

    last_elo[player_id] = new_elo
    last_played_date[player_id] = date

    if player_id not in peak_elo_tracker or new_elo > peak_elo_tracker[player_id]:
        peak_elo_tracker[player_id] = new_elo

    clean_age = age if pd.notna(age) else 0

    has_played_last_year = False
    if pd.notna(date) and pd.notna(last_played_date[player_id]):
        year_gap = (pd.to_datetime(date) - pd.to_datetime(last_played_date[player_id])).days
        has_played_last_year = year_gap <= 365

    elo_record = {
        'player_id': player_id,
        'elo': new_elo,
        'atp_points': atp_points,
        'date': date
    }

    frontend_record = {
        'player': player_id,
        'age': clean_age,
        'elo': round(new_elo),
        'hardcourtElo': round(new_elo),
        'clayElo': round(new_elo),
        'grassElo': round(new_elo),
        'peakElo': round(peak_elo_tracker[player_id]),
        'active': has_played_last_year
    }

    elo_scores.append(elo_record)
    frontend_data_latest[player_id] = frontend_record
def compute_new_elo(winner_current_elo, loser_current_elo):
    winner_expected = 1.0 / (1.0 + 10.0 ** ((loser_current_elo - winner_current_elo) / 400.0))
    change = K * (1 - winner_expected)

    return winner_current_elo + change, loser_current_elo - change

def get_all_matches(start_year, end_year, input_directory):
    match_csvs = glob.glob(os.path.join(input_directory, "*"))

    df_from_each_file = []

    for f in match_csvs:
        print(f"path {f}")
        year = int(f[-8: -4])
        if start_year <= year <= end_year:
            df_from_each_file.append(pd.read_csv(f))

    return pd.concat(df_from_each_file, ignore_index=True)

# def decay_elo(player_id, current_date):
#     if player_id not in last_played_date:
#         return

#     last_date = pd.to_datetime(last_played_date[player_id])
#     current_date = pd.to_datetime(current_date)

#     days_inactive = (current_date - last_date).days
#     num_half_years = days_inactive // 183

#     if num_half_years > 0:
#         decay_amount = 100 * num_half_years
#         last_elo[player_id] -= decay_amount
#         update_elo(player_id, current_date, age, la)

def update_elo_diff_stats(winner_metric, loser_metric, storage, divider_val):
    float_diff = abs(winner_metric - loser_metric)
    # if float_diff < 5000:
    interval = math.ceil(float_diff / divider_val)
    if interval > 0:
        diff_bucket = round(float_diff / interval) * interval
    else:
        return

    higher_rated_won = winner_metric > loser_metric

    if diff_bucket not in storage:
        storage[diff_bucket] = {'wins': 0, 'total': 0}

    if higher_rated_won:
        storage[diff_bucket]['wins'] += 1
    storage[diff_bucket]['total'] += 1

matches = get_all_matches(1968, 2024, '../data/matches')
matches = matches.sort_values(by=['tourney_date', 'match_num'])

atp_upsets = 0
elo_upsets = 0
games = 0

for index, row in matches.iterrows():
    winner_id = row['winner_id']
    loser_id = row['loser_id']
    winner_points = row['winner_rank_points']
    loser_points = row['loser_rank_points']

    if winner_id not in last_elo:
        if pd.notna(winner_points):
            update_elo(winner_id, row['tourney_date'], 1000, row['winner_age'], winner_points)
        else:
            update_elo(winner_id, row['tourney_date'], 1000, row['winner_age'])
    if loser_id not in last_elo:
        if pd.notna(loser_points):
            update_elo(loser_id, row['tourney_date'], 1000, row['loser_age'], loser_points)
        else:
            update_elo(loser_id, row['tourney_date'], 1000, row['loser_age'])

    update_elo_diff_stats(last_elo[winner_id], last_elo[loser_id], elo_differences, 100)

    if pd.notna(winner_points) and pd.notna(loser_points):
        update_elo_diff_stats(winner_points, loser_points, atp_differences, 100)

        if loser_points > winner_points:
            atp_upsets += 1
        if last_elo[loser_id] > last_elo[winner_id]:
            elo_upsets += 1

        games+=1

    # decay_elo(winner_id, row['tourney_date'])
    # decay_elo(loser_id, row['tourney_date'])

    new_winner_elo, new_loser_elo = compute_new_elo(last_elo[winner_id], last_elo[loser_id])

    update_elo(winner_id, row['tourney_date'], new_winner_elo, row['winner_age'], winner_points)
    update_elo(loser_id, row['tourney_date'], new_loser_elo, row['loser_age'], loser_points)

print(f'Elo upsets: {elo_upsets}')
print(f'Atp upsets: {atp_upsets}')
# print(games)

# elo_df = pd.DataFrame(elo_scores)
# print(elo_df)

final_frontend_data = list(frontend_data_latest.values())

final_frontend_data.sort(key=lambda x: x['peakElo'], reverse=True)

print(final_frontend_data[:100])