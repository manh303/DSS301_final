import streamlit as st
import streamlit.components.v1 as components

from controllers.main_controller import MainController
from views.price_quantity_view import render_price_quantity_analysis
from views.warehouse_view import render_warehouse_analysis
from views.causal_impact_view import app as causal_impact_app
from views.product_forecast_view import render_product_forecast_analysis
from models.rfm_model import RFMModel
from models.data_model import get_cached_data

def home():
    if "modal_type" not in st.session_state:
        st.session_state.modal_type = ""

    st.set_page_config(page_title="Invoice Analysis Dashboard", layout="wide")

    with st.container():
        st.markdown("""
            <div style='text-align:center; padding:20px;'>
                <h1 style='color:#0E1117; font-size: 36px;'>📊 Hệ thống Dashboard Phân tích Đơn hàng</h1>
                <p style='font-size:18px; color: #555;'>Khám phá sâu hơn dữ liệu kinh doanh của bạn với các mô hình phân tích thông minh</p>
            </div>
        """, unsafe_allow_html=True)
    
    df = get_cached_data()

    with st.container():
        st.markdown("""
            <style>
                .model-card {
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                    transition: 0.3s ease;
                }
                .model-card:hover {
                    background-color: #f1f1f1;
                }
                .model-title {
                    font-size: 20px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.subheader("🔍 Chọn mô hình để phân tích")
        col1, col2 = st.columns(2)

        with col1:
            with st.container():
                st.markdown("<div class='model-card'><div class='model-title'>📦 Phân tích Kho hàng & Tối ưu tồn kho</div>", unsafe_allow_html=True)
                if st.button("Bắt đầu", key="warehouse"):
                    st.session_state.modal_type = "warehouse"
                st.markdown("</div>", unsafe_allow_html=True)

            with st.container():
                st.markdown("<div class='model-card'><div class='model-title'>📉 Phân tích Tác động (Causal Impact)</div>", unsafe_allow_html=True)
                if st.button("Bắt đầu", key="causal"):
                    st.session_state.modal_type = "causal_impact"
                st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown("<div class='model-card'><div class='model-title'>👥 Phân tích RFM</div>", unsafe_allow_html=True)
                if st.button("Bắt đầu", key="rfm"):
                    st.session_state.modal_type = "rfm"
                st.markdown("</div>", unsafe_allow_html=True)

            with st.container():
                st.markdown("<div class='model-card'><div class='model-title'>💰 Phân tích Giá & Số lượng</div>", unsafe_allow_html=True)
                if st.button("Bắt đầu", key="price_quantity"):
                    st.session_state.modal_type = "price_quantity"
                st.markdown("</div>", unsafe_allow_html=True)

            with st.container():
                st.markdown("<div class='model-card'><div class='model-title'>📈 Dự báo Doanh thu Sản phẩm</div>", unsafe_allow_html=True)
                if st.button("Bắt đầu", key="product_forecast"):
                    st.session_state.modal_type = "product_forecast"
                st.markdown("</div>", unsafe_allow_html=True)

    modal_type = st.session_state.modal_type
    if modal_type:
        show_modal(modal_type, df)

def show_modal(modal_type, df):
    modal_title = {
        "rfm": "👥 Phân tích RFM",
        "price_quantity": "💰 Phân tích Giá & Số lượng",
        "warehouse": "📦 Tối ưu Kho hàng",
        "causal_impact": "📉 Phân tích Tác động",
        "product_forecast": "📈 Dự báo Doanh thu Sản phẩm"
    }

    modal_func = {
        "price_quantity": render_price_quantity_analysis,
        "warehouse": render_warehouse_analysis,
        "causal_impact": causal_impact_app,
        "product_forecast": render_product_forecast_analysis
    }

    components.html("""
        <style>
        .overlay {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.6);
            z-index: 1000;
        }
        </style>
        <div class="overlay"></div>
    """, height=0)

    st.markdown(f"## {modal_title[modal_type]}")
    st.markdown("### 🔽 Dữ liệu phân tích:")

    try:
        if modal_type == "rfm":
            controller = MainController()
            controller.run()
        else:
            modal_func[modal_type](df)
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi hiển thị mô hình '{modal_type}': {e}")

    st.markdown("---")
    if st.button("❌ Đóng phân tích"):
        st.session_state.modal_type = ""
