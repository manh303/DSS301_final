
import streamlit as st

def display_sidebar():
    st.sidebar.title("Dự báo Doanh thu Sản phẩm")
    stock_code = st.sidebar.selectbox("Chọn sản phẩm", ["Product A", "Product B", "Product C"])
    country = st.sidebar.selectbox("Chọn quốc gia", ["VN", "US", "UK"])
    forecast_months = st.sidebar.slider("Số tháng cần dự báo", 1, 12, 3)
    return stock_code, country, forecast_months
