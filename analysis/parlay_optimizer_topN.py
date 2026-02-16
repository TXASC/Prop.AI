import pandas as pd
import itertools

def top_n_3_pick_parlays(ai_props_df, n=3):
    """
    Generates the top N 3-pick parlays from AI-adjusted props.
    Constraints:
      - Exactly 3 picks per parlay
      - At least 2 different teams
      - Maximize combined adjusted_EV
      - Use confidence for tie-breaking

    Inputs:
        ai_props_df: DataFrame with columns including:
            - PLAYER_NAME
            - TEAM_ABBREVIATION
            - adjusted_EV
            - confidence
            - AI_Context_Report
        n: number of top parlays to return

    Outputs:
        List of DataFrames (each DataFrame is a 3-pick parlay)
    """
    df = ai_props_df.copy()

    if len(df) < 3:
        print("Not enough props available for a 3-pick parlay")
        return []

    parlays = []

    # Generate all combinations of 3 props
    for combo_indices in itertools.combinations(df.index, 3):
        subset = df.loc[list(combo_indices)]

        # Enforce at least 2 different teams
        if len(subset["TEAM_ABBREVIATION"].unique()) < 2:
            continue

        # Combined score = sum(adjusted_EV * confidence weight)
        score = sum(subset["adjusted_EV"] * (subset["confidence"]/10))

        # Store the parlay and its score
        parlays.append((score, subset))

    # Sort parlays by score descending
    parlays.sort(key=lambda x: (x[0], sum(x[1]["confidence"])), reverse=True)

    # Take top N
    top_parlays = [p[1].reset_index(drop=True) for p in parlays[:n]]

    if not top_parlays:
        print("No valid parlays could be generated today.")
    return top_parlays
