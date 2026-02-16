import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib

def train_model():
    df = pd.read_csv("data/processed/clean_player_stats.csv")

    X = df[['MIN']]
    y = df['PRA']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = XGBRegressor(n_estimators=200, max_depth=4)
    model.fit(X_train, y_train)

    joblib.dump(model, "models/projection_model.pkl")

if __name__ == "__main__":
    train_model()
