import streamlit as st
import pandas as pd
from revenue_forecast_controller import RevenueForecastController
import matplotlib.pyplot as plt

class RevenueForecastView:
    def __init__(self, controller):
        self.controller = controller

    def display(self):
        st.set_page_config(page_title="Dự báo Doanh thu Sản phẩm", layout="wide")
        st.title("🔮 Dự báo Doanh thu Sản phẩm theo Tháng")

        uploaded_file = st.file_uploader("📂 Chọn file CSV dữ liệu", type=["csv"])

        if uploaded_file:
            self.controller.load_data()
            df = self.controller.model.df
            stock_codes = sorted(df["StockCode"].unique())
            countries = sorted(df["Country"].unique())

            # Giao diện nhập tham số
            col1, col2 = st.columns(2)
            stock_code = col1.selectbox("🛒 Chọn sản phẩm", stock_codes)
            country = col2.selectbox("🌎 Chọn quốc gia", countries)
            forecast_months = st.number_input("📆 Số tháng cần dự báo", min_value=1, value=3, step=1)
            threshold = st.number_input("⚠️ Ngưỡng cảnh báo (%)", min_value=0.0, value=10.0, step=1.0)

            if st.button("🚀 Chạy dự báo"):
                forecast, monthly = self.controller.get_forecast(stock_code, country, forecast_months)

                if forecast is None:
                    st.error("❌ Không có dữ liệu phù hợp.")
                else:
                    # Generate forecast result
                    forecast_result = pd.DataFrame({
                        "Tháng dự báo": forecast["ds"].dt.strftime("%m/%Y"),
                        "Doanh thu dự báo": forecast["yhat"],
                        "Chênh lệch": forecast["delta"],
                        "So với TB 3T (%)": forecast["pct_change"]
                    })

                    st.subheader("📊 Kết quả Dự báo")
                    st.dataframe(forecast_result)

                    # Biểu đồ
                    st.subheader("📈 Biểu đồ Dự báo")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(forecast["ds"], forecast["yhat"], label="Dự báo")
                    ax.set_xlabel("Thời gian")
                    ax.set_ylabel("Doanh thu dự báo")
                    ax.set_title("Diễn biến doanh thu dự báo")
                    ax.legend()
                    st.pyplot(fig)
    