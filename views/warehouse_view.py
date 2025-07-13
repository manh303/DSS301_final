import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import altair as alt
from io import StringIO

# Inventory optimization logic (Deterministic)
def inventory_optimize(df, time_filter, time_value, stock_code, avg_demand, holding_cost, ordering_cost, lead_time):
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    df['Month'] = df['InvoiceDate'].dt.month
    df['Quarter'] = df['InvoiceDate'].dt.quarter
    df['Year'] = df['InvoiceDate'].dt.year
    df['Revenue'] = df['Quantity'] * df['UnitPrice']

    if time_filter == "Tháng":
        df = df[df['Month'] == time_value]
    elif time_filter == "Quý":
        df = df[df['Quarter'] == time_value]
    elif time_filter == "Năm":
        df = df[df['Year'] == time_value]

    if stock_code:
        df = df[df['Description'] == stock_code]

    summary = df.groupby(['StockCode', 'Description']).agg({
        'Quantity': 'sum',
        'Revenue': 'sum'
    }).reset_index()

    if summary.empty:
        return pd.DataFrame()

    summary['Current_Stock'] = np.random.randint(20, 200, size=len(summary))

    # EOQ Model for optimal stock (Deterministic)
    if avg_demand > 0 and holding_cost > 0:
        eoq = np.sqrt((2 * avg_demand * ordering_cost) / holding_cost)
    else:
        eoq = 100

    summary['Optimal_Stock'] = int(eoq)
    summary['Gap'] = summary['Optimal_Stock'] - summary['Current_Stock']
    summary['Lead_Time'] = lead_time
    summary['Ordering_Cost'] = ordering_cost
    summary['Holding_Cost'] = holding_cost

    return summary

