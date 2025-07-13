# models/data_models.py
import pandas as pd
import streamlit as st

@st.cache_data
def get_cached_data():
    df = pd.read_csv("online_retail.csv", encoding='ISO-8859-1')
    df.dropna(inplace=True)
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
    df['Year'] = df['InvoiceDate'].dt.year
    df['Month'] = df['InvoiceDate'].dt.month
    df['Day'] = df['InvoiceDate'].dt.day
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['Date'] = df['InvoiceDate'].dt.date
    return df
