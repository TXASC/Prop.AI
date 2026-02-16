import requests
import pandas as pd
import time

def fetch_underdog_props():
    # Underdog NBA props endpoint (public, but may change)
    url = "https://api.underdogfantasy.com/beta/v3/over_under_lines"
    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Status code: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)
    return None

def parse_underdog_nba_points_props(data):
    # Extract NBA points props for tonight
    props = []
    if not data or "over_under_lines" not in data:
        return props
    import datetime
    tomorrow = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).date()
    for line in data["over_under_lines"]:
        if not line.get("over_under"):
            continue
        ou = line["over_under"]
        if ou.get("stat_type") != "points":
            continue
        player = ou.get("user", {}).get("full_name")
        line_val = line.get("line")
        team = ou.get("team_nickname")
        game_time = ou.get("game", {}).get("starts_at")
        # Only include props for tomorrow's games
        if game_time:
            try:
                game_date = datetime.datetime.fromisoformat(game_time.replace('Z', '+00:00')).date()
            except Exception:
                continue
            if game_date != tomorrow:
                continue
        if player and line_val is not None:
            props.append({
                "PLAYER_NAME": player,
                "TEAM": team,
                "PROP_LINE": line_val,
                "GAME_TIME": game_time
            })
    return props

def save_underdog_points_props():
    data = fetch_underdog_props()
    props = parse_underdog_nba_points_props(data)
    if not props:
        print("No NBA points props found on Underdog.")
        return
    df = pd.DataFrame(props)
    df.to_csv("output/underdog_nba_points_props.csv", index=False)
    print(f"Saved {len(df)} NBA points props to output/underdog_nba_points_props.csv")

if __name__ == "__main__":
    save_underdog_points_props()
