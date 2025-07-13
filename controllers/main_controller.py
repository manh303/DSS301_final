import streamlit as st
import pandas as pd
from models.rfm_model import RFMModel
from views.ui import UIView

class MainController:
    """Controller class for application flow control"""

    def __init__(self):
        """Initialize controller with model and view"""
        self.model = RFMModel()
        self.view = UIView()

    def run(self):
        """
        Run the main application and handle navigation
        """
        # Initialize session state if needed
        if 'screen' not in st.session_state:
            st.session_state.screen = 'upload'

        # Route based on current screen
        if st.session_state.screen == 'upload':
            self.upload_screen()
        elif st.session_state.screen == 'analysis':
            self.analysis_screen()

    def upload_screen(self):
        """
        Handle data upload and configuration screen
        """
        # Display upload page and get configuration
        df, k, ref_date, country_filter, revenue_target = self.view.upload_page()

        if df is not None:
            # Save input configuration to session state for next screen
            st.session_state.df = df
            st.session_state.k = k
            st.session_state.ref_date = pd.to_datetime(ref_date)
            st.session_state.latest_date = ref_date
            st.session_state.country_filter = country_filter
            st.session_state.revenue_target = revenue_target

    def analysis_screen(self):
        """
        Handle analysis and action planning screen
        """
        try:
            # Get processed results from session state
            df_rfm = st.session_state.df_rfm
            summary_df = st.session_state.summary_df
            monthly_revenue = st.session_state.monthly_revenue
            revenue_target = st.session_state.revenue_target
            latest_date = st.session_state.latest_date

            # Display analysis page
            self.view.analysis_page(
                df_rfm,
                summary_df,
                revenue_target,
                latest_date,
                monthly_revenue
            )
        except Exception as e:
            self.view.show_error(f"Lỗi khi hiển thị phân tích: {str(e)}")
            st.button("⬅️ Quay lại", on_click=self._reset_to_upload)

    def _reset_to_upload(self):
        """Reset to upload screen"""
        st.session_state.screen = 'upload'
        st.rerun()
