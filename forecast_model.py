
import pandas as pd
from prophet import Prophet

class ForecastModel:
    def __init__(self, df):
        self.df = df

    def forecast(self, forecast_months):
        model = Prophet()
        model.fit(self.df)
        future = model.make_future_dataframe(periods=forecast_months, freq="MS")
        forecast = model.predict(future)
        forecast['delta'] = forecast['yhat'] - self.df['y'].tail(3).mean()
        forecast['pct_change'] = 100 * forecast['delta'] / self.df['y'].tail(3).mean()
        return forecast
