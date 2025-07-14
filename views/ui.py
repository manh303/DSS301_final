import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import datetime
import os

class UIView:
    """View class for UI handling"""
    
    def config_page(self):
        """
        Display the configuration page without file upload
        
        Returns:
        --------
        tuple: (k, ref_date, country_filter, revenue_target)
            - k: Number of clusters
            - ref_date: Reference date
            - country_filter: Country filter
            - revenue_target: Revenue target for analysis
        """
        st.title("📊 Hệ thống phân cụm khách hàng RFM")
        
        st.markdown("### ⚙️ Cấu hình phân tích")
        
        max_date = datetime.date.today()
        default_date = max_date
        country_filter = "Tất cả"
        
        # Lấy thông tin từ file dữ liệu
        try:
            if os.path.exists("data/online_retail.csv"):
                df_temp = pd.read_csv("data/online_retail.csv", encoding='ISO-8859-1')
                
                # Lấy ngày mới nhất từ dữ liệu
                if 'InvoiceDate' in df_temp.columns:
                    df_temp['InvoiceDate'] = pd.to_datetime(df_temp['InvoiceDate'], errors='coerce')
                    latest_date = df_temp['InvoiceDate'].max()
                    
                    if not pd.isna(latest_date):
                        max_date = latest_date.date()
                        default_date = max_date
                
                # Lấy danh sách quốc gia
                if 'Country' in df_temp.columns:
                    countries = sorted(df_temp['Country'].unique().tolist())
                    country_options = ["Tất cả"] + countries
                    country_filter = st.selectbox("🌎 Chọn quốc gia", country_options)
            else:
                st.error("Không tìm thấy file dữ liệu tại data/online_retail.csv")
        except Exception as e:
            st.error(f"❌ Lỗi khi đọc file: {str(e)}")
        
        # Số lượng cụm
        k = st.selectbox("🔢 Số lượng cụm khách hàng (k)", [2, 3, 4, 5], index=1)
        
        # Ngày tham chiếu
        ref_date = st.date_input(
            "📅 Ngày tham chiếu",
            value=default_date,
            max_value=max_date
        )
        st.caption(f"Ngày tham chiếu dùng để tính Recency - tối đa là ngày {max_date}")
        
        # Mục tiêu doanh thu
        st.markdown("#### 💰 Mục tiêu doanh thu")
        revenue_target = st.number_input(
            "Nhập mục tiêu doanh thu (đơn vị tiền tệ)",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=10000,
            format="%d"
        )
        st.caption("Mục tiêu doanh thu sẽ được sử dụng để so sánh và phân tích xu hướng")
        
        return k, ref_date, country_filter, revenue_target
        
    def analysis_page(self, df_rfm, summary_df, revenue_target, latest_date, monthly_revenue):
        """
        Display the analysis page with cluster insights and action plans
        
        Parameters:
        -----------
        df_rfm : DataFrame
            RFM data with cluster assignments
        summary_df : DataFrame
            Summary information for each cluster
        revenue_target : int
            Revenue target for analysis and forecasting
        latest_date : datetime
            The latest date in the dataset for forecast reference
        monthly_revenue : dict
            Dictionary containing monthly revenue data for each cluster
        """
        # Phân loại cụm theo số lượng cụm đã chọn
        try:
            # Lấy danh sách các cụm
            cluster_ids = sorted(df_rfm['Cluster'].unique())
            
            # Lấy số lượng cụm
            k = len(cluster_ids)
            
            # Sắp xếp cụm theo giá trị trung bình Monetary để xác định thứ tự (thấp đến cao)
            monetary_values = {}
            for cluster_id in cluster_ids:
                monetary_values[cluster_id] = summary_df.loc[cluster_id, 'Monetary_mean']
            
            # Sắp xếp cluster_ids theo giá trị monetary (thấp đến cao)
            sorted_clusters = sorted(cluster_ids, key=lambda c: monetary_values[c])
            
            # Đặt tên theo số lượng cụm đã chọn
            cluster_types = {}
            
            if k == 2:
                # Nếu k = 2
                names = ["Low Value Customers", "High Value Customers"]
                icons = ["⬇️", "💎"]
                
            elif k == 3:
                # Nếu k = 3
                names = ["Low Value Customers", "Medium Value Customers", "High Value Customers"]
                icons = ["⬇️", "➡️", "💎"]
                
            elif k == 4:
                # Nếu k = 4
                names = ["Low Value Customers", "Medium Value Customers", 
                         "High Value Customers", "Very High Value Customers"]
                icons = ["⬇️", "➡️", "💎", "👑"]
                
            else:  # k = 5
                # Nếu k = 5
                names = ["Low Value Customers", "Medium Low Value Customers", "Medium Value Customers",
                         "High Value Customers", "Very High Value Customers"]
                icons = ["⬇️", "↘️", "➡️", "💎", "👑"]
            
            # Gán tên cho các cụm theo thứ tự giá trị tăng dần
            for i, cluster_id in enumerate(sorted_clusters):
                cluster_types[cluster_id] = {
                    "name": names[i], 
                    "emoji": icons[i]
                }
                
        except Exception as e:
            # Nếu có lỗi, sử dụng phân loại dự phòng đơn giản
            cluster_types = {}
            for i in cluster_ids:
                cluster_types[i] = {"name": f"Cụm {i}", "emoji": "📊"}
        
        # Tạo tên tab cho từng cụm
        tab_names = [f"{cluster_types[i]['emoji']} {cluster_types[i]['name']}" for i in cluster_ids]
        
        # Hiển thị tổng quan về phân cụm
        st.subheader("📊 Thông tin phân cụm khách hàng")
        
        # Hiển thị số lượng khách hàng trong từng cụm
        cluster_counts = df_rfm['Cluster'].value_counts().sort_index()
        total_customers = len(df_rfm)
        
        # Tạo dataframe hiển thị thông tin tổng quan về cụm
        overview_data = {
            "Cụm": [f"{cluster_types[i]['emoji']} {cluster_types[i]['name']}" for i in cluster_ids],
            "Số lượng khách hàng": [cluster_counts.get(i, 0) for i in cluster_ids],
            "Tỉ lệ (%)": [f"{cluster_counts.get(i, 0) / total_customers * 100:.1f}%" for i in cluster_ids],
        }
        st.dataframe(pd.DataFrame(overview_data))
        
        # Tạo các tab cho từng cụm
        tabs = st.tabs(tab_names)
        
        # Điền nội dung cho từng tab
        for idx, cluster_id in enumerate(cluster_ids):
            with tabs[idx]:
                self.show_cluster_tab(cluster_id, df_rfm, summary_df, revenue_target, latest_date, monthly_revenue)
        
    def show_cluster_tab(self, cluster_id, df_rfm, summary_df, revenue_target, latest_date, monthly_revenue):
        """
        Display content for each cluster tab
        
        Parameters:
        -----------
        cluster_id : int
            Cluster ID
        df_rfm : DataFrame
            RFM data with cluster assignments
        summary_df : DataFrame
            Summary information for each cluster
        revenue_target : int
            Revenue target for analysis and forecasting
        latest_date : datetime
            The latest date in the dataset for forecast reference
        monthly_revenue : dict
            Dictionary containing monthly revenue data for each cluster
        """
        # Get cluster data
        cluster_df = df_rfm[df_rfm['Cluster'] == cluster_id].copy()
        cluster_summary = summary_df.loc[cluster_id]
        
        # Chia layout thành 2 cột chính: Thông tin khách hàng (trái) và Biểu đồ doanh thu (phải)
        col_left, col_right = st.columns([1, 1])
        
        # Cột trái: Tổng quan và danh sách khách hàng
        with col_left:
            
            # Hiển thị phần tổng quan trong container
            self.show_cluster_overview(cluster_id, cluster_summary)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Danh sách khách hàng
            self.show_customer_list(cluster_df)
            
        # Cột phải: Biểu đồ doanh thu
        with col_right:
            self.show_forecast_chart(revenue_target, latest_date, cluster_id, monthly_revenue)
            
            # Hiển thị giải thích biểu đồ trực tiếp
            st.markdown("""
            <div style="background-color:#f9f9f9; border-radius:8px; padding:15px; margin-top:15px; border-left:4px solid #3498db; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display:flex; align-items:center; margin-bottom:10px;">
                    <div style="background-color:#3498db; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:14px;">
                        🔍
                    </div>
                    <h4 style="margin:0; color:#333; font-size:16px; font-weight:600;">Giải thích biểu đồ</h4>
                </div>
                <ul style="list-style-type:none; padding-left:38px; margin-bottom:0;">
                    <li style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="width:12px; height:12px; background-color:#3498db; border-radius:50%; margin-right:10px;"></div>
                        <span>Đường màu xanh: Doanh thu thực tế của cụm</span>
                    </li>
                    <li style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="width:12px; height:12px; background-color:#f39c12; border-radius:50%; margin-right:10px;"></div>
                        <span>Đường màu cam: Dự báo doanh thu 3 tháng tiếp theo</span>
                    </li>
                    <li style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="width:12px; height:2px; background-color:#e74c3c; margin-right:10px;"></div>
                        <span>Đường màu đỏ đứt nét: Mục tiêu doanh thu</span>
                    </li>
                    <li style="display:flex; align-items:flex-start; margin-bottom:0;">
                        <div style="width:12px; height:12px; background-color:#f8f9fa; border:1px solid #ddd; border-radius:50%; margin-right:10px; margin-top:3px;"></div>
                        <span>Biểu đồ thể hiện xu hướng doanh thu từ dữ liệu thực tế và dự báo 3 tháng sau ngày {}</span>
                    </li>
                </ul>
            </div>
            """.format(latest_date.strftime('%d/%m/%Y') if latest_date else "cuối cùng"), unsafe_allow_html=True)
        
        # 3. Analysis and action plan
        self.show_analysis_and_action_plan(cluster_id, cluster_summary, cluster_df, revenue_target)
    
    def show_cluster_overview(self, cluster_id, cluster_summary):
        """
        Display overview information for a cluster
        
        Parameters:
        -----------
        cluster_id : int
            Cluster ID
        cluster_summary : Series
            Summary information for the cluster
        """
        try:
            # Lấy thông tin phân loại cụm từ session state
            if 'cluster_types' in st.session_state and cluster_id in st.session_state.cluster_types:
                cluster_type = st.session_state.cluster_types[cluster_id]
                cluster_name = cluster_type["name"]
                emoji = cluster_type["emoji"]
            else:
                # Fallback nếu không có trong session state
                cluster_name = f"Cụm {cluster_id}"
                emoji = "📊"
            
            # Hiển thị tiêu đề với tên cụm
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:15px; background-color:#f8f9fa; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <div style="background-color:#4e8cff; color:white; border-radius:50%; width:36px; height:36px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:18px;">
                    {emoji}
                </div>
                <h3 style="margin:0; color:#2c3e50; font-weight:600;">Tổng quan cụm {cluster_name}</h3>
            </div>
            <hr style="margin-top:0; margin-bottom:15px; border-color:#eaeaea;">
            """, unsafe_allow_html=True)
            
            # Lấy các giá trị RFM
            recency_mean = float(cluster_summary.get('Recency_mean', 0))
            frequency_mean = float(cluster_summary.get('Frequency_mean', 0))
            monetary_mean = float(cluster_summary.get('Monetary_mean', 0))
            
            # Hàng đầu: chỉ số RFM chính
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Trung bình ngày từ lần mua cuối</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #3498db;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>{recency_mean:.1f} ngày</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Trung bình số lần mua</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #2ecc71;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>{frequency_mean:.1f} lần</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Trung bình giá trị mua</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #9b59b6;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>${monetary_mean:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Đường ngăn cách
            st.markdown("<hr style='margin:15px 0; border-top:1px dashed #ddd;'>", unsafe_allow_html=True)
                
            # Hàng thứ hai: chỉ số kinh doanh
            col1, col2, col3 = st.columns(3)
            
            with col1:
                customer_count = int(cluster_summary.get('Monetary_count', 0))
                customer_ratio = float(cluster_summary.get('customer_ratio', 0)) * 100
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Số lượng khách hàng</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #e74c3c;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>{customer_count}</div>
                    <div style='color:#27ae60; font-size:0.85em; font-weight:500;'>{customer_ratio:.1f}% tổng số</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                total_revenue = float(cluster_summary.get('total_revenue', 0))
                revenue_ratio = float(cluster_summary.get('revenue_ratio', 0)) * 100
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Tổng doanh thu</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #f39c12;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>${total_revenue:.2f}</div>
                    <div style='color:#27ae60; font-size:0.85em; font-weight:500;'>{revenue_ratio:.1f}% tổng số</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                clv = float(cluster_summary.get('clv', 0))
                st.markdown("<div style='text-align:center; font-size:0.9em; color:#555; font-weight:500;'>Giá trị vòng đời khách hàng</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align:center; background-color:#f0f4f8; padding:10px; border-radius:5px; margin-top:5px; border-left:3px solid #1abc9c;'>
                    <div style='font-size:1.6em; font-weight:bold; color:#2c3e50;'>${clv:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Lỗi: {str(e)}")
            st.info("Đang gặp sự cố khi xử lý dữ liệu cụm. Vui lòng kiểm tra lại dữ liệu.")
    
    def show_customer_list(self, cluster_df):
        """
        Display list of customers in the cluster
        
        Parameters:
        -----------
        cluster_df : DataFrame
            RFM data for customers in this cluster
        """
        # Tạo tiêu đề và khung viền với width vừa với nội dung
        st.markdown("""
        <div style="margin-top:20px; border:1px solid #ddd; border-radius:8px; padding:15px; background-color:#f8f9fa; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width:100%;">
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <div style="background-color:#e67e22; color:white; border-radius:50%; width:36px; height:36px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:18px;">
                    📋
                </div>
                <h3 style="margin:0; color:#2c3e50; font-weight:600;">Danh sách khách hàng</h3>
            </div>
            <hr style="margin-top:0; margin-bottom:15px; border-color:#eaeaea;">
        """, unsafe_allow_html=True)
        
        try:
            # Sort customers by Monetary value (descending)
            sorted_customers = cluster_df.sort_values(by='Monetary', ascending=False)
            
            # Prepare data for display - lấy tất cả khách hàng
            customer_table = sorted_customers[['CustomerID', 'Recency', 'Frequency', 'Monetary']].copy()
            
            # Format columns
            customer_table['CustomerID'] = customer_table['CustomerID'].astype(int)
            customer_table['Recency'] = customer_table['Recency'].round(0).astype(int)
            customer_table['Frequency'] = customer_table['Frequency'].round(1)
            customer_table['Monetary'] = customer_table['Monetary'].round(2)
            
            # Rename columns for better display
            customer_table.columns = ['ID Khách hàng', 'Ngày từ lần mua cuối', 'Số lần mua', 'Tổng chi tiêu ($)']
            
            # Hiển thị tổng số khách hàng
            st.markdown(f"""
            <div style="background-color:#e8f4f8; padding:12px 15px; border-radius:6px; margin-bottom:15px; display:flex; align-items:center; border-left:4px solid #3498db; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="background-color:#3498db; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:14px;">
                    📊
                </div>
                <span style="font-weight:500; font-size:15px;">Tổng số khách hàng trong cụm này: <b>{len(customer_table)}</b></span>
            </div>
            """, unsafe_allow_html=True)
            
            # Display table with pagination
            st.dataframe(
                customer_table, 
                hide_index=True, 
                use_container_width=True,
                height=min(350, 35 + len(customer_table) * 35)  # Adjust height based on number of rows
            )
        
        except Exception as e:
            st.error(f"Lỗi khi hiển thị danh sách khách hàng: {str(e)}")
            st.info("Không thể hiển thị danh sách khách hàng. Vui lòng kiểm tra lại dữ liệu.")
        
        # Đóng div của khung viền
        st.markdown("</div>", unsafe_allow_html=True)
    
    def show_forecast_chart(self, revenue_target, latest_date, cluster_id, monthly_revenue):
        """
        Display forecast chart for a specific cluster
        
        Parameters:
        -----------
        revenue_target : int
            Revenue target for comparison
        latest_date : datetime
            The latest date in the dataset for forecast reference
        cluster_id : int
            Cluster ID to display chart for
        monthly_revenue : dict
            Dictionary containing monthly revenue data for each cluster
        """
        # Tạo tiêu đề với khung viền vừa với nội dung
        st.markdown("""
        <div style="border:1px solid #ddd; border-radius:8px; padding:15px; background-color:#f8f9fa; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <div style="background-color:#3498db; color:white; border-radius:50%; width:36px; height:36px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:18px;">
                    📈
                </div>
                <h3 style="margin:0; color:#2c3e50; font-weight:600;">Biểu đồ doanh thu theo tháng</h3>
            </div>
            <hr style="margin-top:0; margin-bottom:15px; border-color:#eaeaea;">
        """, unsafe_allow_html=True)
        
        # Get cluster data from monthly_revenue
        cluster_data = monthly_revenue.get(cluster_id, None)
        
        if cluster_data is None or not cluster_data['months']:
            st.warning(f"Không có dữ liệu doanh thu cho Cụm {cluster_id}")
            return
            
        # Get months and revenue from cluster data
        months = cluster_data['months']
        actual_values = np.array(cluster_data['revenue'], dtype=np.float64)
        
        # Generate forecast values - slight upward trend from the last actual value
        last_value = actual_values[-1] if len(actual_values) > 0 else 0
        
        # Create forecast for 3 months after the last month
        forecast_values = []
        for i in range(3):
            # Progressive increase with some randomness
            forecast_value = last_value * (1.0 + 0.05 * (i+1)) * (0.9 + 0.2 * np.random.random())
            forecast_values.append(forecast_value)
        
        # Add forecast months to the months list
        if latest_date is not None:
            # Generate forecast period (3 months after latest_date)
            forecast_end = latest_date + pd.DateOffset(months=3)
            forecast_period = pd.date_range(start=latest_date + pd.DateOffset(days=1), 
                                           end=forecast_end, freq='MS')
            
            # Add forecast months to the list
            forecast_months = [d.strftime("%b %Y") for d in forecast_period]
            all_months = months + forecast_months
        else:
            # If no latest_date, just add generic labels
            forecast_months = ["Next 1", "Next 2", "Next 3"]
            all_months = months + forecast_months
        
        # Create arrays for plotting
        all_months_count = len(all_months)
        
        # Create figure with improved styling
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Set background color and grid style
        ax.set_facecolor('#f9f9f9')
        ax.grid(True, linestyle='--', alpha=0.7, color='#dddddd')
        
        # Plot actual values with improved styling
        ax.plot(np.arange(len(months)), actual_values, marker='o', linewidth=2.5, 
                color='#3498db', label='Doanh thu thực tế', markersize=6)
        
        # Plot prediction values with improved styling
        forecast_start_idx = len(months) - 1
        forecast_x = np.arange(forecast_start_idx, forecast_start_idx + len(forecast_values) + 1)
        forecast_y = np.concatenate(([actual_values[-1]], forecast_values))
        
        ax.plot(forecast_x, forecast_y, marker='o', linewidth=2.5, 
                color='#f39c12', linestyle='--', label='Dự báo', markersize=6)
        
        # Plot target value line with improved styling
        revenue_target_float = float(revenue_target)
        ax.axhline(y=revenue_target_float, color='#e74c3c', linestyle='--', 
                   alpha=0.8, linewidth=2, label=f'Mục tiêu: ${int(revenue_target_float)}')
        
        # Set labels and title with improved styling
        ax.set_xticks(np.arange(all_months_count))
        ax.set_xticklabels(all_months, rotation=45, fontsize=9)
        
        # Add title with reference to data period
        title = "Xu hướng doanh thu"
        if latest_date is not None:
            title += f" (Dữ liệu đến {latest_date.strftime('%d-%m-%Y')})"
            
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.set_xlabel('Tháng', fontsize=11, labelpad=10)
        ax.set_ylabel('Doanh thu', fontsize=11, labelpad=10)
        
        # Add legend with improved styling
        legend = ax.legend(loc='upper left', frameon=True, framealpha=0.95, 
                          fontsize=10, facecolor='white', edgecolor='#dddddd')
        
        # Adjust layout
        fig.tight_layout()
        
        # Display chart
        st.pyplot(fig)
        
        # Add summary metrics below the chart with improved styling
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_value = float(np.mean(actual_values))
            diff_pct = ((avg_value - revenue_target_float) / revenue_target_float) * 100 if revenue_target_float > 0 else 0
            st.markdown("""
            <div style="background-color:#f0f4f8; padding:10px; border-radius:5px; text-align:center;">
                <div style="font-size:0.9em; color:#555; font-weight:500;">Doanh thu trung bình</div>
            """, unsafe_allow_html=True)
            st.metric("", f"${int(avg_value)}", f"{diff_pct:.1f}%", 
                     delta_color="normal" if diff_pct >= 0 else "inverse")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            months_above_target = int(np.sum(actual_values > revenue_target_float))
            target_ratio = (months_above_target/len(actual_values))*100 if len(actual_values) > 0 else 0
            st.markdown("""
            <div style="background-color:#f0f4f8; padding:10px; border-radius:5px; text-align:center;">
                <div style="font-size:0.9em; color:#555; font-weight:500;">Tháng vượt mục tiêu</div>
            """, unsafe_allow_html=True)
            st.metric("", f"{months_above_target}/{len(actual_values)}", 
                     f"{target_ratio:.0f}%" if len(actual_values) > 0 else "0%")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            last_month_value = float(actual_values[-1]) if len(actual_values) > 0 else 0
            last_month_vs_target = ((last_month_value - revenue_target_float) / revenue_target_float) * 100 if revenue_target_float > 0 else 0
            st.markdown("""
            <div style="background-color:#f0f4f8; padding:10px; border-radius:5px; text-align:center;">
                <div style="font-size:0.9em; color:#555; font-weight:500;">Tháng gần nhất</div>
            """, unsafe_allow_html=True)
            st.metric("", f"${int(last_month_value)}", f"{last_month_vs_target:.1f}%",
                     delta_color="normal" if last_month_vs_target >= 0 else "inverse")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Đóng div khung viền
        st.markdown("</div>", unsafe_allow_html=True)
    
    def show_analysis_and_action_plan(self, cluster_id, cluster_summary, cluster_df, revenue_target):
        """
        Display analysis and action plan for a cluster
        
        Parameters:
        -----------
        cluster_id : int
            Cluster ID
        cluster_summary : Series
            Summary information for the cluster
        cluster_df : DataFrame
            RFM data for customers in this cluster
        revenue_target : int
            Revenue target for analysis
        """
        st.markdown("""
        <div style="border:1px solid #ddd; border-radius:8px; padding:15px; background-color:#f8f9fa; margin-top:20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <div style="background-color:#9b59b6; color:white; border-radius:50%; width:36px; height:36px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:18px;">
                    🔍
                </div>
                <h3 style="margin:0; color:#2c3e50; font-weight:600;">Phân tích & Đề xuất hành động</h3>
            </div>
            <hr style="margin-top:0; margin-bottom:15px; border-color:#eaeaea;">
        """, unsafe_allow_html=True)
        
        try:
            # Get key metrics
            recency_mean = float(cluster_summary.get('Recency_mean', 0))
            frequency_mean = float(cluster_summary.get('Frequency_mean', 0))
            monetary_mean = float(cluster_summary.get('Monetary_mean', 0))
            customer_count = int(cluster_summary.get('Monetary_count', 0))
            revenue_ratio = float(cluster_summary.get('revenue_ratio', 0)) * 100
            total_revenue = float(cluster_summary.get('total_revenue', 0))
            
            # Determine customer segment type from session state
            if 'cluster_types' in st.session_state and cluster_id in st.session_state.cluster_types:
                cluster_type = st.session_state.cluster_types[cluster_id]
                # Trích xuất tên Tiếng Việt từ định dạng "English → Vietnamese"
                segment_name_full = cluster_type["name"]
                if "→" in segment_name_full:
                    segment_type = segment_name_full.split("→")[1].strip()
                else:
                    segment_type = segment_name_full
                emoji = cluster_type["emoji"]
            else:
                # Fallback nếu không tìm thấy thông tin
                segment_type = f"Cụm {cluster_id}"
                emoji = "📊"
            
            # Phần 1: Lịch sử doanh thu và so sánh
            col1, col2 = st.columns(2)
            
            with col1:
                # Tính toán doanh thu trung bình hàng tháng
                avg_monthly_revenue = total_revenue / 3  # Giả định dữ liệu là 3 tháng
                target_gap = revenue_target - avg_monthly_revenue
                target_gap_pct = (target_gap / avg_monthly_revenue) * 100 if avg_monthly_revenue > 0 else 0
                
                st.markdown("""
                <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #4e8cff; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="background-color:#4e8cff; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:14px;">
                            💹
                        </div>
                        <h4 style="margin:0; color:#333; font-size:16px; font-weight:600;">Phân tích doanh thu</h4>
                    </div>
                    <p style="margin-bottom:5px; padding-left:38px;">Doanh thu trung bình hàng tháng: <b>${:.2f}</b></p>
                    <p style="margin-bottom:0; padding-left:38px;">Mục tiêu doanh thu: <b>${:.0f}</b> <span style="color:{};"> ({:+.1f}%)</span></p>
                </div>
                """.format(
                    avg_monthly_revenue, 
                    float(revenue_target),
                    "#d9534f" if target_gap > 0 else "#5cb85c",
                    target_gap_pct
                ), unsafe_allow_html=True)
                
                # Hiển thị CLV
                clv = float(cluster_summary.get('clv', 0))
                potential_revenue = clv * customer_count * 1.2  # Giả định tăng 20% CLV
                
                st.markdown("""
                <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #5cb85c; margin-top:15px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="background-color:#5cb85c; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:14px;">
                            💎
                        </div>
                        <h4 style="margin:0; color:#333; font-size:16px; font-weight:600;">Giá trị vòng đời khách hàng (CLV)</h4>
                    </div>
                    <p style="margin-bottom:5px; padding-left:38px;">Giá trị vòng đời trung bình: <b>${:.2f}</b> / khách hàng</p>
                    <p style="margin-bottom:0; padding-left:38px;">Tiềm năng khi tăng 20% CLV: <b>${:.2f}</b> tổng doanh thu</p>
                </div>
                """.format(clv, potential_revenue), unsafe_allow_html=True)
            
            # Phần 2: Gợi ý hành động
            with col2:
                # Xác định các hành động dựa trên loại cụm từ tên Tiếng Anh
                actions = []
                
                # Kiểm tra các tên tiếng Anh trong segment_type
                if "High Value" in segment_type or "Very High Value" in segment_type:
                    actions = [
                        "Dịch vụ cá nhân hóa VIP",
                        "Giới thiệu sản phẩm cao cấp",
                        "Chương trình ưu đãi theo cấp bậc",
                        "Phân tích chi tiêu chi tiết"
                    ]
                elif "Medium Value" in segment_type:
                    actions = [
                        "Tăng giá trị đơn hàng (upsell)",
                        "Chương trình tích điểm khách hàng",
                        "Chương trình giới thiệu người dùng mới",
                        "Cá nhân hóa tiếp thị theo lịch sử"
                    ]
                elif "Low Value" in segment_type or "Medium Low Value" in segment_type:
                    actions = [
                        "Chiến dịch kích hoạt mua lại",
                        "Khảo sát tìm hiểu hành vi khách hàng",
                        "Cung cấp ưu đãi giảm giá có thời hạn",
                        "Đề xuất sản phẩm phù hợp ngân sách"
                    ]
                else:  # Fallback cho các trường hợp khác
                    actions = [
                        "Phân tích hành vi mua hàng",
                        "Cá nhân hóa đề xuất sản phẩm",
                        "Tối ưu chiến lược định giá",
                        "Tạo chiến dịch theo mùa"
                    ]
                
                # Hiển thị danh sách hành động với style đẹp hơn
                st.markdown(f"""
                <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #f0ad4e; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="background-color:#f0ad4e; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:14px;">
                            🎯
                        </div>
                        <h4 style="margin:0; color:#333; font-size:16px; font-weight:600;">Đề xuất hành động</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                for i, action in enumerate(actions, 1):
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom:8px; padding-left:38px;">
                        <div style="background-color: #f0ad4e; color: white; border-radius: 50%; width: 24px; height: 24px; 
                                    display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight:bold;">
                            {i}
                        </div>
                        <div>{action}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Thêm phần gợi ý chiến lược
                st.markdown(f"""
                <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #9370db; margin-top:15px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display:flex; align-items:center; margin-bottom:8px;">
                        <div style="background-color:#9370db; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; margin-right:10px; font-size:14px;">
                            🔑
                        </div>
                        <h4 style="margin:0; color:#333; font-size:16px; font-weight:600;">Chiến lược chính</h4>
                    </div>
                    <p style="margin-bottom:0; padding-left:38px;">{self._get_main_strategy(segment_type)}</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Lỗi khi phân tích dữ liệu: {str(e)}")
            st.info("Không thể tạo phân tích chi tiết do dữ liệu không đầy đủ hoặc không hợp lệ. Vui lòng kiểm tra lại dữ liệu đầu vào.")
        
        # Đóng div của phần phân tích
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _get_main_strategy(self, segment_type):
        """
        Trả về chiến lược chính dựa trên loại phân khúc
        
        Parameters:
        -----------
        segment_type : str
            Tên phân khúc khách hàng
            
        Returns:
        --------
        str: Chiến lược chính phù hợp với phân khúc
        """
        if "High Value" in segment_type or "Very High Value" in segment_type:
            return "Tập trung vào việc giữ chân và nâng cao trải nghiệm cho nhóm khách hàng có giá trị cao này. Ưu tiên dịch vụ khách hàng VIP và các sản phẩm cao cấp."
        elif "Medium Value" in segment_type:
            return "Khai thác tiềm năng tăng trưởng bằng cách thúc đẩy tần suất mua hàng và giá trị đơn hàng. Tạo các chương trình khuyến mãi đặc biệt."
        elif "Low Value" in segment_type or "Medium Low Value" in segment_type:
            return "Kích hoạt giao dịch mới và tìm hiểu nhu cầu để nâng cấp giá trị khách hàng. Cung cấp ưu đãi hấp dẫn để tăng tương tác."
        else:
            return "Phân tích kỹ lưỡng hành vi khách hàng để xây dựng chiến lược phù hợp. Cân nhắc thử nghiệm các phương pháp tiếp thị mới."

    def show_error(self, msg):
        """Display error message"""
        st.error(f"❌ Lỗi: {msg}")
        
    def show_success(self, msg):
        """Display success message"""
        st.success(f"✅ {msg}")
