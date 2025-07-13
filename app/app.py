# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import datetime

st.set_page_config(page_title="RFM Clustering DSS", layout="wide")

# 0. File uploader
st.sidebar.title("Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload your online_retail.csv", type="csv"
)
if uploaded_file is None:
    st.sidebar.warning("Please upload the Online Retail CSV to continue.")
    st.stop()

@st.cache_data
def load_data(file_obj):
    df = pd.read_csv(file_obj, encoding="ISO-8859-1", parse_dates=["InvoiceDate"])
    # Keep only real sales
    df = df[df.Quantity > 0]
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int)
    df["Country"] = df["Country"].astype(str)
    return df

df = load_data(uploaded_file)

# Initialize step
if "step" not in st.session_state:
    st.session_state.step = 1

def screen1():
    st.title("Step 1: Configure RFM Clustering")
    # Reference date
    default_date = datetime.date(2011, 12, 31)
    ref_date = st.date_input(
        "Reference date for Recency calculation", value=default_date
    )
    # Region filter
    countries = sorted(df["Country"].unique())
    selected_countries = st.multiselect(
        "Filter by Country (blank = all)", countries, default=countries
    )
    # Number of clusters
    k = st.slider("Number of clusters (k)", 2, 10, 3)

    # Store in session
    st.session_state.ref_date = ref_date
    st.session_state.selected_countries = selected_countries
    st.session_state.k = k

    if st.button("Next →"):
        st.session_state.step = 2

def screen2():
    st.title("Step 2: RFM & Cluster Results")
    st.markdown(f"**Reference date:** {st.session_state.ref_date}")
    st.markdown(f"**Countries:** {', '.join(st.session_state.selected_countries)}")
    st.markdown(f"**Clusters (k):** {st.session_state.k}")

    # Filter and compute RFM
    df_filt = df[df["Country"].isin(st.session_state.selected_countries)]
    snapshot = pd.to_datetime(st.session_state.ref_date)
    rfm = (
        df_filt.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Quantity", lambda q: (q * df_filt.loc[q.index, "UnitPrice"]).sum())
        )
        .reset_index()
    )

    st.subheader("RFM Table (first 10 rows)")
    st.dataframe(rfm.head(10), use_container_width=True)

    # Standardize and cluster
    scaler = StandardScaler()
    X = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
    model = KMeans(n_clusters=st.session_state.k, random_state=42)
    rfm["Cluster"] = model.fit_predict(X)

    # Summary
    summary = (
        rfm.groupby("Cluster")
        .agg(
            Count=("CustomerID", "count"),
            AvgRecency=("Recency", "mean"),
            AvgFreq=("Frequency", "mean"),
            AvgMon=("Monetary", "mean")
        )
        .reset_index()
        .sort_values("Cluster")
    )
    st.subheader("Cluster Summary")
    st.table(summary)

    st.subheader("Cluster Sizes")
    st.bar_chart(summary.set_index("Cluster")["Count"])

    st.subheader("Recency vs Monetary Scatter")
    fig, ax = plt.subplots(figsize=(6,4))
    scatter = ax.scatter(
        rfm["Recency"], rfm["Monetary"],
        c=rfm["Cluster"], cmap="tab10", alpha=0.6
    )
    ax.set_xlabel("Recency (days)")
    ax.set_ylabel("Monetary (£)")
    ax.set_title("R vs. M by Cluster")
    ax.legend(*scatter.legend_elements(), title="Cluster")
    st.pyplot(fig)

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state.step = 1
    if col2.button("Finish"):
        st.session_state.step = 3

def screen3():
    st.title("Step 3: Interpreting Your Segments")
    st.subheader("Cluster Definitions")
    st.markdown("""
    - **Cluster 0:** Loyal (low Recency, high Frequency & Monetary)  
    - **Cluster 1:** At-Risk (high Recency, low Frequency & Monetary)  
    - **Cluster 2:** Potential (medium Recency/Frequency/Monetary)  
    """)
    # Quintiles for RFM
    rfm_all = (
        df.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda x: (pd.to_datetime(st.session_state.ref_date) - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Quantity", lambda q: (q * df.loc[q.index, "UnitPrice"]).sum())
        )
        .reset_index()
    )
    quintiles = pd.DataFrame({
        "Metric": ["Recency","Frequency","Monetary"],
        "20th pct": [
            rfm_all.Recency.quantile(0.2),
            rfm_all.Frequency.quantile(0.2),
            rfm_all.Monetary.quantile(0.2)
        ],
        "80th pct": [
            rfm_all.Recency.quantile(0.8),
            rfm_all.Frequency.quantile(0.8),
            rfm_all.Monetary.quantile(0.8)
        ]
    })
    st.subheader("RFM Quintile Cutoffs")
    st.table(quintiles)

    st.subheader("Recommended Actions")
    st.markdown("""
    - **Loyal:** VIP loyalty program, exclusive rewards.  
    - **Potential:** Product recommendations, small discounts.  
    - **At-Risk:** Win-back emails, higher incentives.  
    """)
    if st.button("Restart"):
        st.session_state.step = 1

# Route screens
if st.session_state.step == 1:
    screen1()
elif st.session_state.step == 2:
    screen2()
else:
    screen3()
