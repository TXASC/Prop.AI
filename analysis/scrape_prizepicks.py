import requests
import pandas as pd
import time

def fetch_prizepicks_props():
    # PrizePicks public API endpoint for projections
    url = "https://api.prizepicks.com/projections"
    params = {
        "league_id": 7,  # NBA
        "per_page": 250,
        "state": "open"
    }
    for _ in range(3):
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Status code: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)
    return None

def parse_prizepicks_nba_points_props(data):
    # Extract NBA points props for today
    props = []
    if not data or "data" not in data:
        return props
    included = {item["id"]: item for item in data.get("included", []) if item.get("type") == "new_player"}
    for proj in data["data"]:
        attributes = proj.get("attributes", {})
        stat_type = attributes.get("stat_type")
        if stat_type != "Points":
            continue
        player_id = str(attributes.get("new_player_id"))
        player = included.get(player_id, {}).get("attributes", {}).get("name")
        line_val = attributes.get("line_score")
        game_time = attributes.get("start_time")
        if player and line_val is not None:
            props.append({
                "PLAYER_NAME": player,
                "PROP_LINE": line_val,
                "GAME_TIME": game_time
            })
    return props

def save_prizepicks_points_props():
    data = fetch_prizepicks_props()
    props = parse_prizepicks_nba_points_props(data)
    if not props:
        print("No NBA points props found on PrizePicks.")
        return
    df = pd.DataFrame(props)
    df.to_csv("output/prizepicks_nba_points_props.csv", index=False)
    print(f"Saved {len(df)} NBA points props to output/prizepicks_nba_points_props.csv")

if __name__ == "__main__":
    save_prizepicks_points_props()
