
import streamlit as st
import matplotlib.pyplot as plt

def show_title():
    st.set_page_config(page_title="Dự báo Doanh thu Sản phẩm", layout="wide")
    st.title("🔮 Dự báo Doanh thu Sản phẩm theo Tháng")

def show_file_uploader():
    return st.file_uploader("📂 Chọn file CSV dữ liệu", type=["csv"])

def show_input_controls(stock_codes, countries, forecast_months, threshold):
    col1, col2 = st.columns(2)
    stock_code = col1.selectbox("🛒 Chọn sản phẩm", stock_codes)
    country = col2.selectbox("🌎 Chọn quốc gia", countries)
    forecast_months = st.number_input("📆 Số tháng cần dự báo", min_value=1, value=forecast_months, step=1)
    threshold = st.number_input("⚠️ Ngưỡng cảnh báo (%)", min_value=0.0, value=float(threshold), step=0.5)
    return stock_code, country, forecast_months, threshold

def show_forecast_result(forecast_result):
    st.subheader("📊 Kết quả Dự báo")
    st.dataframe(
        forecast_result.style.format({
            "Doanh thu dự báo": "{:.2f}",
            "Chênh lệch": "{:.2f}",
            "So với TB 3T (%)": "{:.1f}%" 
        })
    )

def show_chart(forecast):
    st.subheader("📈 Biểu đồ Dự báo")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast["ds"], forecast["yhat"], label="Dự báo")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Doanh thu dự báo")
    ax.set_title("Diễn biến doanh thu dự báo")
    ax.legend()
    st.pyplot(fig)

def show_comments(comment):
    st.info(comment)

def show_suggestions(suggestions):
    st.subheader("🔍 Phân tích & Gợi ý")
    for suggestion in suggestions:
        st.markdown(suggestion)
        st.markdown("💡 Duy trì theo dõi định kỳ và cập nhật mô hình hàng tháng để phản ánh biến động mới.")

def show_warning(msg):
    st.error(msg)
