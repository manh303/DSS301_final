import pandas as pd
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

class RevenueForecastModel:
    def __init__(self, df):
        self.df = df
        self.monthly_data = None

    def process_data(self):
        # Chuyển cột ngày về datetime
        self.df['Date'] = pd.to_datetime(self.df['Date'])

        # Nếu chưa có Revenue thì tính từ Quantity * UnitPrice
        if 'Revenue' not in self.df.columns:
            if 'Quantity' in self.df.columns and 'UnitPrice' in self.df.columns:
                self.df['Revenue'] = self.df['Quantity'] * self.df['UnitPrice']
            else:
                raise ValueError("Dữ liệu phải có cột 'Revenue' hoặc cả 'Quantity' và 'UnitPrice'")

        # Tạo cột tháng
        self.df['Month'] = self.df['Date'].dt.to_period('M').dt.to_timestamp()

    def forecast(self, stock_code, country, periods):
        if not PROPHET_AVAILABLE:
            return None, None
            
        # Lọc theo sản phẩm và quốc gia
        df_filtered = self.df[(self.df['StockCode'] == stock_code) & (self.df['Country'] == country)]

        if df_filtered.empty:
            return None, None

        # Tổng hợp doanh thu theo tháng
        monthly = df_filtered.groupby('Month')['Revenue'].sum().reset_index()
        monthly.columns = ['ds', 'y']

        if len(monthly) < 3:
            return None, None

        # Huấn luyện mô hình Prophet
        model = Prophet()
        model.fit(monthly)

        # Tạo khoảng thời gian tương lai
        future = model.make_future_dataframe(periods=periods, freq='M')
        forecast = model.predict(future)

        # Lấy các cột quan trọng và tính chênh lệch so với trung bình 3 tháng gần nhất
        forecast = forecast[['ds', 'yhat']]
        recent_avg = monthly['y'].tail(3).mean()
        forecast['delta'] = forecast['yhat'] - recent_avg
        forecast['pct_change'] = forecast['delta'] / recent_avg * 100

        return forecast.tail(periods), monthly
