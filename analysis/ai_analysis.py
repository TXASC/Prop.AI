
import pandas as pd
from openai import OpenAI
import os
import sys

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("[WARN] OPENAI_API_KEY not set in environment. AI analysis will not run.", file=sys.stderr)
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

def analyze():
    if not client:
        print("[ERROR] Cannot run AI analysis: OPENAI_API_KEY not set.", file=sys.stderr)
        return
    df = pd.read_csv("output/value_plays.csv")
    reports = []
    for _, row in df.iterrows():
        prompt = f"""
        Analyze this NBA prop bet:

        Player: {row['PLAYER_NAME']}
        Minutes: {row['MIN']}
        Projected PRA: {row['projected_PRA']}

        Consider:
        - fatigue
        - usage
        - matchup risk
        - variance

        Return: Good Bet / Risky / Avoid and explanation
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        reports.append(response.choices[0].message.content)
    df['AI_analysis'] = reports
    df.to_json("output/daily_picks.json", orient="records", indent=2)

if __name__ == "__main__":
    analyze()
