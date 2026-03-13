"""
📈 TrendPredictor

Simple wrapper for trained ML model.
Loads model once and performs predictions.
"""

import joblib


class TrendPredictor:
    def __init__(self, path="trend_model.pkl"):
        self.model = joblib.load(path)

    def predict(self, df):
        features = df[["open", "high", "low", "close", "volume"]]
        return self.model.predict(features)
