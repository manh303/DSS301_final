import streamlit as st
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt

def render_forecast_analysis(df):
    st.subheader("📈 Dự báo bán hàng")

    df = df.dropna(subset=["InvoiceDate", "Quantity", "Description", "StockCode"])
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Label"] = df["Description"] + " (" + df["StockCode"].astype(str) + ")"

    with st.form("forecast_form"):
        st.markdown("### 🔧 Nhập thông tin phân tích dự báo")
        product = st.selectbox("Chọn sản phẩm", df["Label"].unique())

        col1, col2 = st.columns(2)
        with col1:
            months_to_forecast = st.number_input("Số tháng cần dự báo", min_value=1, max_value=12, value=6)
        with col2:
            threshold_quantity = st.number_input("Ngưỡng số lượng bán cần chuẩn bị", min_value=1, value=100)

        submitted = st.form_submit_button("📊 Thực hiện dự báo")

    if submitted:
        product_df = df[df["Label"] == product]
        product_df = product_df.groupby(pd.Grouper(key="InvoiceDate", freq="M"))["Quantity"].sum().reset_index()

        if len(product_df) < 3:
            st.error("❌ Không đủ dữ liệu để dự báo. Cần ít nhất 3 tháng.")
            return

        # Hiển thị bảng dữ liệu
        with st.expander("📄 Dữ liệu đầu vào"):
            st.dataframe(product_df)

        # Chọn mô hình phù hợp
        if len(product_df) >= 24:
            model = ExponentialSmoothing(product_df["Quantity"], seasonal="add", seasonal_periods=12).fit()
        else:
            model = ExponentialSmoothing(product_df["Quantity"], trend="add").fit()

        forecast = model.forecast(months_to_forecast)

        # Vẽ biểu đồ
        st.markdown("### 📊 Biểu đồ dự báo")
        fig, ax = plt.subplots()
        ax.plot(product_df["InvoiceDate"], product_df["Quantity"], label="Thực tế")
        ax.plot(pd.date_range(product_df["InvoiceDate"].max() + pd.DateOffset(months=1), periods=months_to_forecast, freq="M"), forecast, label="Dự báo", linestyle="--")
        ax.set_xlabel("Thời gian")
        ax.set_ylabel("Số lượng bán")
        ax.legend()
        st.pyplot(fig)

        # Tabs DSS và Gợi ý hành động
        tab1, tab2 = st.tabs(["📊 Kết quả DSS", "💡 Gợi ý hành động"])
        with tab1:
            st.info(f"Trong {months_to_forecast} tháng tới, tổng doanh số dự báo là `{forecast.sum():.0f}` sản phẩm.")
        with tab2:
            if forecast.mean() > threshold_quantity:
                st.success("✅ Dự báo bán vượt mức kỳ vọng. Nên chuẩn bị thêm hàng tồn kho.")
            else:
                st.warning("📉 Doanh số dự báo thấp hơn mức kỳ vọng. Cần chiến dịch kích cầu.")

    else:
        st.info("📥 Vui lòng nhập thông tin và bấm nút để thực hiện dự báo.")
