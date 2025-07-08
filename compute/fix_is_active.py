import mysql.connector
from tqdm import tqdm
from datetime import datetime, timedelta

# Connect to database
conn = mysql.connector.connect(
    host="localhost",
    user="noamshamir",
    password="noampass",
    database="noams"
)
cur = conn.cursor()

# Fetch all rows: id, last_match_date, range_to
cur.execute("SELECT id, last_match_date, range_to FROM player_range_elo")
rows = cur.fetchall()

# Prepare update list
updates = []
for row in tqdm(rows, desc="Evaluating is_active"):
    row_id, last_match_date, range_to = row

    if last_match_date is None:
        is_active = 0
    else:
        cutoff = (datetime(range_to, 12, 31) - timedelta(days=365)).date()        
        is_active = 1 if last_match_date >= cutoff else 0
        is_active = 1 if last_match_date >= cutoff else 0

    updates.append((is_active, row_id))

# Apply updates in bulk
cur.executemany("UPDATE player_range_elo SET is_active = %s WHERE id = %s", updates)
conn.commit()

print(f"Updated {len(updates)} rows.")
cur.close()
conn.close()