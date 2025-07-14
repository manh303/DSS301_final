
import streamlit as st
import pandas as pd
from models.forecast_model import ForecastModel
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dự báo Doanh thu Sản phẩm", layout="wide")
st.title("🔮 Dự báo Doanh thu Sản phẩm theo Tháng")

def forecast_data(df, stock_code, country, forecast_months):
    filtered_df = df[(df["StockCode"] == stock_code) & (df["Country"] == country)]
    if filtered_df.empty:
        return None, "❌ Không có dữ liệu phù hợp."
    else:
        monthly = filtered_df.groupby("Month").agg({"Revenue": "sum"}).reset_index()
        monthly.columns = ["ds", "y"]

        # Forecast using model
        model = ForecastModel(monthly)
        forecast = model.forecast(forecast_months)

        return forecast, None

def display_results(forecast):
    st.subheader("📊 Kết quả Dự báo")
    st.dataframe(forecast)
    st.subheader("📈 Biểu đồ Dự báo")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast['ds'], forecast['yhat'], label="Dự báo")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Doanh thu dự báo")
    ax.set_title("Diễn biến doanh thu dự báo")
    ax.legend()
    st.pyplot(fig)

def generate_suggestions(forecast):
    # Generating suggestions based on forecast results
    suggestions = []
    for _, row in forecast.iterrows():
        month_label = row["Tháng dự báo"]
        pct = row["So với TB 3T (%)"]
        action = ""
        if pct >= 10:
            action = "Mở rộng sản xuất và tăng cường cung cấp sản phẩm."
        # More actions for different cases...
        suggestions.append(f"**{month_label}** - Xu hướng: {action}")

    return suggestions
