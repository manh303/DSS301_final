import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import datetime

class RFMModel:
    """Model xử lý dữ liệu RFM và phân cụm khách hàng"""
    
    def load_data_from_path(self, file_path, country, ref_date=None):
        """
        Tải và tiền xử lý dữ liệu từ đường dẫn file CSV
        
        Parameters:
        -----------
        file_path : str
            Đường dẫn đến file CSV chứa dữ liệu giao dịch
        country : str
            Quốc gia để lọc dữ liệu, "Tất cả" để không lọc
        ref_date : datetime
            Ngày tham chiếu để lọc dữ liệu (chỉ lấy từ ngày này trở đi)
            
        Returns:
        --------
        tuple: (DataFrame, datetime)
            - DataFrame: Dữ liệu đã được xử lý
            - datetime: Ngày cuối cùng trong dữ liệu
        """
        df = pd.read_csv(file_path, encoding='ISO-8859-1')
        
        # Đảm bảo CustomerID là kiểu số
        if 'CustomerID' in df.columns:
            # Chuyển đổi CustomerID thành float nếu có thể, bỏ qua các giá trị không thể chuyển đổi
            df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='coerce')
            # Loại bỏ các dòng không có CustomerID
            df = df.dropna(subset=['CustomerID'])
            # Chuyển CustomerID thành kiểu int để đảm bảo tính nhất quán
            df['CustomerID'] = df['CustomerID'].astype(int)
        else:
            raise ValueError("File CSV không có cột CustomerID")
            
        # Đảm bảo các cột số lượng và giá là kiểu số
        if 'Quantity' in df.columns and 'UnitPrice' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
        else:
            raise ValueError("File CSV không có cột Quantity hoặc UnitPrice")
        
        # Loại bỏ các hóa đơn hủy (bắt đầu bằng 'C')
        if 'InvoiceNo' in df.columns:
            df['InvoiceNo'] = df['InvoiceNo'].astype(str)
            df = df[~df['InvoiceNo'].str.startswith('C')]
        else:
            raise ValueError("File CSV không có cột InvoiceNo")
        
        # Chỉ giữ lại các giao dịch có số lượng và giá dương
        df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
        
        # Chuyển đổi cột ngày thành datetime
        if 'InvoiceDate' in df.columns:
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
            # Loại bỏ các dòng có ngày không hợp lệ
            df = df.dropna(subset=['InvoiceDate'])
        else:
            raise ValueError("File CSV không có cột InvoiceDate")
            
        # Lấy ngày cuối cùng từ dữ liệu
        latest_date = df['InvoiceDate'].max()
        
        # Lọc dữ liệu từ ngày tham chiếu đến ngày cuối cùng nếu có ngày tham chiếu
        if ref_date is not None:
            # Chuyển đổi ref_date thành datetime nếu là string hoặc date
            if isinstance(ref_date, (str, datetime.date)):
                ref_date = pd.to_datetime(ref_date)
                
            # Lọc dữ liệu từ ngày tham chiếu
            df = df[df['InvoiceDate'] >= ref_date]
        
        # Lọc theo quốc gia nếu được chỉ định
        if country != "Tất cả" and 'Country' in df.columns:
            df = df[df['Country'] == country]
            
        # Thêm cột doanh thu (Quantity * UnitPrice)
        df['Revenue'] = df['Quantity'] * df['UnitPrice']
            
        return df, latest_date
        
    def load_data(self, file, country, ref_date=None):
        """
        Tải và tiền xử lý dữ liệu từ file CSV
        
        Parameters:
        -----------
        file : FileUpload
            File CSV chứa dữ liệu giao dịch
        country : str
            Quốc gia để lọc dữ liệu, "Tất cả" để không lọc
        ref_date : datetime
            Ngày tham chiếu để lọc dữ liệu (chỉ lấy từ ngày này trở đi)
            
        Returns:
        --------
        tuple: (DataFrame, datetime)
            - DataFrame: Dữ liệu đã được xử lý
            - datetime: Ngày cuối cùng trong dữ liệu
        """
        df = pd.read_csv(file, encoding='ISO-8859-1')
        
        # Đảm bảo CustomerID là kiểu số
        if 'CustomerID' in df.columns:
            # Chuyển đổi CustomerID thành float nếu có thể, bỏ qua các giá trị không thể chuyển đổi
            df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='coerce')
            # Loại bỏ các dòng không có CustomerID
            df = df.dropna(subset=['CustomerID'])
            # Chuyển CustomerID thành kiểu int để đảm bảo tính nhất quán
            df['CustomerID'] = df['CustomerID'].astype(int)
        else:
            raise ValueError("File CSV không có cột CustomerID")
            
        # Đảm bảo các cột số lượng và giá là kiểu số
        if 'Quantity' in df.columns and 'UnitPrice' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
        else:
            raise ValueError("File CSV không có cột Quantity hoặc UnitPrice")
        
        # Loại bỏ các hóa đơn hủy (bắt đầu bằng 'C')
        if 'InvoiceNo' in df.columns:
            df['InvoiceNo'] = df['InvoiceNo'].astype(str)
            df = df[~df['InvoiceNo'].str.startswith('C')]
        else:
            raise ValueError("File CSV không có cột InvoiceNo")
        
        # Chỉ giữ lại các giao dịch có số lượng và giá dương
        df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
        
        # Chuyển đổi cột ngày thành datetime
        if 'InvoiceDate' in df.columns:
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
            # Loại bỏ các dòng có ngày không hợp lệ
            df = df.dropna(subset=['InvoiceDate'])
        else:
            raise ValueError("File CSV không có cột InvoiceDate")
            
        # Lấy ngày cuối cùng từ dữ liệu
        latest_date = df['InvoiceDate'].max()
        
        # Lọc dữ liệu từ ngày tham chiếu đến ngày cuối cùng nếu có ngày tham chiếu
        if ref_date is not None:
            # Chuyển đổi ref_date thành datetime nếu là string hoặc date
            if isinstance(ref_date, (str, datetime.date)):
                ref_date = pd.to_datetime(ref_date)
                
            # Lọc dữ liệu từ ngày tham chiếu
            df = df[df['InvoiceDate'] >= ref_date]
        
        # Lọc theo quốc gia nếu được chỉ định
        if country != "Tất cả" and 'Country' in df.columns:
            df = df[df['Country'] == country]
            
        # Thêm cột doanh thu (Quantity * UnitPrice)
        df['Revenue'] = df['Quantity'] * df['UnitPrice']
            
        return df, latest_date

    def calculate_rfm(self, df, ref_date):
        """
        Tính toán chỉ số RFM từ dữ liệu giao dịch
        
        Parameters:
        -----------
        df : DataFrame
            Dữ liệu giao dịch đã qua tiền xử lý
        ref_date : datetime
            Ngày tham chiếu để tính toán recency
            
        Returns:
        --------
        DataFrame: Chỉ số RFM của từng khách hàng
        """
        try:
            # Kiểm tra dữ liệu đầu vào
            if df.empty:
                raise ValueError("Dữ liệu giao dịch rỗng")
                
            # Chuyển đổi ref_date thành datetime nếu chưa phải
            ref_date = pd.to_datetime(ref_date)
            
            # Đảm bảo InvoiceDate là kiểu datetime
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
            df = df.dropna(subset=['InvoiceDate'])
            
            # Xác định ngày cuối cùng của mỗi khách hàng
            last_purchase = df.groupby('CustomerID')['InvoiceDate'].max().reset_index()
            
            # Tính số ngày giữa ngày mua cuối cùng và ngày tham chiếu
            last_purchase['Recency'] = (ref_date - last_purchase['InvoiceDate']).dt.days
            
            # Đảm bảo Recency không âm
            last_purchase['Recency'] = last_purchase['Recency'].apply(lambda x: max(0, x))
            
            # Tính tần suất mua hàng (số hóa đơn)
            frequency = df.groupby('CustomerID')['InvoiceNo'].nunique().reset_index()
            frequency.rename(columns={'InvoiceNo': 'Frequency'}, inplace=True)
            
            # Tính giá trị khách hàng (tổng doanh thu)
            monetary = df.groupby('CustomerID')['Revenue'].sum().reset_index()
            monetary.rename(columns={'Revenue': 'Monetary'}, inplace=True)
            
            # Gộp các chỉ số RFM
            rfm = pd.merge(last_purchase, frequency, on='CustomerID')
            rfm = pd.merge(rfm, monetary, on='CustomerID')
            
            # Chỉ giữ các cột cần thiết
            rfm = rfm[['CustomerID', 'Recency', 'Frequency', 'Monetary']]
            
            # Kiểm tra và xử lý các giá trị NaN
            if rfm.isna().any().any():
                rfm = rfm.dropna()
                if rfm.empty:
                    raise ValueError("Không thể tính toán RFM: Tất cả các dòng đều có giá trị NaN")
            
            # Đảm bảo các cột có kiểu dữ liệu đúng
            rfm['Recency'] = pd.to_numeric(rfm['Recency'], errors='coerce')
            rfm['Frequency'] = pd.to_numeric(rfm['Frequency'], errors='coerce')
            rfm['Monetary'] = pd.to_numeric(rfm['Monetary'], errors='coerce')
            
            # Loại bỏ các dòng có giá trị NaN sau khi chuyển đổi
            rfm = rfm.dropna()
            
            if rfm.empty:
                raise ValueError("Không thể tính toán RFM: Dữ liệu không hợp lệ sau khi xử lý")
                
            return rfm
            
        except Exception as e:
            raise ValueError(f"Lỗi khi tính toán RFM: {str(e)}")
    
    def cluster_rfm(self, rfm_df, k=3):
        """
        Phân cụm khách hàng dựa trên chỉ số RFM
        
        Parameters:
        -----------
        rfm_df : DataFrame
            DataFrame chứa chỉ số RFM
        k : int, mặc định=3
            Số lượng cụm
            
        Returns:
        --------
        DataFrame: Dữ liệu RFM với nhãn cụm
        """
        try:
            # Kiểm tra dữ liệu đầu vào
            if rfm_df.empty:
                raise ValueError("Dữ liệu RFM rỗng")
                
            # Kiểm tra các cột bắt buộc
            required_cols = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
            for col in required_cols:
                if col not in rfm_df.columns:
                    raise ValueError(f"Dữ liệu thiếu cột {col}")
            
            # Sao chép dữ liệu để không ảnh hưởng đến dữ liệu gốc
            df = rfm_df.copy()
            
            # Đảm bảo các cột RFM có kiểu dữ liệu đúng
            for col in ['Recency', 'Frequency', 'Monetary']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Loại bỏ các dòng có giá trị NaN
            df = df.dropna(subset=['Recency', 'Frequency', 'Monetary'])
            
            if df.empty:
                raise ValueError("Không thể phân cụm: Dữ liệu không hợp lệ sau khi xử lý")
            
            # Chuẩn hóa dữ liệu
            scaler = StandardScaler()
            df_scaled = scaler.fit_transform(df[['Recency', 'Frequency', 'Monetary']])
            
            # Phân cụm
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            df['Cluster'] = kmeans.fit_predict(df_scaled)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Lỗi khi phân cụm RFM: {str(e)}")
    
    def cluster_summary(self, clustered_df):
        """
        Tạo bảng tóm tắt cho mỗi cụm
        
        Parameters:
        -----------
        clustered_df : DataFrame
            DataFrame chứa dữ liệu RFM và nhãn cụm
            
        Returns:
        --------
        DataFrame: Bảng tóm tắt các chỉ số của từng cụm
        """
        try:
            # Kiểm tra dữ liệu đầu vào
            if clustered_df.empty:
                raise ValueError("Dữ liệu cụm rỗng")
                
            # Kiểm tra các cột bắt buộc
            required_cols = ['CustomerID', 'Recency', 'Frequency', 'Monetary', 'Cluster']
            for col in required_cols:
                if col not in clustered_df.columns:
                    raise ValueError(f"Dữ liệu thiếu cột {col}")
            
            # Sao chép dữ liệu để không ảnh hưởng đến dữ liệu gốc
            df = clustered_df.copy()
            
            # Đảm bảo các cột có kiểu dữ liệu đúng
            df['Cluster'] = pd.to_numeric(df['Cluster'], errors='coerce')
            df['Recency'] = pd.to_numeric(df['Recency'], errors='coerce')
            df['Frequency'] = pd.to_numeric(df['Frequency'], errors='coerce')
            df['Monetary'] = pd.to_numeric(df['Monetary'], errors='coerce')
            
            # Loại bỏ các dòng có giá trị NaN
            df = df.dropna(subset=['Cluster', 'Recency', 'Frequency', 'Monetary'])
            
            if df.empty:
                raise ValueError("Không thể tạo tóm tắt: Dữ liệu không hợp lệ sau khi xử lý")
            
            # Tính các chỉ số tóm tắt cho mỗi cụm
            summary = df.groupby('Cluster').agg({
                'Recency': ['mean', 'min', 'max'],
                'Frequency': ['mean', 'min', 'max'],
                'Monetary': ['mean', 'min', 'max', 'count']
            })
            
            # Đổi tên cột để dễ đọc
            summary.columns = [f"{col[0]}_{col[1]}" for col in summary.columns]
            
            # Thêm cột tỷ lệ khách hàng
            total_customers = df.shape[0]
            summary['customer_ratio'] = summary['Monetary_count'] / total_customers
            
            # Thêm cột tổng doanh thu
            summary['total_revenue'] = summary['Monetary_mean'] * summary['Monetary_count']
            
            # Thêm cột tỷ lệ doanh thu
            total_revenue = df['Monetary'].sum()
            if total_revenue > 0:
                summary['revenue_ratio'] = summary['total_revenue'] / total_revenue
            else:
                summary['revenue_ratio'] = 0
            
            # Thêm cột CLV (Customer Lifetime Value) - giá trị đơn giản hóa
            summary['clv'] = summary['Monetary_mean'] * summary['Frequency_mean']
            
            return summary
            
        except Exception as e:
            raise ValueError(f"Lỗi khi tạo tóm tắt cụm: {str(e)}")
        
    def calculate_monthly_revenue(self, df, clustered_df):
        """
        Tính toán doanh thu theo tháng cho mỗi cụm khách hàng
        
        Parameters:
        -----------
        df : DataFrame
            Dữ liệu giao dịch gốc
        clustered_df : DataFrame
            DataFrame chứa dữ liệu RFM và nhãn cụm
            
        Returns:
        --------
        dict: Dictionary chứa doanh thu theo tháng cho mỗi cụm
        {
            cluster_id: {
                'months': list các tháng,
                'revenue': list doanh thu tương ứng
            }
        }
        """
        try:
            # Kiểm tra dữ liệu đầu vào
            if df.empty or clustered_df.empty:
                raise ValueError("Dữ liệu giao dịch hoặc dữ liệu cụm rỗng")
                
            # Kiểm tra các cột bắt buộc trong df
            required_cols_df = ['CustomerID', 'InvoiceDate', 'Revenue']
            for col in required_cols_df:
                if col not in df.columns:
                    raise ValueError(f"Dữ liệu giao dịch thiếu cột {col}")
                    
            # Kiểm tra các cột bắt buộc trong clustered_df
            required_cols_clustered = ['CustomerID', 'Cluster']
            for col in required_cols_clustered:
                if col not in clustered_df.columns:
                    raise ValueError(f"Dữ liệu cụm thiếu cột {col}")
            
            # Tạo bản sao của dữ liệu
            df = df.copy()
            clustered_df = clustered_df.copy()
            
            # Đảm bảo các cột có kiểu dữ liệu đúng
            df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='coerce')
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
            
            clustered_df['CustomerID'] = pd.to_numeric(clustered_df['CustomerID'], errors='coerce')
            clustered_df['Cluster'] = pd.to_numeric(clustered_df['Cluster'], errors='coerce')
            
            # Loại bỏ các dòng có giá trị NaN
            df = df.dropna(subset=['CustomerID', 'InvoiceDate', 'Revenue'])
            clustered_df = clustered_df.dropna(subset=['CustomerID', 'Cluster'])
            
            if df.empty or clustered_df.empty:
                raise ValueError("Không thể tính toán doanh thu theo tháng: Dữ liệu không hợp lệ sau khi xử lý")
            
            # Thêm cột tháng-năm
            df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')
            
            # Tạo dictionary ánh xạ CustomerID với Cluster
            customer_cluster_map = dict(zip(clustered_df['CustomerID'], clustered_df['Cluster']))
            
            # Thêm cột Cluster vào df
            df['Cluster'] = df['CustomerID'].map(customer_cluster_map)
            
            # Chỉ giữ lại các giao dịch có thông tin cụm
            df = df.dropna(subset=['Cluster'])
            if df.empty:
                raise ValueError("Không có giao dịch nào được ánh xạ với cụm khách hàng")
                
            df['Cluster'] = df['Cluster'].astype(int)
            
            # Tính tổng doanh thu theo tháng và cụm
            monthly_revenue = df.groupby(['YearMonth', 'Cluster'])['Revenue'].sum().reset_index()
            
            # Kiểm tra kết quả
            if monthly_revenue.empty:
                raise ValueError("Không có dữ liệu doanh thu theo tháng")
            
            # Tạo dictionary kết quả
            result = {}
            
            # Lấy danh sách tất cả các tháng
            all_months = sorted(monthly_revenue['YearMonth'].unique())
            
            # Với mỗi cụm, tạo danh sách doanh thu theo tháng
            for cluster in sorted(monthly_revenue['Cluster'].unique()):
                cluster_data = monthly_revenue[monthly_revenue['Cluster'] == cluster]
                
                # Tạo dictionary cho mỗi tháng
                months = [m.strftime('%b %Y') for m in all_months]
                revenue = []
                
                # Với mỗi tháng, lấy doanh thu hoặc 0 nếu không có dữ liệu
                for month in all_months:
                    month_data = cluster_data[cluster_data['YearMonth'] == month]
                    if not month_data.empty:
                        revenue.append(float(month_data['Revenue'].values[0]))
                    else:
                        revenue.append(0.0)
                
                # Lưu vào dictionary kết quả
                result[int(cluster)] = {
                    'months': months,
                    'revenue': revenue
                }
            
            # Nếu không có cụm nào được tính toán
            if not result:
                raise ValueError("Không thể tính toán doanh thu cho bất kỳ cụm nào")
                
            return result
            
        except Exception as e:
            raise ValueError(f"Lỗi khi tính toán doanh thu theo tháng: {str(e)}")

