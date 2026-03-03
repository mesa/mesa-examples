import joblib


class TrendPredictor:
    """
    Wrapper for trained ML trend model.
    """

    def __init__(self, path="trend_model.pkl"):
        self.model = joblib.load(path)

    def predict(self, df):
        features = df[["open", "high", "low", "close", "volume"]]
        return self.model.predict(features)