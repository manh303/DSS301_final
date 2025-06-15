import pandas as pd
import plotly.express as px
import streamlit as st

# Load dữ liệu
df = pd.read_csv('/data/online_retail.csv', parse_dates=['InvoiceDate'])
df.dropna(inplace=True)
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
df['Month'] = df['InvoiceDate'].dt.to_period('M').astype(str)

st.set_page_config(layout="wide")
st.title("📊 Báo cáo quản trị – Phân tích dữ liệu hóa đơn")

# 1. Doanh thu theo tháng & quốc gia
st.subheader("1. Doanh thu theo tháng và quốc gia")
monthly_rev = df.groupby(['Month', 'Country'])['TotalPrice'].sum().reset_index()
fig1 = px.line(monthly_rev, x='Month', y='TotalPrice', color='Country', title="Doanh thu theo tháng và quốc gia")
st.plotly_chart(fig1, use_container_width=True)

# 2. Sản phẩm bán chạy nhất
st.subheader("2. Top 10 sản phẩm bán chạy nhất")
top_products = df.groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(10).reset_index()
fig2 = px.bar(top_products, x='Description', y='Quantity', title="Top 10 sản phẩm bán chạy nhất")
fig2.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig2, use_container_width=True)

# 3. Khách hàng lớn nhất
st.subheader("3. Top 5 khách hàng có tổng chi cao nhất")
top_customers = df.groupby('CustomerID')['TotalPrice'].sum().sort_values(ascending=False).head(5).reset_index()
fig3 = px.bar(top_customers, x='CustomerID', y='TotalPrice', title="Top 5 khách hàng chi tiêu cao nhất")
st.plotly_chart(fig3, use_container_width=True)

# 4. Thị trường sinh doanh thu cao nhất
st.subheader("4. Doanh thu theo quốc gia")
revenue_country = df.groupby('Country')['TotalPrice'].sum().sort_values(ascending=False).reset_index()
fig4 = px.bar(revenue_country.head(10), x='Country', y='TotalPrice', title="Top 10 quốc gia có doanh thu cao nhất")
st.plotly_chart(fig4, use_container_width=True)

# 5. Sản phẩm thường bị trả lại (Quantity < 0)
st.subheader("5. Top sản phẩm bị trả lại nhiều nhất")
returned = df[df['Quantity'] < 0]
returned_items = returned.groupby('Description')['Quantity'].sum().sort_values().head(10).reset_index()
fig5 = px.bar(returned_items, x='Description', y='Quantity', title="Top 10 sản phẩm bị trả lại nhiều nhất")
fig5.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig5, use_container_width=True)
