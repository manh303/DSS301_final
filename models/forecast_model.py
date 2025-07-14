
import pandas as pd
from prophet import Prophet

class ForecastModel:
    def __init__(self, df):
        self.df = df

    def forecast(self, forecast_months):
        # Fit the model
        model = Prophet()
        model.fit(self.df)

        # Make future dataframe
        future = model.make_future_dataframe(periods=forecast_months, freq="MS")
        forecast = model.predict(future)

        # Calculate the delta and percentage change
        recent_avg = self.df['y'].tail(3).mean()
        forecast['delta'] = forecast['yhat'] - recent_avg
        forecast['pct_change'] = 100 * forecast['delta'] / recent_avg

        return forecast
