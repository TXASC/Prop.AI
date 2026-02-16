
import pandas as pd
import os
from config import PROCESSED_DATA_DIR

def projection_to_probability(input_path, output_path):
    """
    Converts model projections to implied probabilities using a normal distribution assumption.
    Expects input CSV with columns: Player, Stat, Projection, Line
    Outputs CSV with columns: Player, Stat, Projection, Line, Over_Prob, Under_Prob
    """
    from scipy.stats import norm
    if not os.path.exists(input_path):
        print(f"Input file {input_path} not found.")
        return
    df = pd.read_csv(input_path)
    # Assume a standard deviation for projection error (can be tuned)
    STD_DEV = 3.0
    over_probs = []
    under_probs = []
    for _, row in df.iterrows():
        proj = row['Projection']
        line = row['Line']
        # Probability the stat exceeds the line
        over_prob = 1 - norm.cdf(line, loc=proj, scale=STD_DEV)
        under_prob = norm.cdf(line, loc=proj, scale=STD_DEV)
        over_probs.append(over_prob)
        under_probs.append(under_prob)
    df['Over_Prob'] = over_probs
    df['Under_Prob'] = under_probs
    df.to_csv(output_path, index=False)
    print(f"Projection probabilities saved to {output_path}")

if __name__ == "__main__":
    # Example usage
    import os
    input_csv = os.path.join(PROCESSED_DATA_DIR, "nba_projections.csv")
    output_csv = os.path.join(PROCESSED_DATA_DIR, "nba_projection_probabilities.csv")
    projection_to_probability(input_csv, output_csv)
