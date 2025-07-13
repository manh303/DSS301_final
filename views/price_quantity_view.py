import streamlit as st
import pandas as pd


def render_price_quantity_analysis(df):
    st.subheader("💰 Phân tích Giá và Số lượng")

    df = df.dropna(subset=["UnitPrice", "Quantity", "Description", "StockCode"])
    df["Label"] = df["Description"].astype(str) + " (" + df["StockCode"].astype(str) + ")"

    with st.form("price_form"):
        st.markdown("### Thiết lập thông tin phân tích")
        product = st.selectbox("Chọn sản phẩm", df["Label"].unique())
        submitted = st.form_submit_button("📊 Phân tích & Hành động")

    if submitted:
        product_df = df[df["Label"] == product]

        if product_df.empty:
            st.error("Không tìm thấy dữ liệu cho sản phẩm đã chọn.")
            return

        product_df = product_df.groupby("UnitPrice")["Quantity"].sum().reset_index()

        st.markdown("### 🔍 Phân tích mối quan hệ Giá và Số lượng")
        st.dataframe(product_df)
        st.line_chart(product_df.set_index("UnitPrice"))

        tab1, tab2 = st.tabs(["📊 Kết quả DSS", "💡 Gợi ý hành động"])
        with tab1:
            st.markdown("#### Dữ liệu cho thấy mối quan hệ giữa giá và số lượng bán")
        with tab2:
            if product_df["Quantity"].iloc[-1] < product_df["Quantity"].iloc[0]:
                st.warning("⚠️ Khi tăng giá thì số lượng giảm → nên xem xét chiến lược giá hợp lý hơn.")
            else:
                st.success("✅ Sản phẩm có thể duy trì hoặc tăng giá mà không ảnh hưởng lớn đến doanh số.")
