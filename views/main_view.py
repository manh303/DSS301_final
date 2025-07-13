import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from models.data_model import (
    get_cached_data,
    prepare_rfm_data,
    product_monthly_sales,
    price_quantity_impact_data
)

def inventory_optimization_view():
    st.subheader("📦 Tối ưu hóa kho hàng")
    df = get_cached_data()
    stock_summary = df.groupby("StockCode").agg({
        "Quantity": "sum",
        "Revenue": "sum"
    }).sort_values("Revenue", ascending=False).reset_index()

    top_n = st.slider("Chọn số sản phẩm doanh thu cao nhất", 5, 50, 10)
    top_products = stock_summary.head(top_n)
    st.dataframe(top_products)

    st.markdown("### Biểu đồ doanh thu theo mã sản phẩm")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="StockCode", y="Revenue", data=top_products, ax=ax)
    plt.xticks(rotation=90)
    st.pyplot(fig)


def cluster_revenue_forecast_view():
    st.subheader("👥 Dự báo doanh thu theo nhóm khách hàng")
    df = get_cached_data()
    rfm = prepare_rfm_data(df)

    st.markdown("### Bảng điểm RFM")
    st.dataframe(rfm.head())

    st.markdown("### Phân bố điểm RFM_Score")
    fig, ax = plt.subplots()
    sns.histplot(rfm["RFM_Score"], bins=15, kde=True, ax=ax)
    st.pyplot(fig)

    st.markdown("### Biểu đồ phân tán R vs M")
    fig2, ax2 = plt.subplots()
    sns.scatterplot(
        x="Recency",
        y="Monetary",
        hue="RFM_Score",
        data=rfm,
        palette="viridis",
        ax=ax2
    )
    st.pyplot(fig2)


def product_monthly_forecast_view():
    st.subheader("📅 Doanh thu sản phẩm theo tháng")
    df = get_cached_data()
    monthly_sales = product_monthly_sales(df)

    product = st.selectbox("Chọn sản phẩm", monthly_sales["Product"].unique())
    product_df = monthly_sales[monthly_sales["Product"] == product]

    st.markdown(f"### Doanh thu theo tháng: {product}")
    st.line_chart(product_df.set_index("YearMonth")["Revenue"])

    st.markdown("### Biểu đồ cột")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="YearMonth", y="Revenue", data=product_df, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)


def price_quantity_impact_view():
    st.subheader("📈 Phân tích ảnh hưởng UnitPrice/Quantity đến Revenue")
    df = get_cached_data()
    data = price_quantity_impact_data(df)

    x_axis = st.selectbox("Chọn biến độc lập", ["UnitPrice", "Quantity"])

    st.markdown(f"### Phân tán {x_axis} vs Revenue")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.scatterplot(x=x_axis, y="Revenue", data=data, alpha=0.5, ax=ax)
    st.pyplot(fig)

    st.markdown(f"### Tương quan Pearson: {x_axis} vs Revenue")
    correlation = data[[x_axis, "Revenue"]].corr().iloc[0, 1]
    st.write(f"Hệ số tương quan: {correlation:.2f}")
