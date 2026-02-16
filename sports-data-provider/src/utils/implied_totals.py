def calculate_implied_scores(betting_spread, total_points):
    """
    Calculate the implied scores for home and away teams based on the betting spread and total points.

    Parameters:
    betting_spread (float): The betting spread for the game.
    total_points (float): The total points set for the game.

    Returns:
    tuple: A tuple containing the implied scores for the home and away teams.
    """
    home_score = (total_points + betting_spread) / 2
    away_score = (total_points - betting_spread) / 2
    return home_score, away_score