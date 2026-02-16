def calculate_implied_scores(game):
    """
    Compute implied team scores from Vegas lines (spreads/totals).
    Args:
        game: dict with 'bookmakers' containing spreads and totals
    Returns:
        dict: home_implied_score, away_implied_score
    """
    total = None
    spread = None
    # Find best available total and spread from bookmakers
    for bookmaker in game.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'totals' and market['outcomes']:
                total = market['outcomes'][0].get('point')
            if market['key'] == 'spreads' and market['outcomes']:
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        spread = outcome.get('point')
    if total is None or spread is None:
        return {'home_implied_score': None, 'away_implied_score': None}
    # Implied scores
    home_implied = (total + spread) / 2
    away_implied = (total - spread) / 2
    return {
        'home_implied_score': round(home_implied, 2),
        'away_implied_score': round(away_implied, 2)
    }
