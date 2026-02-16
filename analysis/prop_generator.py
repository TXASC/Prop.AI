import logging
import pandas as pd
import os

def generate_props_from_projections(projections):
    props = []
    for p in projections:
        # Points: round to nearest 0.5
        pts_line = round(p['projected_points'] * 2) / 2
        rebs_line = round(p['projected_rebounds'])
        asts_line = round(p['projected_assists'])
        props.append({
            'PLAYER_NAME': p['player_name'],
            'TEAM_ABBREVIATION': p['team'],
            'StatType': 'PTS',
            'Line': pts_line,
            'OverOdds': -110,
            'UnderOdds': -110
        })
        props.append({
            'PLAYER_NAME': p['player_name'],
            'TEAM_ABBREVIATION': p['team'],
            'StatType': 'REB',
            'Line': rebs_line,
            'OverOdds': -110,
            'UnderOdds': -110
        })
        props.append({
            'PLAYER_NAME': p['player_name'],
            'TEAM_ABBREVIATION': p['team'],
            'StatType': 'AST',
            'Line': asts_line,
            'OverOdds': -110,
            'UnderOdds': -110
        })
    os.makedirs('data/raw', exist_ok=True)
    df = pd.DataFrame(props)
    df.to_csv('data/raw/today_props.csv', index=False)
    logging.info(f"Saved {len(df)} props to data/raw/today_props.csv")
    return df