def render_warehouse_analysis(df):
    st.title("📦 Tối ưu tồn kho & Phân tích kho hàng")

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    df['Month'] = df['InvoiceDate'].dt.month
    df['Quarter'] = df['InvoiceDate'].dt.quarter
    df['Year'] = df['InvoiceDate'].dt.year

    unique_months = sorted(df['Month'].dropna().unique())
    unique_quarters = sorted(df['Quarter'].dropna().unique())
    unique_years = sorted(df['Year'].dropna().unique())
    unique_products = df[['StockCode', 'Description']].drop_duplicates().sort_values(by='StockCode')

    with st.expander("📉 Dữ liệu phân tích:", expanded=True):
        st.header("📦 Tối ưu tồn kho & Phân tích kho hàng")
        with st.container():
            st.subheader("⚙️ Cấu hình phân tích")
            selected_product = st.selectbox("Chọn tên sản phẩm", unique_products['Description'].unique())
            time_filter = st.radio("Chọn khoảng thời gian phân tích", ["Tháng", "Quý", "Năm"], horizontal=True)

            if time_filter == "Tháng":
                time_value = st.selectbox("Chọn tháng", list(range(1, 13)))
            elif time_filter == "Quý":
                time_value = st.selectbox("Chọn quý", [1, 2, 3, 4])
            else:
                time_value = st.selectbox("Chọn năm", unique_years)

            st.subheader("🔢 Thông số cho mô hình Deterministic")
            avg_demand = st.number_input("📦 Nhu cầu trung bình (đơn vị/tháng)", min_value=1, value=100)
            holding_cost = st.number_input("💰 Chi phí lưu kho / đơn vị / tháng", min_value=1.0, value=5.0)
            ordering_cost = st.number_input("🛒 Chi phí đặt hàng / lần", min_value=1.0, value=100.0)
            lead_time = st.number_input("⏱️ Thời gian giao hàng (ngày)", min_value=1, value=7)

            run_analysis = st.button("🚀 Phân tích tồn kho")

    if not run_analysis:
        st.info("👉 Vui lòng cấu hình và nhấn 'Phân tích tồn kho' để xem kết quả.")
        return

    top_df = inventory_optimize(df, time_filter, time_value, selected_product, avg_demand, holding_cost, ordering_cost, lead_time)

    if top_df.empty:
        st.warning("Không có dữ liệu phù hợp với bộ lọc được chọn.")
        return

    tab1, tab2 = st.tabs(["📊 Kết quả DSS", "🛠️ Hành động & Gợi ý"])

    with tab1:
        st.subheader("📈 So sánh Tồn kho hiện tại và Khuyến nghị")
        col1, col2 = st.columns(2)

        with col1:
            base = alt.Chart(top_df).encode(y=alt.Y('Description:N', sort='-x'))

            bar_current = base.mark_bar(color='#ff7f0e').encode(
                x='Current_Stock:Q',
                tooltip=['Description', 'Current_Stock']
            )
            bar_optimal = base.mark_bar(color='#1f77b4').encode(
                x='Optimal_Stock:Q',
                tooltip=['Optimal_Stock']
            )
            st.altair_chart(bar_current + bar_optimal, use_container_width=True)

        with col2:
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.heatmap(
                top_df[['Gap']].T,
                annot=True,
                fmt=".0f",
                cmap="coolwarm",
                cbar=True,
                xticklabels=top_df['Description'],
                yticklabels=["Gap tồn kho"],
                ax=ax
            )
            ax.set_title("🔥 Chênh lệch tồn kho theo sản phẩm")
            st.pyplot(fig)

        st.markdown("""
        - **Thanh cam**: lượng tồn kho thực tế  
        - **Thanh xanh**: mức tồn kho tối ưu theo mô hình EOQ  
        - **Biểu đồ nhiệt**: thể hiện chênh lệch tồn kho, đỏ là thiếu – xanh là dư
        """)

        st.subheader("🧾 Bảng phân tích chi tiết")
        st.dataframe(top_df[['StockCode', 'Description', 'Current_Stock', 'Optimal_Stock', 'Gap', 'Lead_Time', 'Ordering_Cost', 'Holding_Cost']], use_container_width=True)

    with tab2:
        st.subheader("🔧 Gợi ý cải thiện tồn kho")
        for _, row in top_df.iterrows():
            product = row['Description']
            gap = row['Gap']
            lead = row['Lead_Time']
            order_cost = row['Ordering_Cost']
            hold_cost = row['Holding_Cost']

            if gap > 10:
                st.warning(f"🚛 **{product}** đang thiếu hàng **({gap} đơn vị)**.\n\n➡️ Hành động: \n- Tăng tần suất đặt hàng\n- Tăng định mức tồn kho\n- Xem xét nhà cung ứng giao hàng nhanh hơn\n➡️ Gợi ý: \n- Thiết lập cảnh báo khi tồn kho dưới ngưỡng\n- Rút ngắn thời gian giao hàng (hiện tại: {lead} ngày)\n- Tích hợp mô hình Reorder Point\n- Tạo lịch nhập hàng định kỳ hoặc tự động hóa chuỗi cung ứng")
            elif gap < -10:
                st.info(f"📦 **{product}** đang tồn kho dư **({-gap} đơn vị)**.\n\n➡️ Hành động: \n- Giảm lượng đặt hàng\n- Kéo giãn chu kỳ nhập hàng\n➡️ Gợi ý: \n- Thực hiện khuyến mãi đẩy hàng\n- Phân loại ABC để ưu tiên\n- Đàm phán giảm chi phí lưu kho (hiện tại: {hold_cost}/đơn vị/tháng)\n- Chuyển hàng sang kho luân chuyển nhanh hoặc giảm giá")
            else:
                st.success(f"✅ **{product}** đang có tồn kho hợp lý.\n\n➡️ Hành động: \n- Duy trì kế hoạch nhập hàng\n➡️ Gợi ý: \n- Theo dõi xu hướng bán hàng để điều chỉnh\n- Xây dựng dashboard cảnh báo tự động\n- Xem xét biến động mùa vụ và tăng trưởng để dự báo nâng cao")

    st.markdown("---")
    st.caption("Dữ liệu phân tích dựa trên tồn kho mô phỏng và doanh thu thực tế theo thời gian. Có thể tích hợp thuật toán nâng cao để tối ưu chi tiết hơn.")
