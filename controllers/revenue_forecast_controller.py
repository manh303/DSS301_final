from models.revenue_forecast_model import RevenueForecastModel
import pandas as pd

class RevenueForecastController:
    def __init__(self, df):
        self.df = df
        self.model = RevenueForecastModel(df)
        self.model.process_data()

    def load_data(self, file):
        df = pd.read_csv(file, encoding="ISO-8859-1")
        self.model = RevenueForecastModel(df)
        self.model.process_data()

    def get_forecast(self, stock_code, country, forecast_months):
        if self.model:
            return self.model.forecast(stock_code, country, forecast_months)
        else:
            return None, None
