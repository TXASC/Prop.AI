import pandas as pd
import itertools

def best_3_pick_parlay(ai_props_df):
    """
    Selects the optimal 3-pick parlay from AI-adjusted props.
    Constraints:
      - Exactly 3 picks
      - At least 2 different teams
      - Maximize combined adjusted_EV
      - Use confidence to break ties

    Input:
        ai_props_df: DataFrame with columns including:
            - PLAYER_NAME
            - TEAM_ABBREVIATION
            - adjusted_EV
            - confidence
            - AI_Context_Report
    Output:
        DataFrame with the selected 3 picks
    """
    df = ai_props_df.copy()

    if len(df) < 3:
        print("Not enough props available for a 3-pick parlay")
        return pd.DataFrame()

    best_combo = None
    best_score = float('-inf')

    # Generate all combinations of 3 props
    for combo_indices in itertools.combinations(df.index, 3):
        subset = df.loc[list(combo_indices)]

        # Ensure at least 2 different teams
        if len(subset["TEAM_ABBREVIATION"].unique()) < 2:
            continue

        # Combined score: sum of adjusted_EV, weighted by confidence
        score = sum(subset["adjusted_EV"] * (subset["confidence"]/10))

        # Break ties with sum of confidence
        tie_breaker = sum(subset["confidence"])

        if score > best_score:
            best_score = score
            best_combo = subset
        elif score == best_score and tie_breaker > sum(best_combo["confidence"]):
            best_combo = subset

    if best_combo is not None:
        return best_combo.reset_index(drop=True)
    else:
        print("No valid 3-pick parlay found with at least 2 teams.")
        return pd.DataFrame()
