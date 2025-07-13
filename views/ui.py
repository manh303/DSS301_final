import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import datetime

class UIView:
    """View class for UI handling"""
    
    def upload_page(self):
        """
        Display the upload page with input data configuration
        
        Returns:
        --------
        tuple: (uploaded_file, k, ref_date, country_filter, revenue_target)
            - uploaded_file: Uploaded file
            - k: Number of clusters
            - ref_date: Reference date
            - country_filter: Country filter
            - revenue_target: Revenue target for analysis
        """
        st.title("📊 Hệ thống phân cụm khách hàng RFM")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📁 Tải lên dữ liệu giao dịch")
            uploaded_file = st.file_uploader("Chọn file CSV", type=["csv"])
            
        with col2:
            st.markdown("### ⚙️ Cấu hình phân tích")
            k = st.selectbox("Số lượng cụm (k)", [3, 4, 5], index=0)
            
            # Initialize date variables
            max_date = datetime.date.today()
            default_date = max_date
            
            # Initialize country options and default value
            country_options = ["Tải file CSV để xem các quốc gia"]
            country_filter = "Tất cả"
            disabled_country = True
            
            # If file is uploaded, get data from the file
            if uploaded_file is not None:
                try:
                    # Read the uploaded file
                    df_temp = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
                    
                    # Reset file pointer to beginning for later use
                    uploaded_file.seek(0)
                    
                    # Find the latest date in the data if InvoiceDate column exists
                    if 'InvoiceDate' in df_temp.columns:
                        # Convert InvoiceDate to datetime
                        df_temp['InvoiceDate'] = pd.to_datetime(df_temp['InvoiceDate'], errors='coerce')
                        
                        # Get the latest date
                        latest_date = df_temp['InvoiceDate'].max()
                        
                        if not pd.isna(latest_date):
                            # Convert to date object
                            max_date = latest_date.date()
                            default_date = max_date
                    else:
                        st.warning("⚠️ File CSV không có cột InvoiceDate. Sẽ sử dụng ngày hôm nay.")
                    
                    # Check if Country column exists
                    if 'Country' in df_temp.columns:
                        # Get unique countries and sort them
                        countries = sorted(df_temp['Country'].unique().tolist())
                        
                        # Add "Tất cả" as the first option
                        country_options = ["Tất cả"] + countries
                        disabled_country = False
                    else:
                        country_options = ["Không tìm thấy cột Country"]
                        st.warning("⚠️ File CSV không có cột Country. Sẽ xử lý tất cả dữ liệu.")
                except Exception as e:
                    country_options = ["Lỗi đọc file"]
                    st.error(f"❌ Lỗi khi đọc file: {str(e)}")
            
            # Display reference date with restrictions
            ref_date = st.date_input(
                "Ngày tham chiếu",
                value=default_date,
                max_value=max_date
            )
            st.caption(f"Ngày tham chiếu dùng để tính Recency - tối đa là ngày {max_date}")
            
            # Always show the country filter dropdown
            st.markdown("#### Phạm vi khách hàng")
            if disabled_country:
                st.selectbox("Chọn quốc gia", country_options, disabled=True)
                st.caption("Tải file CSV lên để chọn phạm vi khách hàng")
                # We still need to return a value even if disabled
                country_filter = "Tất cả"
            else:
                country_filter = st.selectbox("Chọn quốc gia", country_options)
            
            # Add revenue target input field
            st.markdown("#### Mục tiêu doanh thu")
            revenue_target = st.number_input(
                "Nhập mục tiêu doanh thu (đơn vị tiền tệ)",
                min_value=1000,
                max_value=1000000,
                value=100000,
                step=10000,
                format="%d"
            )
            st.caption("Mục tiêu doanh thu sẽ được sử dụng để so sánh và phân tích xu hướng")
            
            analyze_btn = st.button("🔍 Phân tích dữ liệu", type="primary")
            if analyze_btn and uploaded_file is None:
                st.error("❌ Vui lòng tải lên file dữ liệu!")
            elif analyze_btn:
                st.session_state.screen = 'analysis'
                st.rerun()
        
        return uploaded_file, k, ref_date, country_filter, revenue_target

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
        st.title("📈 Phân tích cụm & Đề xuất hành động")
        
        # Create tabs for clusters with meaningful names
        cluster_ids = sorted(df_rfm['Cluster'].unique())
        
        # Phân loại cụm dựa trên đặc điểm tương đối
        try:
            # Xếp hạng các cụm theo từng chỉ số RFM
            recency_rank = summary_df['Recency_mean'].rank(ascending=False)  # Recency cao = xếp hạng cao = ít mua gần đây
            frequency_rank = summary_df['Frequency_mean'].rank()  # Frequency thấp = xếp hạng thấp
            monetary_rank = summary_df['Monetary_mean'].rank()  # Monetary thấp = xếp hạng thấp
            
            # Tính điểm tổng hợp (thấp = tốt)
            total_score = recency_rank + (3 - frequency_rank) + (3 - monetary_rank)
            
            # Xác định loại cụm dựa trên điểm tổng hợp
            cluster_types = {}
            
            # Xác định cụm có giá trị cao nhất
            high_value_cluster = monetary_rank.idxmax()
            cluster_types[high_value_cluster] = {"name": "Giá trị cao", "emoji": "💎"}
            
            # Xác định cụm trung thành (tần suất cao nhất)
            loyal_cluster = frequency_rank.idxmax()
            if loyal_cluster != high_value_cluster:
                cluster_types[loyal_cluster] = {"name": "Trung thành", "emoji": "🏆"}
            
            # Xác định cụm nguy cơ rời bỏ (recency cao nhất)
            churn_risk_cluster = recency_rank.idxmax()
            if churn_risk_cluster not in cluster_types:
                cluster_types[churn_risk_cluster] = {"name": "Nguy cơ rời bỏ", "emoji": "⚠️"}
            
            # Nếu vẫn còn cụm chưa được phân loại, gán tên dựa trên đặc điểm nổi bật
            for cluster_id in cluster_ids:
                if cluster_id not in cluster_types:
                    if frequency_rank[cluster_id] > recency_rank[cluster_id]:
                        cluster_types[cluster_id] = {"name": "Thường xuyên mua", "emoji": "🔄"}
                    else:
                        cluster_types[cluster_id] = {"name": "Tiềm năng", "emoji": "🌱"}
        except Exception as e:
            # Nếu có lỗi, sử dụng phân loại dự phòng
            cluster_types = {}
            for i in cluster_ids:
                if i % 3 == 0:
                    cluster_types[i] = {"name": "Giá trị cao", "emoji": "💎"}
                elif i % 3 == 1:
                    cluster_types[i] = {"name": "Trung thành", "emoji": "🏆"}
                else:
                    cluster_types[i] = {"name": "Tiềm năng", "emoji": "🌱"}
        
        # Tạo tên tab cho từng cụm
        tab_names = [f"Cụm {i} - {cluster_types[i]['emoji']} {cluster_types[i]['name']}" for i in cluster_ids]
        
        # Lưu thông tin phân loại cụm vào session state để các phương thức khác có thể sử dụng
        st.session_state.cluster_types = cluster_types
        
        # Tạo tabs với tên có ý nghĩa
        tabs = st.tabs(tab_names)
        
        # Display information for each cluster in its respective tab
        for i, cluster_id in enumerate(cluster_ids):
            with tabs[i]:
                self.show_cluster_tab(cluster_id, df_rfm, summary_df, revenue_target, latest_date, monthly_revenue)
        
        # Add button to go back to upload page
        if st.button("⬅️ Quay lại trang dữ liệu đầu vào"):
            st.session_state.screen = 'upload'
            st.rerun()
    
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
        
        # 1. Overview section
        self.show_cluster_overview(cluster_id, cluster_summary)
        
        # 2. Customer list and forecast chart in two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.show_customer_list(cluster_df)
            
        with col2:
            self.show_forecast_chart(revenue_target, latest_date, cluster_id, monthly_revenue)
            
            with st.expander("Giải thích biểu đồ"):
                st.write("- Đường màu xanh: Doanh thu thực tế của cụm")
                st.write("- Đường màu cam: Dự báo doanh thu 3 tháng tiếp theo")
                st.write("- Đường màu đỏ đứt nét: Mục tiêu doanh thu")
                st.write(f"- Biểu đồ thể hiện xu hướng doanh thu từ dữ liệu thực tế và dự báo 3 tháng sau ngày {latest_date.strftime('%d/%m/%Y')}")
        
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
                # Xác định loại cụm dựa trên các chỉ số RFM nếu không có trong session state
                recency_mean = float(cluster_summary.get('Recency_mean', 0))
                frequency_mean = float(cluster_summary.get('Frequency_mean', 0))
                monetary_mean = float(cluster_summary.get('Monetary_mean', 0))
                
                # Xác định tên cụm dựa trên đặc điểm nổi bật nhất
                if frequency_mean > 3:
                    cluster_name = "Nhóm khách hàng trung thành"
                    emoji = "🏆"
                elif monetary_mean > 500:
                    cluster_name = "Nhóm khách hàng giá trị cao"
                    emoji = "💎"
                elif recency_mean > 60:
                    cluster_name = "Nhóm khách hàng nguy cơ rời bỏ"
                    emoji = "⚠️"
                else:
                    cluster_name = "Nhóm khách hàng tiềm năng"
                    emoji = "🌱"
            
            # Hiển thị tiêu đề với tên cụm
            st.markdown(f"## Tổng quan Cụm {cluster_id} - {emoji} {cluster_name}:")
            
            # Lấy các giá trị RFM
            recency_mean = float(cluster_summary.get('Recency_mean', 0))
            frequency_mean = float(cluster_summary.get('Frequency_mean', 0))
            monetary_mean = float(cluster_summary.get('Monetary_mean', 0))
            
            # Create metrics in 3 columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Trung bình ngày từ lần mua cuối", f"{recency_mean:.1f} ngày")
                
            with col2:
                st.metric("Trung bình số lần mua", f"{frequency_mean:.1f} lần")
                
            with col3:
                st.metric("Trung bình giá trị mua", f"${monetary_mean:.2f}")
                
            # Create a second row of metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                customer_count = int(cluster_summary.get('Monetary_count', 0))
                customer_ratio = float(cluster_summary.get('customer_ratio', 0)) * 100
                st.metric("Số lượng khách hàng", f"{customer_count}", f"{customer_ratio:.1f}% tổng số")
                
            with col2:
                total_revenue = float(cluster_summary.get('total_revenue', 0))
                revenue_ratio = float(cluster_summary.get('revenue_ratio', 0)) * 100
                st.metric("Tổng doanh thu", f"${total_revenue:.2f}", f"{revenue_ratio:.1f}% tổng số")
                
            with col3:
                clv = float(cluster_summary.get('clv', 0))
                st.metric("Giá trị vòng đời khách hàng", f"${clv:.2f}")
        except Exception as e:
            st.error(f"Lỗi: {str(e)}")
            st.info("Đang gặp sự cố khi xử lý dữ liệu cụm. Vui lòng kiểm tra lại dữ liệu đầu vào hoặc thử lại.")
    
    def show_customer_list(self, cluster_df):
        """
        Display list of customers in the cluster
        
        Parameters:
        -----------
        cluster_df : DataFrame
            RFM data for customers in this cluster
        """
        st.markdown("### Danh sách khách hàng")
        
        try:
            # Sort customers by Monetary value (descending)
            sorted_customers = cluster_df.sort_values(by='Monetary', ascending=False)
            
            # Prepare data for display
            customer_table = sorted_customers[['CustomerID', 'Recency', 'Frequency', 'Monetary']].head(15).copy()
            
            # Format columns
            customer_table['CustomerID'] = customer_table['CustomerID'].astype(int)
            customer_table['Recency'] = customer_table['Recency'].round(0).astype(int)
            customer_table['Frequency'] = customer_table['Frequency'].round(1)
            customer_table['Monetary'] = customer_table['Monetary'].round(2)
            
            # Rename columns for better display
            customer_table.columns = ['ID Khách hàng', 'Ngày từ lần mua cuối', 'Số lần mua', 'Tổng chi tiêu ($)']
            
            # Display table
            st.dataframe(customer_table, hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Lỗi khi hiển thị danh sách khách hàng: {str(e)}")
            st.info("Không thể hiển thị danh sách khách hàng. Vui lòng kiểm tra lại dữ liệu.")
    
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
        # Hiển thị tiêu đề biểu đồ
        st.markdown("### Biểu đồ doanh thu theo tháng")
        
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
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plot actual values
        ax.plot(np.arange(len(months)), actual_values, marker='o', linewidth=2, color='#1f77b4', label='Doanh thu thực tế')
        
        # Plot prediction values
        # Tính toán vị trí bắt đầu của dự báo
        forecast_start_idx = len(months) - 1  # Vị trí cuối cùng của dữ liệu thực tế
        forecast_x = np.arange(forecast_start_idx, forecast_start_idx + len(forecast_values) + 1)
        forecast_y = np.concatenate(([actual_values[-1]], forecast_values))  # Bắt đầu từ giá trị cuối cùng của dữ liệu thực tế
        
        ax.plot(forecast_x, forecast_y, marker='o', linewidth=2, color='#ff7f0e', linestyle='--', label='Dự báo')
        
        # Plot target value line
        revenue_target_float = float(revenue_target)
        ax.axhline(y=revenue_target_float, color='red', linestyle='--', alpha=0.7, label=f'Mục tiêu: ${int(revenue_target_float)}')
        
        # Set labels and title
        ax.set_xticks(np.arange(all_months_count))
        ax.set_xticklabels(all_months, rotation=45)
        ax.set_xlabel('Tháng')
        ax.set_ylabel('Doanh thu')
        
        # Set title with reference to data period
        title = "Xu hướng doanh thu"
        if latest_date is not None:
            title += f" (Dữ liệu đến {latest_date.strftime('%d-%m-%Y')})"
            
        ax.set_title(title)
        
        # Add grid and legend
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        
        # Adjust layout to prevent cutting off labels
        fig.tight_layout()
        
        # Display chart
        st.pyplot(fig)
        
        # Add summary metrics below the chart
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_value = float(np.mean(actual_values))
            diff_pct = ((avg_value - revenue_target_float) / revenue_target_float) * 100 if revenue_target_float > 0 else 0
            st.metric("Doanh thu trung bình", f"${int(avg_value)}", f"{diff_pct:.1f}%", 
                     delta_color="normal" if diff_pct >= 0 else "inverse")
        
        with col2:
            months_above_target = int(np.sum(actual_values > revenue_target_float))
            st.metric("Tháng vượt mục tiêu", f"{months_above_target}/{len(actual_values)}", 
                     f"{(months_above_target/len(actual_values))*100:.0f}%" if len(actual_values) > 0 else "0%")
            
        with col3:
            last_month_value = float(actual_values[-1]) if len(actual_values) > 0 else 0
            last_month_vs_target = ((last_month_value - revenue_target_float) / revenue_target_float) * 100 if revenue_target_float > 0 else 0
            st.metric("Tháng gần nhất", f"${int(last_month_value)}", f"{last_month_vs_target:.1f}%",
                     delta_color="normal" if last_month_vs_target >= 0 else "inverse")
    
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
        st.markdown("### Phân tích & Hành động")
        
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
                segment_type = cluster_type["name"]
                emoji = cluster_type["emoji"]
            else:
                # Xác định loại cụm dựa trên các chỉ số RFM nếu không có trong session state
                if recency_mean <= 30 and frequency_mean >= 3:
                    segment_type = "Khách hàng trung thành"
                    emoji = "🏆"
                elif recency_mean <= 30 and monetary_mean >= 500:
                    segment_type = "Khách hàng giá trị cao"
                    emoji = "💎"
                elif recency_mean > 60 and frequency_mean < 2:
                    segment_type = "Khách hàng nguy cơ rời bỏ"
                    emoji = "⚠️"
                elif frequency_mean > 3:
                    segment_type = "Khách hàng thường xuyên mua"
                    emoji = "🔄"
                else:
                    segment_type = "Khách hàng tiềm năng"
                    emoji = "🌱"
            
            # Hiển thị phân tích và các phương án
            st.markdown("#### Phân tích & Các phương án")
            
            # Phần 1: Lịch sử doanh thu và so sánh
            with st.container():
                # Tính toán doanh thu trung bình hàng tháng
                avg_monthly_revenue = total_revenue / 3  # Giả định dữ liệu là 3 tháng
                target_gap = revenue_target - avg_monthly_revenue
                target_gap_pct = (target_gap / avg_monthly_revenue) * 100 if avg_monthly_revenue > 0 else 0
                
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #6c757d;">
                    <p>Doanh thu trung bình hàng tháng của nhóm khách hàng này là: <b>${:.2f}</b></p>
                    <p>Để đạt mục tiêu doanh thu ${:.0f}, bạn cần tăng <b>{:.1f}%</b> doanh thu so với hiện tại</p>
                </div>
                """.format(avg_monthly_revenue, float(revenue_target), abs(target_gap_pct)), unsafe_allow_html=True)
            
            # Phần 2: Gợi ý hành động
            st.markdown("#### Gợi ý hành động")
            
            # Xác định các hành động dựa trên loại cụm
            actions = []
            if segment_type == "Trung thành" or segment_type == "Khách hàng trung thành":
                actions = [
                    "Tăng giá trị đơn hàng: đề xuất sản phẩm bổ sung hoặc cao cấp hơn (upsell/cross-sell)",
                    "Chương trình khách hàng thân thiết: tạo ưu đãi đặc biệt để tăng tần suất mua hàng",
                    "Phân tích giỏ hàng: xác định các sản phẩm thường được mua cùng nhau để tăng doanh thu",
                    "Chương trình giới thiệu: khuyến khích khách hàng giới thiệu bạn bè để mở rộng cơ sở khách hàng"
                ]
            elif segment_type == "Giá trị cao" or segment_type == "Khách hàng giá trị cao":
                actions = [
                    "Dịch vụ cá nhân hóa: cung cấp trải nghiệm VIP để duy trì chi tiêu cao",
                    "Tiếp thị sản phẩm cao cấp: giới thiệu sản phẩm cao cấp và phiên bản giới hạn để tăng doanh thu",
                    "Chương trình ưu đãi theo cấp bậc: tạo ưu đãi đặc biệt dựa trên mức chi tiêu",
                    "Phân tích chi tiêu: xác định xu hướng chi tiêu để tối ưu hóa danh mục sản phẩm"
                ]
            elif segment_type == "Nguy cơ rời bỏ" or segment_type == "Khách hàng nguy cơ rời bỏ":
                actions = [
                    "Chiến dịch win-back: gửi ưu đãi đặc biệt để kích hoạt lại giao dịch mua",
                    "Phân tích lý do rời bỏ: khảo sát để hiểu nguyên nhân khách hàng không mua hàng",
                    "Chiến lược giá linh hoạt: cung cấp giảm giá có thời hạn để khuyến khích mua lại",
                    "Nâng cao trải nghiệm khách hàng: cải thiện dịch vụ để tăng sự hài lòng và doanh thu"
                ]
            else:  # Khách hàng tiềm năng hoặc thường xuyên mua
                actions = [
                    "Phân tích hành vi mua hàng: xác định các mô hình chi tiêu để tối ưu hóa tiếp thị",
                    "Cá nhân hóa đề xuất sản phẩm: dựa trên lịch sử mua hàng để tăng tỷ lệ chuyển đổi",
                    "Chiến lược định giá theo phân khúc: tối ưu hóa giá cho các phân khúc khách hàng khác nhau",
                    "Chương trình khuyến mãi theo mùa: tạo chiến dịch theo mùa để thúc đẩy doanh thu"
                ]
            
            # Hiển thị danh sách hành động với số thứ tự
            for i, action in enumerate(actions, 1):
                st.markdown(f"{i}. {action}")
            
            # Phần 3: Lưu ý
            st.markdown("#### Lưu ý")
            with st.container():
                # Tính toán giá trị vòng đời khách hàng (CLV)
                clv = float(cluster_summary.get('clv', 0))
                potential_revenue = clv * customer_count * 1.2  # Giả định tăng 20% CLV
                
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545;">
                    <p>Giá trị vòng đời trung bình của mỗi khách hàng trong nhóm này là: <b>${:.2f}</b></p>
                    <p>Nếu tăng giá trị vòng đời lên 20%, nhóm này có thể tạo ra <b>${:.2f}</b> doanh thu tiềm năng</p>
                </div>
                """.format(clv, potential_revenue), unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Lỗi khi phân tích dữ liệu: {str(e)}")
            st.info("Không thể tạo phân tích chi tiết do dữ liệu không đầy đủ hoặc không hợp lệ. Vui lòng kiểm tra lại dữ liệu đầu vào.")

    def show_error(self, msg):
        """Display error message"""
        st.error(f"❌ Lỗi: {msg}")
        
    def show_success(self, msg):
        """Display success message"""
        st.success(f"✅ {msg}")
