import pandas as pd
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY"))

def analyze_context():
    props_path = "output/positive_ev_props.csv"
    injuries_path = "data/raw/injuries.csv"
    fatigue_path = "data/processed/fatigue_flags.csv"
    if not (os.path.exists(props_path) and os.path.exists(injuries_path) and os.path.exists(fatigue_path)):
        print("Missing one or more required files for context analysis.")
        return
    props = pd.read_csv(props_path)
    injuries = pd.read_csv(injuries_path)
    fatigue = pd.read_csv(fatigue_path)
    reports = []
    for _, row in props.iterrows():
        player_name = row.get("PLAYER_NAME", "")
        injury_notes = injuries[injuries["player"].str.contains(player_name, case=False, na=False)]
        fatigue_flag = fatigue[fatigue["PLAYER_NAME"].str.contains(player_name, case=False, na=False)]["fatigue_flag"].values
        fatigue_note = "Fatigue risk" if len(fatigue_flag) > 0 and fatigue_flag[0] == 1 else "No major fatigue risk"
        prompt = f"""
You are an NBA betting analyst.\n\nEvaluate this prop bet:\n\nPlayer: {player_name}\nBet Line: {row.get('Line', '')}\nModel Edge: {row.get('edge', '')}\n\nKnown Injury News:\n{injury_notes.to_string(index=False)}\n\nFatigue: {fatigue_note}\n\nTasks:\n- Determine if minutes risk exists\n- Consider teammate injuries\n- Consider fatigue risk\n- Determine blowout risk potential\n\nReturn:\nConfidence Score (1-10)\nand a 2-3 sentence explanation.\n"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        reports.append(response.choices[0].message.content)
    props["AI_Context_Report"] = reports
    os.makedirs("output", exist_ok=True)
    props.to_json("output/final_picks.json", orient="records", indent=2)
    print("Context AI analysis complete. Results saved to output/final_picks.json")

if __name__ == "__main__":
    analyze_context()
