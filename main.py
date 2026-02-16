
import os

PYTHON = r"d:/prop_ai_app/.venv/Scripts/python.exe"

def run_step(script, desc):
	print(f"\n=== Running: {desc} ===")
	code = os.system(f"{PYTHON} {script}")
	if code != 0:
		print(f"Step failed: {script}")
	else:
		print(f"Step complete: {desc}")

pipeline = [
	("collectors/get_nba_stats.py", "Collect NBA player stats"),
	("processors/clean_stats.py", "Clean stats"),
	("analysis/projections.py", "Generate projections"),
	("collectors/get_odds.py", "Collect odds/props"),
	("processors/odds_to_probability.py", "Convert odds to probability"),
	("processors/projection_to_probability.py", "Convert projections to probability"),
	("analysis/find_ev.py", "Find expected value (EV)"),
	("analysis/find_value.py", "Find value props"),
	("analysis/ai_analysis.py", "AI analysis"),
	("collectors/get_injuries.py", "Get NBA injury report"),
	("analysis/schedule_analysis.py", "Analyze schedule/fatigue flags"),
	("analysis/context_ai_agent.py", "Context AI agent for final picks"),
]

for script, desc in pipeline:
	run_step(script, desc)

print("\nFull NBA prop analysis pipeline complete.")
