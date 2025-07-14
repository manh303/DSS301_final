
import streamlit as st
import pandas as pd
from models.forecast_model import ForecastModel
from views.forecast_view import display_sidebar, display_results, display_suggestions

def load_data(uploaded_file):
    # Đọc dữ liệu CSV
    df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df.dropna(subset=["InvoiceDate", "StockCode", "Quantity", "UnitPrice"], inplace=True)
    df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df

def generate_suggestions(forecast_result):
    suggestions = []
    for _, row in forecast_result.iterrows():
        month_label = row["Tháng dự báo"]
        pct = row["So với TB 3T (%)"]
        action = ""
        trend = ""
        detail = ""

        # Dựa trên % thay đổi, đưa ra hành động và gợi ý chi tiết
        if pct >= 10:
            trend = "📈 Tăng rất mạnh"
            action = "Mở rộng sản xuất và tăng cường cung cấp sản phẩm.
Đẩy mạnh các chiến dịch quảng bá và bán hàng."
            detail = "Tăng cường quảng bá sản phẩm và mở rộng chiến dịch marketing.
Xem xét hợp tác với các KOL/KOC để mở rộng thị trường."
        elif 5 <= pct < 10:
            trend = "🟢 Tăng mạnh"
            action = "Tiếp tục duy trì chiến lược marketing hiện tại.
Xem xét mở rộng sản xuất và tăng cường cung cấp sản phẩm."
            detail = "Tiếp tục duy trì các chiến lược marketing đang hoạt động hiệu quả.
Khám phá các thị trường mới và đầu tư vào cải tiến sản phẩm."
        elif 0 <= pct < 5:
            trend = "➖ Tăng nhẹ"
            action = "Duy trì chiến lược marketing hiện tại.
Tăng cường quảng bá sản phẩm và khuyến mãi."
            detail = "Xem xét các kênh quảng cáo hiệu quả hơn (ví dụ: TikTok, Facebook, Instagram).
Tăng cường hợp tác với các KOL/KOC."
        elif -5 < pct < 0:
            trend = "🔵 Giảm nhẹ"
            action = "Cải thiện chiến lược marketing để duy trì ổn định.
Xem xét các chiến lược khuyến mãi."
            detail = "Điều chỉnh mức giá sản phẩm để cải thiện lợi nhuận.
Tập trung vào nâng cao trải nghiệm khách hàng."
        elif -10 < pct <= -5:
            trend = "📉 Giảm mạnh"
            action = "Cần thay đổi chiến lược marketing hoàn toàn để thu hút khách hàng mới.
Tăng cường các chương trình khuyến mãi mạnh mẽ."
            detail = "Tổ chức các sự kiện bán hàng đặc biệt hoặc flash sale.
Tăng cường chiến dịch quảng cáo trực tuyến và giảm giá mạnh."
        else:
            trend = "🚨 Giảm rất mạnh"
            action = "Điều chỉnh ngay lập tức chiến lược marketing.
Giảm giá mạnh và thanh lý hàng tồn kho."
            detail = "Cân nhắc giảm giá 10–20% hoặc thanh lý hàng tồn kho.
Tổ chức chiến dịch quảng cáo mạnh mẽ hơn và tăng ngân sách truyền thông."

        suggestions.append(f"**{month_label}** - Xu hướng: {trend}
- Đề xuất: {action}
- Gợi ý chi tiết: {detail}
")

    return suggestions

def main():
    st.title("🔮 Dự báo Doanh thu Sản phẩm theo Tháng")

    uploaded_file = st.file_uploader("📂 Chọn file CSV dữ liệu", type=["csv"])

    if uploaded_file:
        df = load_data(uploaded_file)
        stock_code, country, forecast_months = display_sidebar()

        # Lọc dữ liệu
        filtered_df = df[(df["StockCode"] == stock_code) & (df["Country"] == country)]
        if filtered_df.empty:
            st.error("❌ Không có dữ liệu phù hợp.")
        else:
            monthly = filtered_df.groupby("Month").agg({"Revenue": "sum"}).reset_index()
            monthly.columns = ["ds", "y"]

            # Dự báo với mô hình Prophet
            model = ForecastModel(monthly)
            forecast = model.forecast(forecast_months)

            # Tạo bảng kết quả dự báo
            forecast_result = pd.DataFrame({
                "Tháng dự báo": forecast["ds"].dt.strftime("%m/%Y"),
                "Doanh thu dự báo": forecast["yhat"],
                "Chênh lệch": forecast["delta"],
                "So với TB 3T (%)": forecast["pct_change"]
            })

            # Hiển thị kết quả dự báo
            display_results(forecast_result)

            # Tạo và hiển thị gợi ý hành động
            suggestions = generate_suggestions(forecast_result)
            display_suggestions(suggestions)

if __name__ == "__main__":
    main()
