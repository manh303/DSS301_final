import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
try:
    from causalimpact import CausalImpact
    CAUSALIMPACT_AVAILABLE = True
except ImportError:
    CAUSALIMPACT_AVAILABLE = False
from controllers import causal_impact_controller
from models.models_causal import RevenueCausalImpactModel

def app(provided_df=None):
    st.title("📉 Phân tích ảnh hưởng của thay đổi giá đến doanh thu (CausalImpact)")
    
    if not CAUSALIMPACT_AVAILABLE:
        st.error("⚠️ Module 'causalimpact' không được cài đặt. Vui lòng cài đặt bằng lệnh: pip install causalimpact")
        st.info("Các chức năng khác vẫn hoạt động bình thường. Hãy thử các phân tích khác trong ứng dụng.")
        return

    uploaded_file = st.file_uploader("📂 Tải lên file CSV dữ liệu", type=["csv"])

    # Sử dụng DataFrame được cung cấp nếu không có file upload
    if uploaded_file:       
        df = pd.read_csv(uploaded_file)
    elif provided_df is not None:
        df = provided_df.copy()
        st.info("Đang sử dụng dữ liệu có sẵn. Bạn cũng có thể tải lên file CSV khác để phân tích.")
    else:
        st.warning("Vui lòng tải lên file CSV để bắt đầu phân tích.")
        return
        
    # Đổi tên cột cho đúng với model
    if 'Date' in df.columns:
        df.rename(columns={'Date': 'InvoiceDate'}, inplace=True)
    if 'Price' in df.columns:
        df.rename(columns={'Price': 'UnitPrice'}, inplace=True)
    if 'Product' in df.columns:
        df.rename(columns={'Product': 'StockCode'}, inplace=True)
    # Thêm cột Country mặc định nếu thiếu
    if 'Country' not in df.columns:
        df['Country'] = 'Default'
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df = df.sort_values('InvoiceDate')
    # Tính doanh thu nếu chưa có
    if 'Revenue' not in df.columns:
        df['Revenue'] = df['UnitPrice'] * df['Quantity']
    # Tổng hợp theo tháng (nếu dữ liệu theo ngày)
    df['Month'] = df['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
    monthly = df.groupby('Month').agg({'Revenue': 'sum', 'UnitPrice': 'mean'}).reset_index()
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
            monthly_adj.loc[change_idx+1:, 'UnitPrice'] = monthly_adj.loc[change_idx+1:, 'UnitPrice'] * change_factor

            # Chuẩn bị dữ liệu cho CausalImpact
            data = monthly_adj[['Revenue', 'UnitPrice']].copy()
            data = data.set_index(monthly_adj['Month'])
            data.index = pd.to_datetime(data.index)
            pre_period = [data.index[0].strftime('%Y-%m-%d'), data.index[change_idx].strftime('%Y-%m-%d')]
            post_period = [data.index[change_idx+1].strftime('%Y-%m-%d'), data.index[-1].strftime('%Y-%m-%d')]

            try:
                model = RevenueCausalImpactModel(df)
                model.process_data()
                # Ví dụ: chọn StockCode, Country, event_date từ giao diện hoặc mặc định
                stock_code = df['StockCode'].iloc[0]
                country = df['Country'].iloc[0]
                event_date = monthly['Month'].iloc[change_idx+1]  # hoặc chọn mốc phù hợp
                result, monthly = model.causal_impact(stock_code, country, event_date)
                # Sau khi chạy ci = CausalImpact(...)
                if result is not None:
                    st.subheader("Kết quả phân tích tác động (giả lập Causal Impact)")
                    st.write(f"Doanh thu trung bình trước sự kiện: {result['pre_mean']:.2f}")
                    st.write(f"Doanh thu trung bình sau sự kiện: {result['post_mean']:.2f}")
                    st.write(f"Chênh lệch tuyệt đối: {result['impact']:.2f}")
                    st.write(f"Chênh lệch tương đối: {result['impact_pct']:.2f}%")
                    st.write(f"p-value: {result['p_value']:.4f} {'(Có ý nghĩa)' if result['is_significant'] else '(Không có ý nghĩa)'}")
                else:
                    st.warning("Không đủ dữ liệu để phân tích.")

                # Vẽ biểu đồ doanh thu theo tháng
                fig, ax = plt.subplots()
                monthly.plot(x='Month', y='Revenue', ax=ax, marker='o')
                ax.axvline(event_date, color='red', linestyle='--', label='Event')
                ax.set_title('Doanh thu theo tháng')
                ax.legend()
                st.pyplot(fig)

                # Nhận xét và quyết định (giữ nguyên như trước)
                summary = model.summary_data if hasattr(model, 'summary_data') else None
                decision_main = ""
                decision_careful = ""
                decision_next = ""
                if summary is not None and 'actual' in summary.columns and 'pred' in summary.columns:
                    actual = summary.loc['post', 'actual']
                    pred = summary.loc['post', 'pred']
                    delta = actual - pred
                    p = model.p_value if hasattr(model, 'p_value') else None
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
