import pandas as pd

def preprocess_uploaded_file(uploaded_file):
    df = pd.read_csv(uploaded_file)

    if 'InvoiceDate' in df.columns:
        df.rename(columns={'InvoiceDate': 'Date'}, inplace=True)
    if 'UnitPrice' in df.columns:
        df.rename(columns={'UnitPrice': 'Price'}, inplace=True)
    if 'StockCode' in df.columns:
        df.rename(columns={'StockCode': 'Product'}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    if 'Revenue' not in df.columns:
        df['Revenue'] = df['Price'] * df['Quantity']

    df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    monthly = df.groupby('Month').agg({
        'Revenue': 'sum',
        'Price': 'mean'
    }).reset_index()

    return df, monthly
