# Sports Data Provider

This project is designed to fetch and analyze sports data, specifically focusing on NBA games and player statistics. It integrates data from TheOddsAPI for game schedules and betting markets, and BallDontLie for player stats.

## Project Structure

```
sports-data-provider
├── src
│   ├── providers
│   │   ├── ball_dont_lie.py        # Provider for fetching player stats
│   │   ├── the_odds_api.py         # Provider for fetching game schedules and betting markets
│   ├── pipeline
│   │   ├── daily_pipeline.py        # Daily pipeline for processing data
│   ├── utils
│   │   ├── implied_totals.py        # Utility for calculating implied scores
│   └── types
│       └── index.py                 # Type definitions
├── requirements.txt                 # Project dependencies
└── README.md                        # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd sports-data-provider
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage Guidelines

- **Fetching Game Schedules and Betting Markets:**
  Use the `fetch_nba_games_and_markets` function from `the_odds_api.py` to retrieve NBA game schedules and associated betting markets.

- **Fetching Player Stats:**
  Use the functions in `ball_dont_lie.py` to get player game logs, team rosters, and recent games.

- **Daily Data Processing:**
  Run the `daily_pipeline.py` to execute the daily data fetching and processing workflow, which includes logging, fetching games, calculating implied scores, and generating betting insights.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.