import argparse
import pandas as pd
import glob
import os

K = 32
elo_scores = []
elo_differences = {}
last_elo = {}

def compute_elo(args):
    matches = get_all_matches(args.start_year, args.end_year, args.input_directory)
    matches = matches.sort_values(by=['tourney_date', 'match_num'])

    for index, row in matches.iterrows():
        winner_id = row['winner_id']
        loser_id = row['loser_id']

        if winner_id not in last_elo:
            update_elo(winner_id, 1000, row['tourney_date'])
        if loser_id not in last_elo:
            update_elo(loser_id, 1000, row['tourney_date'])

        elo_diff = round(abs(last_elo[winner_id] - last_elo[loser_id]))
        higher_rated_won = last_elo[winner_id] >= last_elo[loser_id]

        if elo_diff not in elo_differences:
            elo_differences[elo_diff] = {'wins': 0, 'total': 0}

        if higher_rated_won:
            elo_differences[elo_diff]['wins'] += 1
        elo_differences[elo_diff]['total'] += 1

        new_winner_elo, new_loser_elo = compute_new_elo(last_elo[winner_id], last_elo[loser_id])

        update_elo(winner_id, new_winner_elo, row['tourney_date'])
        update_elo(loser_id, new_loser_elo, row['tourney_date'])


def update_elo(player_id, new_elo, date):
    global elo_scores
    last_elo[player_id] = new_elo

    elo_record = {'player_id': player_id, 'elo': new_elo, 'date': date}
    elo_scores.append(elo_record)


def compute_new_elo(winner_current_elo, loser_current_elo):
    winner_expected = 1.0 / (1.0 + 10.0 ** ((loser_current_elo - winner_current_elo) / 400.0))
    change = K * (1 - winner_expected)

    return winner_current_elo + change, loser_current_elo - change


def get_all_matches(start_year, end_year, input_directory):
    match_csvs = glob.glob(os.path.join(input_directory, "*"))

    df_from_each_file = []

    for f in match_csvs:
        year = int(f[-8: -4])
        if start_year <= year <= end_year:
            df_from_each_file.append(pd.read_csv(f))

    return pd.concat(df_from_each_file, ignore_index=True)


def peak_elo(df):
    peak_elos = df.sort_values(by='elo', ascending=False)
    peak_elos = peak_elos.groupby('player_id').head(1)
    return peak_elos

def win_chance_by_elo(elo_differences):
    elo_diff_avgs = {}
    for elo_diff, results in elo_differences.items():
        elo_diff_avgs[elo_diff] = round((results['wins'] / results['total'])*100)
    return dict(sorted(elo_diff_avgs.items()))


def main():
    parser = argparse.ArgumentParser(description="Calculate the elo's of tennis players")
    parser.add_argument('--start-year', type=int, default=1968, help="year to start elo computation")
    parser.add_argument('--end-year', type=int, default=2024, help="year to stop elo computation")
    parser.add_argument("--output-file", default="data/elo/elo.csv")
    parser.add_argument("--input-directory", default="data/matches")

    args = parser.parse_args()
    compute_elo(args)

    elo_df = pd.DataFrame(elo_scores)
    print(win_chance_by_elo(elo_differences))


if __name__ == "__main__":
    main()

import math
import pandas as pd
import matplotlib.pyplot as plt

def compute_calibration_error(differences_dict, scale_factor=400):
    total_matches = 0
    total_squared_error = 0
    calibration_data = []

    for diff, results in sorted(differences_dict.items()):
        wins = results['wins']
        total = results['total']
        observed_prob = wins / total  # observed win probability in this bucket
        # For Elo, predicted win probability based on rating difference d:
        predicted_prob = 1 / (1 + 10 ** ( - diff / scale_factor ))
        squared_error = (observed_prob - predicted_prob) ** 2 * total
        total_matches += total
        total_squared_error += squared_error
        calibration_data.append((diff, observed_prob, predicted_prob, total, squared_error))
    
    mse = total_squared_error / total_matches if total_matches > 0 else None
    rmse = math.sqrt(mse) if mse is not None else None
    return rmse, calibration_data

def compute_atp_calibration_error(differences_dict, scale_factor=400, atp_scale=15):
    """
    Similar to compute_calibration_error(), but for ATP differences.
    We first scale the ATP difference (using atp_scale) to get an effective difference.
    """
    total_matches = 0
    total_squared_error = 0
    calibration_data = []
    for diff, results in sorted(differences_dict.items()):
        wins = results['wins']
        total = results['total']
        observed_prob = wins / total
        # Scale the ATP difference for a fair comparison:
        effective_diff = diff / atp_scale
        predicted_prob = 1 / (1 + 10 ** ( - effective_diff / scale_factor ))
        squared_error = (observed_prob - predicted_prob) ** 2 * total
        total_matches += total
        total_squared_error += squared_error
        calibration_data.append((diff, observed_prob, predicted_prob, total, squared_error))
    mse = total_squared_error / total_matches if total_matches > 0 else None
    rmse = math.sqrt(mse) if mse is not None else None
    return rmse, calibration_data

# Calculate calibration error for Elo differences and ATP differences
elo_rmse, elo_calibration_data = compute_calibration_error(elo_differences, scale_factor=400)
atp_rmse, atp_calibration_data = compute_atp_calibration_error(atp_differences, scale_factor=400, atp_scale=15)

print(f"Elo Calibration RMSE: {elo_rmse:.3f}")
print(f"ATP Calibration RMSE: {atp_rmse:.3f}")

# For clarity, let's also print a table showing for each bucket the observed and predicted win chances.
elo_calib_df = pd.DataFrame(elo_calibration_data, columns=['Elo Diff', 'Observed Win %', 'Predicted Win %', 'Total Matches', 'Weighted Squared Error'])
print("Elo Calibration Data:")
print(elo_calib_df)

atp_calib_df = pd.DataFrame(atp_calibration_data, columns=['ATP Diff', 'Observed Win %', 'Predicted Win %', 'Total Matches', 'Weighted Squared Error'])
print("ATP Calibration Data:")
print(atp_calib_df)

# Optional: Plot the calibration curves for a visual comparison
plt.figure(figsize=(10, 5))
plt.plot(elo_calib_df['Elo Diff'], elo_calib_df['Observed Win %'] * 100, 'o-', label='Observed Elo Win %')
plt.plot(elo_calib_df['Elo Diff'], elo_calib_df['Predicted Win %'] * 100, 'o-', label='Predicted Elo Win %')
plt.xlabel("Difference in Elo")
plt.ylabel("Win Chance (%)")
plt.title("Elo Calibration Curve")
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(atp_calib_df['ATP Diff'], atp_calib_df['Observed Win %'] * 100, 'o-', label='Observed ATP Win %')
plt.plot(atp_calib_df['ATP Diff'], atp_calib_df['Predicted Win %'] * 100, 'o-', label='Predicted ATP Win %')
plt.xlabel("Difference in ATP Points")
plt.ylabel("Win Chance (%)")
plt.title("ATP Calibration Curve")
plt.legend()
plt.grid(True)
plt.show()