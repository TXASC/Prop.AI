import pandas as pd
import os

def find_ev(odds_prob_path, proj_prob_path, output_path):
    """
    Merges odds-based and projection-based probabilities, calculates expected value (EV) for each prop.
    Expects:
      - odds_prob_path: CSV with Player, Stat, Line, Over_Odds, Under_Odds, Over_Prob_Odds, Under_Prob_Odds
      - proj_prob_path: CSV with Player, Stat, Line, Projection, Over_Prob, Under_Prob
    Outputs:
      - CSV with Player, Stat, Line, Over_Odds, Under_Odds, Over_Prob_Odds, Under_Prob_Odds, Projection, Over_Prob, Under_Prob, Over_EV, Under_EV
    """
    if not os.path.exists(odds_prob_path) or not os.path.exists(proj_prob_path):
        print(f"Missing input files: {odds_prob_path} or {proj_prob_path}")
        return
    odds_df = pd.read_csv(odds_prob_path)
    proj_df = pd.read_csv(proj_prob_path)
    # Merge on Player, Stat, Line
    merged = pd.merge(odds_df, proj_df, on=["Player", "Stat", "Line"], how="inner")
    # Calculate EV: (probability_win * payout) - (probability_lose * 1)
    # For American odds, payout = abs(odds)/100 if odds > 0 else 100/abs(odds)
    def payout(odds):
        if odds > 0:
            return odds / 100
        else:
            return 100 / abs(odds)
    merged['Over_Payout'] = merged['Over_Odds'].apply(payout)
    merged['Under_Payout'] = merged['Under_Odds'].apply(payout)
    merged['Over_EV'] = merged['Over_Prob'] * merged['Over_Payout'] - (1 - merged['Over_Prob'])
    merged['Under_EV'] = merged['Under_Prob'] * merged['Under_Payout'] - (1 - merged['Under_Prob'])
    merged.to_csv(output_path, index=False)
    print(f"EV results saved to {output_path}")

if __name__ == "__main__":
    odds_prob_csv = "data/processed/nba_odds_probabilities.csv"
    proj_prob_csv = "data/processed/nba_projection_probabilities.csv"
    output_csv = "data/processed/nba_ev_results.csv"
    find_ev(odds_prob_csv, proj_prob_csv, output_csv)
