import pandas as pd

def compute_ev(props_df):
    """
    Compute expected value (EV) for each player prop
    using placeholder probabilities and lines for now.
    """
    df = props_df.copy()

    # Convert American odds to implied probability
    def american_to_prob(odds):
        if odds < 0:
            return -odds / (-odds + 100)
        else:
            return 100 / (odds + 100)

    df["Over_Prob"] = df["OverOdds"].apply(american_to_prob)
    df["Under_Prob"] = df["UnderOdds"].apply(american_to_prob)

    # Placeholder model probability: using 50/50 for now
    df["Model_Prob_Over"] = 0.5

    # Expected value = model probability - implied probability
    df["EV_Over"] = df["Model_Prob_Over"] - df["Over_Prob"]

    # Filter only positive EV props
    df_ev = df[df["EV_Over"] > 0].copy()

    return df_ev
