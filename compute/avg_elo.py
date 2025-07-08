# year_end_top10.py
# Requires: tqdm (pip install tqdm)
import pandas as pd
import glob, os
import matplotlib.pyplot as plt
from tqdm import tqdm

K = 32
INPUT_DIR = "../data/matches"
START_YEAR = 1968
END_YEAR   = 2024

def parse_date(d):
    if isinstance(d, (int, float)):
        return pd.to_datetime(str(int(d)), format="%Y%m%d")
    if isinstance(d, str) and d.isdigit():
        return pd.to_datetime(d, format="%Y%m%d")
    return pd.to_datetime(d)

def compute_new_elo(w, l):
    expected = 1 / (1 + 10 ** ((l - w) / 400))
    delta = K * (1 - expected)
    return w + delta, l - delta

if __name__ == "__main__":
    # Load all matches once
    files = glob.glob(os.path.join(INPUT_DIR, "*"))
    all_matches = []
    for f in files:
        try:
            y = int(os.path.basename(f)[-8:-4])
        except:
            continue
        if START_YEAR <= y <= END_YEAR:
            df = pd.read_csv(f)
            df["tourney_date"] = df["tourney_date"].apply(parse_date)
            all_matches.append(df)
    all_matches = (pd.concat(all_matches, ignore_index=True)
                       .sort_values("tourney_date"))

    # Compute year-end top 10 Elo for each year with single progress bar
    year_end = {}
    for yr in tqdm(range(START_YEAR, END_YEAR + 1), desc="Processing years"):
        last_elo = {}
        cutoff = pd.to_datetime(f"{yr}1231", format="%Y%m%d")
        matches = all_matches[all_matches["tourney_date"] <= cutoff]
        for _, r in matches.iterrows():
            w, l = r["winner_id"], r["loser_id"]
            if w not in last_elo:
                last_elo[w] = 1500
            if l not in last_elo:
                last_elo[l] = 1500
            new_w, new_l = compute_new_elo(last_elo[w], last_elo[l])
            last_elo[w], last_elo[l] = new_w, new_l
        year_end[yr] = sorted(last_elo.values(), reverse=True)[:10]

    df = pd.DataFrame(year_end, index=[f"Top {i+1}" for i in range(10)])

    # Plot
    plt.figure(figsize=(14, 6))
    for rank in df.index:
        plt.plot(df.columns, df.loc[rank], label=rank)
    plt.xlabel("Year")
    plt.ylabel("Elo at Year-End")
    plt.title("Year-End Top 10 Elo by Era")
    plt.legend(ncol=2)
    plt.grid(True)
    plt.tight_layout()
    plt.show()