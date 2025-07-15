
import pandas as pd
from prophet import Prophet

def load_data(file):
    df = pd.read_csv(file, encoding="ISO-8859-1")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df.dropna(subset=["InvoiceDate", "StockCode", "Quantity", "UnitPrice"], inplace=True)
    df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df

def forecast_revenue(df, stock_code, country, forecast_months):
    # Lọc dữ liệu
    filtered_df = df[(df["StockCode"] == stock_code) & (df["Country"] == country)]
    if filtered_df.empty:
        return None
    
    monthly = filtered_df.groupby("Month").agg({"Revenue": "sum"}).reset_index()
    monthly.columns = ["ds", "y"]

    # Mô hình Prophet
    model = Prophet()
    model.fit(monthly)

    future = model.make_future_dataframe(periods=forecast_months, freq="MS")
    forecast = model.predict(future)

    # Tính toán và chuẩn bị dữ liệu dự báo
    recent_avg = monthly["y"].tail(3).mean()
    forecast["delta"] = forecast["yhat"] - recent_avg
    forecast["pct_change"] = 100 * forecast["delta"] / recent_avg

    # Tạo dataframe kết quả
    forecast_result_raw = forecast[["ds", "yhat", "delta", "pct_change"]].tail(forecast_months)
    forecast_result = pd.DataFrame({
        "Tháng dự báo": forecast_result_raw["ds"].dt.strftime("%m/%Y"),
        "Doanh thu dự báo": forecast_result_raw["yhat"],
        "Chênh lệch": forecast_result_raw["delta"],
        "So với TB 3T (%)": forecast_result_raw["pct_change"]
    })
    
    return forecast_result, forecast, recent_avg
