import os
from db_manager import initialize_database

if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    initialize_database()
    print("Database schema initialized.")
