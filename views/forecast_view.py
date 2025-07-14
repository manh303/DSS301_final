
import streamlit as st
import matplotlib.pyplot as plt

def display_sidebar():
    st.sidebar.title("Dự báo Doanh thu Sản phẩm")
    stock_code = st.sidebar.selectbox("Chọn sản phẩm", ["Product A", "Product B", "Product C"])
    country = st.sidebar.selectbox("Chọn quốc gia", ["VN", "US", "UK"])
    forecast_months = st.sidebar.slider("Số tháng cần dự báo", 1, 12, 3)
    return stock_code, country, forecast_months

def display_results(forecast_result):
    st.subheader("📊 Kết quả Dự báo")
    st.dataframe(forecast_result)

    # Display the forecast chart
    st.subheader("📈 Biểu đồ Dự báo")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast_result['ds'], forecast_result['yhat'], label="Dự báo")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Doanh thu dự báo")
    ax.set_title("Diễn biến doanh thu dự báo")
    ax.legend()
    st.pyplot(fig)

def display_suggestions(suggestions):
    st.subheader("🔍 Phân tích & Gợi ý")
    for suggestion in suggestions:
        st.markdown(suggestion)
