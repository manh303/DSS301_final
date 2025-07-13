import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from controllers.revenue_forecast_controller import RevenueForecastController

class RevenueForecastView:
    def __init__(self, controller):
        self.controller = controller

    def display(self):
        st.title("🔮 Dự báo Doanh thu Sản phẩm theo Tháng")

        uploaded_file = st.file_uploader("📂 Chọn file CSV dữ liệu", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")

            # Chuẩn hóa cột ngày
            if "Date" not in df.columns:
                if "InvoiceDate" in df.columns:
                    df.rename(columns={"InvoiceDate": "Date"}, inplace=True)
                    st.info("✅ Đã đổi tên cột 'InvoiceDate' thành 'Date'")
                else:
                    st.error("❌ Thiếu cột 'Date' hoặc 'InvoiceDate'")
                    return

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])

            # Kiểm tra và tính Revenue nếu cần
            if "Revenue" not in df.columns:
                if "Quantity" in df.columns and "UnitPrice" in df.columns:
                    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
                    st.info("✅ Đã tự động tính cột Revenue")
                else:
                    st.error("❌ Thiếu cột Revenue hoặc Quantity + UnitPrice")
                    return

            if "StockCode" not in df.columns or "Country" not in df.columns:
                st.error("❌ Thiếu cột StockCode hoặc Country")
                return

            stock_codes = sorted(df["StockCode"].dropna().unique())
            countries = sorted(df["Country"].dropna().unique())

            if not stock_codes or not countries:
                st.error("❌ Không có đủ dữ liệu hợp lệ để phân tích.")
                return

            col1, col2 = st.columns(2)
            stock_code = col1.selectbox("🎢 Chọn sản phẩm", stock_codes)
            country = col2.selectbox("🌎 Chọn quốc gia", countries)
            forecast_months = st.number_input("📆 Số tháng cần dự báo", min_value=1, value=3, step=1)
            threshold = st.number_input("⚠️ Ngưỡng cảnh báo (%)", min_value=0.0, value=10.0, step=1.0)

            # Khởi tạo controller từ dataframe
            self.controller = RevenueForecastController(df)

            if st.button("🚀 Chạy dự báo"):
                forecast, monthly = self.controller.get_forecast(stock_code, country, forecast_months)

                if forecast is None:
                    st.error("❌ Không có dữ liệu phù hợp.")
                else:
                    forecast_result = pd.DataFrame({
                        "Tháng dự báo": forecast["ds"].dt.strftime("%m/%Y"),
                        "Doanh thu dự báo": forecast["yhat"],
                        "Chênh lệch": forecast["delta"],
                        "So với TB 3T (%)": forecast["pct_change"]
                    })

                    st.subheader("📊 Kết quả Dự báo")
                    st.dataframe(forecast_result)

                    st.subheader("📈 Biểu đồ Dự báo")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(forecast["ds"], forecast["yhat"], marker='o', label="Dự báo")
                    ax.set_xlabel("Thời gian")
                    ax.set_ylabel("Doanh thu dự báo")
                    ax.set_title("Diễn biến doanh thu dự báo")
                    ax.legend()
                    st.pyplot(fig)

def render_product_forecast_analysis(df):
    view = RevenueForecastView(None)
    view.display()
