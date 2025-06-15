from fpdf import FPDF
import pandas as pd
import os

os.makedirs("/app/output", exist_ok=True)

# Load và xử lý dữ liệu
df = pd.read_csv("/data/online_retail.csv", parse_dates=["InvoiceDate"])
df.dropna(inplace=True)
df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
revenue_by_country = df.groupby("Country")["TotalPrice"].sum().sort_values(ascending=False)

# Tạo PDF với fpdf2 + font Unicode
pdf = FPDF()
pdf.add_page()

# Add font Unicode
pdf.add_font("DejaVu", "", "/app/app/DejaVuSans.ttf", uni=True)
pdf.set_font("DejaVu", size=12)

pdf.cell(200, 10, txt="Báo cáo Tổng doanh thu theo quốc gia", ln=True, align="C")

pdf.set_font("DejaVu", size=11)
for country, total in revenue_by_country.items():
    pdf.cell(200, 10, txt=f"{country}: {total:,.2f}", ln=True)

pdf.output("/app/output/baocao_doanhthu.pdf")
