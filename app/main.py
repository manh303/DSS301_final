import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load dữ liệu
df = pd.read_csv('/data/online_retail.csv', parse_dates=['InvoiceDate'])

# Làm sạch dữ liệu
df.dropna(inplace=True)
df['InvoiceNo'] = df['InvoiceNo'].astype(str)

# Phân tích tổng doanh thu theo quốc gia
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
revenue_by_country = df.groupby('Country')['TotalPrice'].sum().sort_values(ascending=False)

# Vẽ biểu đồ
plt.figure(figsize=(12, 6))
sns.barplot(x=revenue_by_country.index, y=revenue_by_country.values)
plt.xticks(rotation=90)
plt.title('Tổng doanh thu theo quốc gia')
plt.tight_layout()
plt.savefig('/app/revenue_by_country.png')
