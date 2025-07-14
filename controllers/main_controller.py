import streamlit as st
import pandas as pd
import os
from models.rfm_model import RFMModel
from views.ui import UIView

class MainController:
    """Controller class for application flow control"""
    
    def __init__(self):
        """Initialize controller with model and view"""
        self.model = RFMModel()
        self.view = UIView()
        self.default_data_path = "data/online_retail.csv"

    def run(self):
        """
        Run the main application and handle navigation
        """
        # Hiển thị màn hình cấu hình và nhận cấu hình
        k, ref_date, country, revenue_target = self.view.config_page()
        
        # Nút phân tích dữ liệu
        analyze_button = st.button("🔍 Phân tích dữ liệu", type="primary")
        
        if analyze_button:
            self.analyze_data(k, ref_date, country, revenue_target)
    
    def analyze_data(self, k, ref_date, country, revenue_target):
        """
        Phân tích dữ liệu và hiển thị kết quả
        """
        st.markdown("---")
        st.subheader("📈 Kết quả phân tích")
        
        with st.spinner("Đang xử lý dữ liệu..."):
            # Kiểm tra nếu file mặc định tồn tại
            if os.path.exists(self.default_data_path):
                try:
                    # Đọc và xử lý dữ liệu với bộ lọc ngày tham chiếu
                    df, latest_date = self.model.load_data_from_path(self.default_data_path, country, ref_date)
                    
                    # Kiểm tra dữ liệu
                    if df.empty:
                        st.error("❌ Dữ liệu giao dịch rỗng. Vui lòng kiểm tra lại file CSV.")
                        return
                        
                    # Calculate RFM and perform clustering
                    rfm = self.model.calculate_rfm(df, ref_date)
                    
                    # Kiểm tra kết quả RFM
                    if rfm.empty:
                        st.error("❌ Không thể tính toán RFM từ dữ liệu. Vui lòng kiểm tra lại file CSV.")
                        return
                    
                    clustered = self.model.cluster_rfm(rfm.copy(), k)
                    
                    # Kiểm tra kết quả phân cụm
                    if clustered.empty:
                        st.error("❌ Không thể phân cụm khách hàng. Vui lòng kiểm tra lại dữ liệu.")
                        return
                    
                    summary = self.model.cluster_summary(clustered)
                    
                    # Calculate monthly revenue for each cluster
                    monthly_revenue = self.model.calculate_monthly_revenue(df, clustered)
                    
                    # Pass revenue_target, latest_date and monthly_revenue to the view
                    self.view.analysis_page(clustered, summary, revenue_target, latest_date, monthly_revenue)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi khi xử lý dữ liệu: {str(e)}")
            else:
                st.error(f"❌ Không tìm thấy file dữ liệu tại {self.default_data_path}")