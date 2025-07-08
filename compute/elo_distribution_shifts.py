#!/usr/bin/env python3
# predictive_accuracy_by_year_with_progress.py

import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
from tqdm import tqdm  # pip install tqdm if you don’t have it

K = 32
INPUT_DIR = "../data/matches"
START_YEAR = 1968
END_YEAR   = 2024

def parse_date(d):
    return (
        pd.to_datetime(str(int(d)), format="%Y%m%d")
        if (isinstance(d, (int, float)) or (isinstance(d, str) and d.isdigit()))
        else pd.to_datetime(d)
    )

def compute_new_elo(w, l):
    exp   = 1 / (1 + 10 ** ((l - w) / 400))
    delta = K * (1 - exp)
    return w + delta, l - delta

def get_matches(year):
    files = glob.glob(os.path.join(INPUT_DIR, "*"))
    dfs = []
    for f in files:
        try:
            y = int(os.path.basename(f)[-8:-4])
        except ValueError:
            continue
        if START_YEAR <= y <= year:
            df = pd.read_csv(f)
            df['tourney_date'] = df['tourney_date'].apply(parse_date)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

if __name__ == "__main__":
    year_acc = {}
    last_elo  = {}

    # outer progress: years
    for yr in tqdm(range(START_YEAR, END_YEAR + 1), desc="Processing years"):
        matches = (
            get_matches(yr)
            .sort_values('tourney_date')
            .reset_index(drop=True)
        )

        correct = total = 0
        last_elo.clear()

        # inner progress: matches in this year
        for _, r in tqdm(
            matches.iterrows(),
            total=len(matches),
            desc=f" Year {yr}",
            leave=False
        ):
            w, l = r['winner_id'], r['loser_id']

            # init Elo
            last_elo.setdefault(w, 1500)
            last_elo.setdefault(l, 1500)

            # make prediction
            diff = last_elo[w] - last_elo[l]
            if diff != 0:
                fav = w if diff > 0 else l
                correct += (fav == w)
                total   += 1

            # update ratings
            new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])
            last_elo[w], last_elo[l] = new_w, new_l

        # record accuracy
        year_acc[yr] = (correct / total * 100) if total else None

    # build plot data (skip years with no matches)
    yrs  = [y for y, acc in year_acc.items() if acc is not None]
    vals = [year_acc[y] for y in yrs]

    # plot
    plt.figure(figsize=(12, 5))
    plt.plot(yrs, vals, marker='o')
    plt.xlabel("Year")
    plt.ylabel("Favored-by-Elo Win %")
    plt.title("Elo Predictive Accuracy by Year")
    plt.grid(True)
    plt.tight_layout()
    plt.show()