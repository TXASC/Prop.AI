import requests
import pandas as pd
import os

def get_injuries():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    r = requests.get(url)
    data = r.json()
    players = []
    for team in data.get("injuries", []):
        for athlete in team.get("athletes", []):
            players.append({
                "player": athlete.get("fullName", ""),
                "status": athlete.get("status", ""),
                "detail": athlete.get("description", "")
            })
    os.makedirs("data/raw", exist_ok=True)
    df = pd.DataFrame(players)
    df.to_csv("data/raw/injuries.csv", index=False)
    print("Injury report saved to data/raw/injuries.csv")

if __name__ == "__main__":
    get_injuries()
