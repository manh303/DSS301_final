import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from causalimpact import CausalImpact
from controllers import causal_impact_controller

def app():
    st.title("📉 Phân tích ảnh hưởng của thay đổi giá đến doanh thu (CausalImpact)")

    uploaded_file = st.file_uploader("📂 Tải lên file CSV dữ liệu", type=["csv"])

    if uploaded_file:       
        df = pd.read_csv(uploaded_file)
        # Đổi tên cột cho đồng nhất
        if 'InvoiceDate' in df.columns:
            df.rename(columns={'InvoiceDate': 'Date'}, inplace=True)
        if 'UnitPrice' in df.columns:
            df.rename(columns={'UnitPrice': 'Price'}, inplace=True)
        if 'StockCode' in df.columns:
            df.rename(columns={'StockCode': 'Product'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        # Tính doanh thu nếu chưa có
        if 'Revenue' not in df.columns:
            df['Revenue'] = df['Price'] * df['Quantity']
        # Tổng hợp theo tháng (nếu dữ liệu theo ngày)
        df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()
        monthly = df.groupby('Month').agg({'Revenue': 'sum', 'Price': 'mean'}).reset_index()
        st.write("Dữ liệu tổng hợp theo tháng:")
        st.dataframe(monthly)

        # Người dùng chọn mức tăng/giảm giá (chỉ các mức 10, 20, 30, 40%)
        percent_options = [-40, -30, -20, -10, 10, 20, 30, 40]
        percent_label = st.selectbox(
            "Chọn mức thay đổi giá (%)",
            [f"Giảm {abs(x)}%" if x < 0 else f"Tăng {x}%" for x in percent_options]
        )
        percent_change = int(percent_label.replace("Tăng ", "").replace("Giảm ", "-").replace("%", ""))
        change_factor = 1 + percent_change / 100

        # Chọn thời điểm thay đổi giá
        month_labels = monthly['Month'].dt.strftime('%m/%Y').tolist()
        change_month = st.selectbox("📅 Chọn tháng bắt đầu thay đổi giá", month_labels)
        change_idx = month_labels.index(change_month)
        if change_idx + 1 >= len(monthly):
            st.error("⚠️ Không có dữ liệu sau tháng thay đổi giá được chọn. Hãy chọn mốc thời gian sớm hơn.")
            st.stop()

        st.write(f"Giai đoạn trước thay đổi giá: {monthly['Month'].iloc[0].strftime('%Y-%m-%d')} đến {monthly['Month'].iloc[change_idx].strftime('%Y-%m-%d')}")
        st.write(f"Giai đoạn sau thay đổi giá: {monthly['Month'].iloc[change_idx+1].strftime('%Y-%m-%d')} đến {monthly['Month'].iloc[-1].strftime('%Y-%m-%d')}")

        if st.button("🚀 Phân tích tác động với mức thay đổi giá đã chọn"):
            if change_idx < 2:
                st.error("⚠️ Giai đoạn trước thay đổi giá phải có ít nhất 3 tháng.")
            else:
                st.markdown(f"---\n### Kịch bản: **{'Tăng' if percent_change > 0 else 'Giảm' if percent_change < 0 else 'Không đổi'} {abs(percent_change)}%**")
                # Áp dụng thay đổi giá vào dữ liệu
                monthly_adj = monthly.copy()
                monthly_adj.loc[change_idx+1:, 'Price'] = monthly_adj.loc[change_idx+1:, 'Price'] * change_factor

                # Chuẩn bị dữ liệu cho CausalImpact
                data = monthly_adj[['Revenue', 'Price']].copy()
                data = data.set_index(monthly_adj['Month'])
                data.index = pd.to_datetime(data.index)
                pre_period = [data.index[0].strftime('%Y-%m-%d'), data.index[change_idx].strftime('%Y-%m-%d')]
                post_period = [data.index[change_idx+1].strftime('%Y-%m-%d'), data.index[-1].strftime('%Y-%m-%d')]

                try:
                    ci = CausalImpact(data, pre_period, post_period)
                    # Sau khi chạy ci = CausalImpact(...)
                    summary = ci.summary_data if hasattr(ci, 'summary_data') else None
                    if summary is not None and 'actual' in summary.columns and 'pred' in summary.columns:
                        actual = summary.loc['post', 'actual']
                        pred = summary.loc['post', 'pred']
                        abs_effect = summary.loc['post', 'abs_effect']
                        rel_effect = summary.loc['post', 'rel_effect']
                        abs_ci = summary.loc['post', 'abs_effect_ci'] if 'abs_effect_ci' in summary.columns else (np.nan, np.nan)
                        rel_ci = summary.loc['post', 'rel_effect_ci'] if 'rel_effect_ci' in summary.columns else (np.nan, np.nan)
                        p = ci.p_value if hasattr(ci, 'p_value') else None

                        # Tạo bảng phân tích
                        table_data = {
                            "Chỉ số": [
                                "Doanh thu thực tế sau can thiệp",
                                "Doanh thu dự báo nếu không can thiệp",
                                "Hiệu số tuyệt đối",
                                "Khoảng tin cậy 95% (hiệu số tuyệt đối)",
                                "Hiệu số tương đối",
                                "Khoảng tin cậy 95% (hiệu số tương đối)",
                                "p-value"
                            ],
                            "Giá trị": [
                                f"{actual:,.0f}",
                                f"{pred:,.0f}",
                                f"{abs_effect:,.0f}",
                                f"[{abs_ci[0]:,.0f}, {abs_ci[1]:,.0f}]" if isinstance(abs_ci, (list, tuple, np.ndarray)) else "-",
                                f"{rel_effect*100:.2f}%",
                                f"[{rel_ci[0]*100:.2f}%, {rel_ci[1]*100:.2f}%]" if isinstance(rel_ci, (list, tuple, np.ndarray)) else "-",
                                f"{p:.3f}" if p is not None else "-"
                            ]
                        }
                        st.subheader("Bảng phân tích kết quả tác động")
                        st.table(pd.DataFrame(table_data))

                        st.markdown(f"""
                        **Kết quả phân tích tác động (Causal Impact):**
                        - **Giá trị thực tế trung bình sau can thiệp:** {actual:,.2f}
                        - **Giá trị dự báo trung bình nếu không can thiệp:** {pred:,.2f}
                        - **Hiệu số tuyệt đối:** {abs_effect:,.2f} (Khoảng tin cậy 95%: {abs_ci})
                        - **Hiệu số tương đối:** {rel_effect:.2%} (Khoảng tin cậy 95%: {rel_ci})
                        - **p-value:** {p:.2g} {'(Có ý nghĩa thống kê)' if p is not None and p < 0.05 else '(Không có ý nghĩa thống kê)'}
                        """)
                    else:
                        st.warning("Không thể trích xuất kết quả phân tích chi tiết.")
                    ci.plot()
                    fig = plt.gcf()
                    st.pyplot(fig)

                    # Nhận xét và quyết định (giữ nguyên như trước)
                    summary = ci.summary_data if hasattr(ci, 'summary_data') else None
                    decision_main = ""
                    decision_careful = ""
                    decision_next = ""
                    if summary is not None and 'actual' in summary.columns and 'pred' in summary.columns:
                        actual = summary.loc['post', 'actual']
                        pred = summary.loc['post', 'pred']
                        delta = actual - pred
                        p = ci.p_value if hasattr(ci, 'p_value') else None
                        if p is not None and p < 0.05:
                            if delta > 0:
                                st.success("Giá mới giúp TĂNG doanh thu một cách có ý nghĩa thống kê.")
                                decision_main = "QUYẾT ĐỊNH 1: Ưu tiên tăng giá để tối ưu hóa doanh thu trong giai đoạn này."
                                decision_careful = "QUYẾT ĐỊNH 2: Đánh giá tác động lâu dài của việc tăng giá đến sự hài lòng và giữ chân khách hàng."
                                decision_next = "QUYẾT ĐỊNH 3: Xây dựng kế hoạch truyền thông để giải thích lý do tăng giá cho khách hàng."
                            else:
                                st.warning("Giá mới làm GIẢM doanh thu một cách có ý nghĩa thống kê.")
                                decision_main = "QUYẾT ĐỊNH 1: Tránh giảm giá sâu, ưu tiên giữ giá ổn định để bảo vệ doanh thu."
                                decision_careful = "QUYẾT ĐỊNH 2: Phân tích lại cấu trúc chi phí để tìm giải pháp tăng lợi nhuận mà không cần giảm giá."
                                decision_next = "QUYẾT ĐỊNH 3: Thử nghiệm các chương trình khuyến mãi thay vì giảm giá trực tiếp."
                        else:
                            st.info("Không có bằng chứng rõ ràng rằng thay đổi giá đã tạo ra sự thay đổi đáng kể về doanh thu.")
                            decision_main = "QUYẾT ĐỊNH 1: Duy trì mức giá hiện tại trong ngắn hạn."
                            decision_careful = "QUYẾT ĐỊNH 2: Tăng cường khảo sát thị trường để hiểu rõ hơn về hành vi khách hàng."
                            decision_next = "QUYẾT ĐỊNH 3: Đầu tư vào hoạt động marketing để thúc đẩy doanh thu mà không cần thay đổi giá."
                    # Nếu không thể trích xuất chỉ số cơ bản thì KHÔNG hiển thị 3 quyết định về dữ liệu nữa
                    st.subheader("Đưa ra Quyết định")
                    st.markdown(f"Dựa trên phân tích lịch sử, hãy chọn chiến lược tiếp theo cho sản phẩm này (áp dụng từ {monthly['Month'].iloc[change_idx+1].strftime('%d/%m/%Y')}):")

                    # Define decision scenarios and options
                    decision_scenarios = {
                        -10: [ # giảm 10%
                            {
                                "label": "Tiếp tục giảm giá 10% thêm 1 tháng nữa",
                                "loi_ich": "Duy trì đà tăng doanh thu, thu hút thêm khách hàng mới.",
                                "rui_ro": "Lợi nhuận trên mỗi đơn vị giảm, có thể ảnh hưởng dài hạn."
                            },
                            {
                                "label": "Giữ giá giảm 10% và kết hợp khuyến mãi (mua 2 tặng 1)",
                                "loi_ich": "Tăng số lượng bán, kích thích khách hàng mua nhiều hơn.",
                                "rui_ro": "Có thể giảm biên lợi nhuận nếu khách hàng chỉ mua khi có khuyến mãi."
                            },
                            {
                                "label": "Quay lại giá gốc, theo dõi doanh thu 2 tuần rồi đánh giá lại",
                                "loi_ich": "Bảo toàn lợi nhuận, kiểm soát tác động lâu dài.",
                                "rui_ro": "Có thể mất khách hàng đã quen với giá thấp."
                            }
                        ],
                        10: [ # tăng 10%
                            {
                                "label": "Tiếp tục tăng giá 10% thêm 1 tháng",
                                "loi_ich": "Tối ưu hóa lợi nhuận trên mỗi đơn vị bán.",
                                "rui_ro": "Có thể giảm số lượng bán nếu khách hàng nhạy cảm với giá."
                            },
                            {
                                "label": "Kết hợp tăng giá 10% với nâng cao chất lượng dịch vụ",
                                "loi_ich": "Tăng giá trị cảm nhận, giữ chân khách hàng trung thành.",
                                "rui_ro": "Chi phí nâng cấp dịch vụ có thể làm giảm lợi nhuận."
                            },
                            {
                                "label": "Giữ giá tăng 10% trong 2 tuần, sau đó khảo sát ý kiến khách hàng",
                                "loi_ich": "Đánh giá thực tế tác động của tăng giá.",
                                "rui_ro": "Nếu phản hồi tiêu cực, cần điều chỉnh kịp thời."
                            }
                        ],
                        -20: [ # giảm 20%
                            {
                                "label": "Tiếp tục giảm giá 20% thêm 2 tuần",
                                "loi_ich": "Đẩy mạnh xả hàng tồn, tăng doanh số ngắn hạn.",
                                "rui_ro": "Lợi nhuận giảm mạnh, nguy cơ phá giá thị trường."
                            },
                            {
                                "label": "Giữ giá giảm 20% và tặng kèm sản phẩm phụ",
                                "loi_ich": "Tăng giá trị đơn hàng, tạo sự khác biệt với đối thủ.",
                                "rui_ro": "Chi phí tặng phẩm có thể làm giảm lợi nhuận tổng thể."
                            },
                            {
                                "label": "Tăng giá trở lại mức giảm 10% và đánh giá phản ứng khách hàng",
                                "loi_ich": "Tăng dần lợi nhuận, kiểm soát tác động tiêu cực.",
                                "rui_ro": "Khách hàng có thể phản ứng tiêu cực với việc tăng giá lại."
                            }
                        ],
                        20: [ # tăng 20%
                            {
                                "label": "Tiếp tục tăng giá 20% thêm 2 tuần",
                                "loi_ich": "Tối đa hóa lợi nhuận nếu thị trường chấp nhận.",
                                "rui_ro": "Nguy cơ mất khách hàng nhạy cảm về giá."
                            },
                            {
                                "label": "Tăng giá 20% và triển khai chương trình khách hàng thân thiết",
                                "loi_ich": "Giữ chân khách hàng trung thành, tăng giá trị lâu dài.",
                                "rui_ro": "Chi phí chương trình có thể làm giảm lợi nhuận ngắn hạn."
                            },
                            {
                                "label": "Giảm giá lại về mức tăng 10% nếu doanh số giảm mạnh",
                                "loi_ich": "Linh hoạt điều chỉnh theo thị trường.",
                                "rui_ro": "Khách hàng có thể chờ giảm giá tiếp, ảnh hưởng tâm lý mua hàng."
                            }
                        ],
                        -30: [ # giảm 30%
                            {
                                "label": "Tiếp tục giảm giá 30% thêm 1 tháng",
                                "loi_ich": "Duy trì đà tăng doanh thu, thu hút thêm khách hàng mới.",
                                "rui_ro": "Lợi nhuận trên mỗi đơn vị giảm, có thể ảnh hưởng dài hạn."
                            },
                            {
                                "label": "Giữ giá giảm 30% và kết hợp khuyến mãi (mua 2 tặng 1)",
                                "loi_ich": "Tăng số lượng bán, kích thích khách hàng mua nhiều hơn.",
                                "rui_ro": "Có thể giảm biên lợi nhuận nếu khách hàng chỉ mua khi có khuyến mãi."
                            },
                            {
                                "label": "Quay lại giá gốc, theo dõi doanh thu 2 tuần rồi đánh giá lại",
                                "loi_ich": "Bảo toàn lợi nhuận, kiểm soát tác động lâu dài.",
                                "rui_ro": "Có thể mất khách hàng đã quen với giá thấp."
                            }
                        ],
                        30: [ # tăng 30%
                            {
                                "label": "Tiếp tục tăng giá 30% thêm 1 tháng",
                                "loi_ich": "Tối ưu hóa lợi nhuận trên mỗi đơn vị bán.",
                                "rui_ro": "Có thể giảm số lượng bán nếu khách hàng nhạy cảm với giá."
                            },
                            {
                                "label": "Kết hợp tăng giá 30% với nâng cao chất lượng dịch vụ",
                                "loi_ich": "Tăng giá trị cảm nhận, giữ chân khách hàng trung thành.",
                                "rui_ro": "Chi phí nâng cấp dịch vụ có thể làm giảm lợi nhuận."
                            },
                            {
                                "label": "Giữ giá tăng 30% trong 2 tuần, sau đó khảo sát ý kiến khách hàng",
                                "loi_ich": "Đánh giá thực tế tác động của tăng giá.",
                                "rui_ro": "Nếu phản hồi tiêu cực, cần điều chỉnh kịp thời."
                            }
                        ],
                        -40: [ # giảm 40%
                            {
                                "label": "Tiếp tục giảm giá 40% thêm 1 tháng",
                                "loi_ich": "Duy trì đà tăng doanh thu, thu hút thêm khách hàng mới.",
                                "rui_ro": "Lợi nhuận trên mỗi đơn vị giảm, có thể ảnh hưởng dài hạn."
                            },
                            {
                                "label": "Giữ giá giảm 40% và kết hợp khuyến mãi (mua 2 tặng 1)",
                                "loi_ich": "Tăng số lượng bán, kích thích khách hàng mua nhiều hơn.",
                                "rui_ro": "Có thể giảm biên lợi nhuận nếu khách hàng chỉ mua khi có khuyến mãi."
                            },
                            {
                                "label": "Quay lại giá gốc, theo dõi doanh thu 2 tuần rồi đánh giá lại",
                                "loi_ich": "Bảo toàn lợi nhuận, kiểm soát tác động lâu dài.",
                                "rui_ro": "Có thể mất khách hàng đã quen với giá thấp."
                            }
                        ],
                        40: [ # tăng 40%
                            {
                                "label": "Tiếp tục tăng giá 40% thêm 1 tháng",
                                "loi_ich": "Tối đa hóa lợi nhuận nếu thị trường chấp nhận.",
                                "rui_ro": "Nguy cơ mất khách hàng nhạy cảm về giá."
                            },
                            {
                                "label": "Tăng giá 40% và triển khai chương trình khách hàng thân thiết",
                                "loi_ich": "Giữ chân khách hàng trung thành, tăng giá trị lâu dài.",
                                "rui_ro": "Chi phí chương trình có thể làm giảm lợi nhuận ngắn hạn."
                            },
                            {
                                "label": "Giảm giá lại về mức tăng 10% nếu doanh số giảm mạnh",
                                "loi_ich": "Linh hoạt điều chỉnh theo thị trường.",
                                "rui_ro": "Khách hàng có thể chờ giảm giá tiếp, ảnh hưởng tâm lý mua hàng."
                            }
                        ]
                    }

                    # Get options for the specific percent_change
                    options = decision_scenarios.get(percent_change, [
                        {
                            "label": "Không thực hiện thay đổi giá trong giai đoạn này.",
                            "loi_ich": "Duy trì mức giá hiện tại trong ngắn hạn.",
                            "rui_ro": "Không có tác động đáng kể đến doanh thu."
                        }
                    ])

                    choices = [f"{opt['label']}\nLợi ích: {opt['loi_ich']}\nRủi ro: {opt['rui_ro']}" for opt in options]
                    selected = st.radio("Chọn phương án:", choices)

                    if st.button("Xác nhận Quyết định"):
                        st.success(f"Bạn đã chọn: {selected.splitlines()[0]}")
                except Exception as e:
                    st.error(f"Lỗi khi chạy Causal Impact cho kịch bản {percent_change}%: {e}")

    else:
        st.info("Vui lòng tải lên file CSV có các cột: Date, Price, Quantity (và Revenue nếu có).")
