"""
Parlay Suggester

Generates high-probability multi-leg parlay suggestions for NBA pick'em platforms
using CLV, bet ingestion, and prop correlations.

Functions:
    generate_suggested_parlays(platform=None, max_legs=5, min_correlation=0.2, min_clv=0)
"""

import logging
import json
import itertools
from datetime import datetime
import pandas as pd
from database.clv_tracking import get_clv_db_connection, insert_suggested_parlay

LOG_PATH = "logs/parlay_suggester.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def joint_probability(probs, correlations):
    """
    Approximate joint probability for a set of props using pairwise correlations.
    Uses a simplified Gaussian copula approach for positive correlations.
    """
    if not probs:
        return 0
    p = 1.0
    for prob in probs:
        p *= prob
    # Adjust for positive correlations (boost joint probability)
    if correlations:
        avg_corr = sum(correlations) / len(correlations)
        p *= (1 + avg_corr)
    return min(max(p, 0), 1)

def generate_suggested_parlays(platform=None, max_legs=5, min_correlation=0.2, min_clv=0):
    """
    Generate and store suggested parlays based on CLV and prop correlations.
    Args:
        platform (str): Optional platform filter.
        max_legs (int): Maximum legs per parlay.
        min_correlation (float): Minimum pairwise correlation for legs.
        min_clv (float): Minimum CLV for props.
    """
    try:
        conn = get_clv_db_connection()
        # Load latest pickem bets and CLV
        df_bets = pd.read_sql_query("SELECT * FROM pickem_bets", conn)
        df_corr = pd.read_sql_query("SELECT * FROM prop_correlations", conn)
        # Filter by platform if needed
        if platform:
            df_bets = df_bets[df_bets['platform'].str.lower() == platform.lower()]
        # Filter props by CLV
        df_bets = df_bets[df_bets['projected_lines'].notnull()]
        # Parse projected_lines and filter by min_clv
        prop_candidates = []
        for _, row in df_bets.iterrows():
            try:
                lines = json.loads(row['projected_lines'])
                for prop in lines:
                    clv = lines[prop].get('clv', 0)
                    if clv >= min_clv:
                        prop_candidates.append({
                            'player_id': lines[prop].get('player_id'),
                            'stat': lines[prop].get('stat'),
                            'line': lines[prop].get('line'),
                            'projection': lines[prop].get('projection'),
                            'clv': clv,
                            'platform': row['platform'],
                            'entry_id': row['entry_id']
                        })
            except Exception:
                continue
        # Build candidate combos
        combos = list(itertools.combinations(prop_candidates, max_legs))
        suggestions = []
        for combo in combos:
            # Compute pairwise correlations
            corrs = []
            probs = []
            for i, leg1 in enumerate(combo):
                # Assume hit probability from CLV (e.g., p = 0.5 + clv/2)
                probs.append(min(max(0.5 + leg1['clv'] / 2, 0), 1))
                for j, leg2 in enumerate(combo):
                    if i >= j:
                        continue
                    mask = (
                        (df_corr['player1_id'] == str(leg1['player_id'])) &
                        (df_corr['player2_id'] == str(leg2['player_id'])) &
                        (df_corr['stat1'] == leg1['stat']) &
                        (df_corr['stat2'] == leg2['stat'])
                    )
                    corr = df_corr[mask]['correlation_coefficient']
                    if not corr.empty and corr.iloc[0] >= min_correlation:
                        corrs.append(corr.iloc[0])
            if len(corrs) < (max_legs * (max_legs - 1)) // 2:
                continue  # skip if not enough positive correlations
            joint_prob = joint_probability(probs, corrs)
            projected_payout = 10 * (3 ** max_legs)  # Placeholder: replace with real payout logic
            suggestions.append({
                'legs': combo,
                'joint_prob': joint_prob,
                'projected_payout': projected_payout,
                'score': joint_prob * projected_payout,
                'notes': f'Avg corr: {sum(corrs)/len(corrs):.2f}' if corrs else ''
            })
        # Rank and insert top N
        suggestions = sorted(suggestions, key=lambda x: -x['score'])[:10]
        for s in suggestions:
            legs_json = json.dumps([{
                'player_id': leg['player_id'],
                'stat': leg['stat'],
                'line': leg['line'],
                'projection': leg['projection'],
                'clv': leg['clv']
            } for leg in s['legs']])
            insert_suggested_parlay(
                platform or 'all',
                datetime.utcnow().isoformat(),
                legs_json,
                s['joint_prob'],
                s['projected_payout'],
                s['notes'],
                'pending'
            )
            logging.info(f"Suggested parlay: {legs_json} | prob={s['joint_prob']:.3f} | payout={s['projected_payout']} | {s['notes']}")
    except Exception as e:
        logging.error(f"Parlay suggestion failed: {e}")
