import pandas as pd
import numpy as np
from scipy import stats

class RevenueCausalImpactModel:
    def __init__(self, data):
        self.df = data

    def process_data(self):
        self.df["InvoiceDate"] = pd.to_datetime(self.df["InvoiceDate"], errors="coerce")
        self.df.dropna(subset=["InvoiceDate", "StockCode", "Quantity", "UnitPrice"], inplace=True)
        self.df["Month"] = self.df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
        self.df["Revenue"] = self.df["Quantity"] * self.df["UnitPrice"]

    def causal_impact(self, stock_code, country, event_date, pre_period_months=6, post_period_months=3):
        filtered_df = self.df[(self.df["StockCode"] == stock_code) & (self.df["Country"] == country)]
        if filtered_df.empty:
            return None
        # Tổng doanh thu theo tháng
        monthly = filtered_df.groupby("Month").agg({"Revenue": "sum", "UnitPrice": "mean", "Quantity": "sum"}).reset_index()
        monthly = monthly.sort_values("Month")
        monthly.set_index("Month", inplace=True)
        # Xác định mốc sự kiện
        if event_date not in monthly.index:
            return None
        event_idx = monthly.index.get_loc(event_date)
        # Đảm bảo có ít nhất 3 điểm dữ liệu trong pre_period
        pre_start = max(0, event_idx - pre_period_months)
        if event_idx - pre_start < 3:
            pre_start = max(0, event_idx - 3)
        post_end = min(len(monthly)-1, event_idx + post_period_months)
        # Kiểm tra lại số lượng điểm dữ liệu
        pre_period_points = event_idx - pre_start
        if pre_period_points < 3:
            print(f"Không đủ dữ liệu: chỉ có {pre_period_points} điểm trong pre_period")
            return None
        # Tạo dữ liệu pre và post
        pre_data = monthly.iloc[pre_start:event_idx]["Revenue"].values
        post_data = monthly.iloc[event_idx:post_end+1]["Revenue"].values
        # Thực hiện t-test để so sánh
        t_stat, p_value = stats.ttest_ind(pre_data, post_data)
        # Tính toán tác động
        pre_mean = np.mean(pre_data)
        post_mean = np.mean(post_data)
        impact = post_mean - pre_mean
        impact_pct = (impact / pre_mean) * 100 if pre_mean != 0 else 0
        # Tạo kết quả mô phỏng CausalImpact
        result = {
            "pre_data": pre_data,
            "post_data": post_data,
            "impact": impact,
            "impact_pct": impact_pct,
            "p_value": p_value,
            "t_stat": t_stat,
            "pre_mean": pre_mean,
            "post_mean": post_mean,
            "is_significant": p_value < 0.05
        }
        return result, monthly.reset_index()
    