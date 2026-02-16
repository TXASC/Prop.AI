
import pandas as pd
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

def american_to_probability(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def convert():
    import os
    input_path = os.path.join(RAW_DATA_DIR, "nba_props.csv")
    output_path = os.path.join(PROCESSED_DATA_DIR, "props_with_prob.csv")
    df = pd.read_csv(input_path)
    df["over_prob"] = df["OverOdds"].apply(american_to_probability)
    df["under_prob"] = df["UnderOdds"].apply(american_to_probability)
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    convert()
