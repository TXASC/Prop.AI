import pandas as pd
import joblib
import requests
import os

def get_odds():
    # Fetch NBA player prop odds from SportsDataIO
    api_key = os.getenv("SPORTSDATAIO_API_KEY", "811492965d2246fdbedb49c47294faf5")
    import datetime
    today = datetime.date.today()
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    import json
    os.makedirs("output", exist_ok=True)
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://api.sportsdata.io/v3/nba/odds/json/PlayerPropsByDate/{date_str}"
        print(f"Requesting NBA player props for {date_str}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            with open(f"output/odds_raw_{date_str}.json", "w", encoding="utf-8") as f:
                f.write(response.text)
            if response.status_code != 200:
                print(f"Failed to fetch odds: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                continue
            data = response.json()
            if data:
                print(f"Found {len(data)} props for {date_str}.")
                return data
            else:
                print(f"No props found for {date_str}.")
        except Exception as e:
            print(f"Error fetching odds for {date_str}: {e}")
            continue
    print("No NBA player props found for the last 7 days.")
    return None

def find_value():
    model = joblib.load("models/projection_model.pkl")
    df = pd.read_csv("data/processed/clean_player_stats.csv")

    odds_data = get_odds()
    if not odds_data:
        print("No odds data available. Using placeholder prop lines.")
        df['prop_line'] = df['PRA'] - 1.5
    else:
        # Attempt to match player names and assign prop lines
        prop_lines = {}
        for item in odds_data:
            name = item.get('PlayerName') or item.get('Name')
            stat = item.get('StatType')
            value = item.get('Value')
            # Only use PRA or Points+Rebounds+Assists props
            if name and stat and value and stat.upper() in ['PRA', 'POINTS+REBOUNDS+ASSISTS']:
                prop_lines[name.strip().lower()] = value
        def get_prop_line(player):
            return prop_lines.get(player.strip().lower(), None)
        df['prop_line'] = df['PLAYER_NAME'].apply(get_prop_line)
        # Fallback for missing odds (avoid chained assignment warning)
        df['prop_line'] = df['prop_line'].fillna(df['PRA'] - 1.5)

    df['projected_PRA'] = model.predict(df[['MIN']])
    df['edge'] = df['projected_PRA'] - df['prop_line']
    os.makedirs("output", exist_ok=True)
    value_plays = df[df['edge'] > 2]
    value_plays.to_csv("output/value_plays.csv", index=False)

if __name__ == "__main__":
    find_value()
