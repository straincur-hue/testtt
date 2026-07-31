"""
건설공사비 지수 기반 물가 계산기
한국건설기술연구원 공표 건설공사비지수 활용 (기준년도: 2015=100)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from utils import (
    load_data,
    get_available_years,
    calculate_price_change,
    calculate_annual_average,
    calculate_yoy_change,
    calculate_mom_change,
    get_period_summary,
    filter_by_period,
    INDEX_COLUMNS,
)

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="건설공사비 지수 물가 계산기",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .metric-card {
        background: #f0f4ff;
        border-left: 4px solid #4f6ef7;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .metric-card h3 { margin: 0 0 4px 0; font-size: 0.85rem; color: #555; }
    .metric-card p  { margin: 0; font-size: 1.5rem; font-weight: 700; color: #222; }
    .positive { color: #e03e3e !important; }
    .negative { color: #1d7e3a !important; }
    .neutral  { color: #4f6ef7 !important; }
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a237e;
        border-bottom: 2px solid #e8eaf6;
        padding-bottom: 6px;
        margin-top: 8px;
        margin-bottom: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
@st.cache_data
def get_data(uploaded_file=None):
    return load_data(uploaded_file)


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/000000/crane.png", width=60
    )
    st.title("건설공사비\n물가 계산기")
    st.caption("기준년도: **2015 = 100**")
    st.divider()

    # 데이터 업로드
    st.markdown("#### 📂 데이터 파일")
    uploaded = st.file_uploader(
        "CSV 파일 업로드 (선택)",
        type=["csv"],
        help="기본 제공 데이터 대신 직접 CSV를 업로드할 수 있습니다.",
    )
    if uploaded:
        st.success("업로드된 파일 사용 중")

    st.divider()

    # 지수 항목 선택
    st.markdown("#### 📊 지수 항목")
    category_display = list(INDEX_COLUMNS.keys())
    selected_category = st.selectbox(
        "공사 유형",
        category_display,
        format_func=lambda x: x,
        help="계산에 사용할 건설공사비 지수 항목을 선택하세요.",
    )

    st.divider()
    st.caption(
        "출처: 한국건설기술연구원\n건설공사비지수 (KCCI)\n월별 공표"
    )

# ── 데이터 불러오기 ────────────────────────────────────────────────────────────
df = get_data(uploaded)
years = get_available_years(df)
cat = selected_category  # 내부 컬럼명

# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.title("🏗️ 건설공사비 지수 기반 물가 계산기")
st.markdown(
    "건설공사비지수(KCCI)를 활용하여 건설 공사비의 시점 간 물가 변동을 계산합니다. "
    f"**현재 선택 항목:** `{cat}` · **기준년도:** `2015 = 100`"
)
st.divider()

# ── 탭 구성 ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["💰 물가 계산", "📈 지수 추이", "📊 변동률 분석", "📋 데이터 조회"]
)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 : 물가 계산
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-header">시점 간 물가 변동 계산</p>', unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown("**📅 기준 시점 (계약·공사 시작 시점)**")
        b_col1, b_col2 = st.columns(2)
        base_year = b_col1.selectbox("연도", years, index=years.index(2020) if 2020 in years else 0, key="base_year")
        available_months_base = sorted(df[df["연도"] == base_year]["월"].tolist())
        base_month = b_col2.selectbox("월", available_months_base, key="base_month")

        st.markdown("**💵 원래 공사 금액**")
        amount_col1, amount_col2 = st.columns([3, 1])
        original_amount = amount_col1.number_input(
            "금액 입력",
            min_value=0.0,
            value=1_000_000_000.0,
            step=10_000_000.0,
            format="%.0f",
            label_visibility="collapsed",
        )
        unit = amount_col2.selectbox("단위", ["원", "천원", "백만원", "억원"], index=0, label_visibility="collapsed")

        # 단위 환산
        unit_multiplier = {"원": 1, "천원": 1_000, "백만원": 1_000_000, "억원": 100_000_000}
        amount_in_won = original_amount * unit_multiplier[unit]

    with col_r:
        st.markdown("**📅 비교 시점 (현재·정산 시점)**")
        t_col1, t_col2 = st.columns(2)
        target_year = t_col1.selectbox("연도", years, index=len(years) - 1, key="target_year")
        available_months_target = sorted(df[df["연도"] == target_year]["월"].tolist())
        target_month = t_col2.selectbox("월", available_months_target, index=len(available_months_target) - 1, key="target_month")

        st.markdown("**📝 계산 설명**")
        st.info(
            "건설공사비지수를 이용한 물가 변동 계산 공식:\n\n"
            "```\n조정 금액 = 원래 금액 × (비교시점 지수 / 기준시점 지수)\n```\n\n"
            "이는 계약금액 조정, 공사비 소급 산정, 설계변경 등에 활용됩니다.",
            icon="ℹ️",
        )

    st.divider()

    # ── 계산 실행 ──
    result = calculate_price_change(
        df,
        base_year, base_month,
        target_year, target_month,
        cat,
        amount_in_won,
    )

    if result is None:
        st.warning("선택한 기간의 데이터가 없습니다. 연도와 월을 다시 확인해 주세요.")
    else:
        # 방향 판단
        rate = result["change_rate"]
        rate_class = "positive" if rate > 0 else ("negative" if rate < 0 else "neutral")
        rate_arrow = "▲" if rate > 0 else ("▼" if rate < 0 else "─")

        # 금액 포맷 함수
        def fmt_won(v: float) -> str:
            if abs(v) >= 1e8:
                return f"{v/1e8:,.2f} 억원"
            elif abs(v) >= 1e6:
                return f"{v/1e6:,.2f} 백만원"
            elif abs(v) >= 1e3:
                return f"{v/1e3:,.1f} 천원"
            else:
                return f"{v:,.0f} 원"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="metric-card"><h3>기준 시점 지수</h3>'
                f'<p class="neutral">{result["base_index"]}</p></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="metric-card"><h3>비교 시점 지수</h3>'
                f'<p class="neutral">{result["target_index"]}</p></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="metric-card"><h3>물가 변동률</h3>'
                f'<p class="{rate_class}">{rate_arrow} {abs(rate):.2f}%</p></div>',
                unsafe_allow_html=True,
            )
        with c4:
            chg = result["change_amount"]
            chg_class = "positive" if chg > 0 else ("negative" if chg < 0 else "neutral")
            chg_arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "─")
            st.markdown(
                f'<div class="metric-card"><h3>증감 금액</h3>'
                f'<p class="{chg_class}">{chg_arrow} {fmt_won(abs(chg))}</p></div>',
                unsafe_allow_html=True,
            )

        st.divider()

        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            st.markdown("##### 📌 계산 결과 요약")
            summary_data = {
                "항목": ["공사 유형", "기준 시점", "비교 시점", "기준 시점 지수", "비교 시점 지수", "변동률", "원래 금액", "조정 후 금액", "증감 금액"],
                "값": [
                    cat,
                    f"{base_year}년 {base_month}월",
                    f"{target_year}년 {target_month}월",
                    str(result["base_index"]),
                    str(result["target_index"]),
                    f"{rate_arrow} {rate:.2f}%",
                    fmt_won(amount_in_won),
                    fmt_won(result["adjusted_amount"]),
                    f"{'+' if chg >= 0 else ''}{fmt_won(chg)}",
                ],
            }
            st.dataframe(
                pd.DataFrame(summary_data),
                hide_index=True,
                use_container_width=True,
            )

        with res_col2:
            st.markdown("##### 📊 금액 비교 차트")
            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        x=["원래 금액", "조정 후 금액"],
                        y=[amount_in_won / 1e8, result["adjusted_amount"] / 1e8],
                        marker_color=["#4f6ef7", "#e03e3e" if rate > 0 else "#1d7e3a"],
                        text=[fmt_won(amount_in_won), fmt_won(result["adjusted_amount"])],
                        textposition="outside",
                    )
                ]
            )
            fig_bar.update_layout(
                yaxis_title="금액 (억원)",
                height=300,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # 엑셀 다운로드
        result_df = pd.DataFrame([{
            "공사유형": cat,
            "기준시점": f"{base_year}-{base_month:02d}",
            "비교시점": f"{target_year}-{target_month:02d}",
            "기준지수": result["base_index"],
            "비교지수": result["target_index"],
            "변동률(%)": result["change_rate"],
            "원래금액(원)": amount_in_won,
            "조정금액(원)": result["adjusted_amount"],
            "증감금액(원)": result["change_amount"],
        }])
        st.download_button(
            "⬇️ 결과 CSV 다운로드",
            data=result_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"물가계산결과_{base_year}{base_month:02d}_{target_year}{target_month:02d}.csv",
            mime="text/csv",
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 : 지수 추이
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">건설공사비 지수 시계열 추이</p>', unsafe_allow_html=True)

    col_period1, col_period2, col_period3 = st.columns([2, 2, 2])
    with col_period1:
        s_year = st.selectbox("시작 연도", years, index=0, key="trend_sy")
    with col_period2:
        e_year = st.selectbox("종료 연도", years, index=len(years) - 1, key="trend_ey")
    with col_period3:
        show_all = st.multiselect(
            "표시 항목",
            list(INDEX_COLUMNS.keys()),
            default=["종합", "건축", "토목"],
        )

    if s_year > e_year:
        st.warning("시작 연도가 종료 연도보다 클 수 없습니다.")
    elif not show_all:
        st.info("표시할 항목을 하나 이상 선택하세요.")
    else:
        filtered = df[(df["연도"] >= s_year) & (df["연도"] <= e_year)]

        # 라인 차트
        fig_line = go.Figure()
        colors = px.colors.qualitative.Set2
        for i, col in enumerate(show_all):
            fig_line.add_trace(
                go.Scatter(
                    x=filtered["날짜"],
                    y=filtered[col],
                    name=col,
                    mode="lines",
                    line=dict(width=2, color=colors[i % len(colors)]),
                    hovertemplate="%{x|%Y년 %m월}<br>지수: %{y:.2f}<extra></extra>",
                )
            )

        # 기준선 (100)
        fig_line.add_hline(
            y=100,
            line_dash="dot",
            line_color="gray",
            annotation_text="기준 (2015=100)",
            annotation_position="bottom right",
        )

        fig_line.update_layout(
            title=f"건설공사비 지수 추이 ({s_year}~{e_year})",
            xaxis_title="시점",
            yaxis_title="지수 (2015=100)",
            hovermode="x unified",
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=60, b=40),
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # 연도별 평균 바 차트
        st.markdown("##### 연도별 평균 지수")
        annual_df = calculate_annual_average(filtered)
        fig_annual = go.Figure()
        for i, col in enumerate(show_all):
            fig_annual.add_trace(
                go.Bar(
                    x=annual_df["연도"],
                    y=annual_df[col],
                    name=col,
                    marker_color=colors[i % len(colors)],
                )
            )
        fig_annual.update_layout(
            barmode="group",
            xaxis_title="연도",
            yaxis_title="평균 지수",
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig_annual, use_container_width=True)

        # 기간 내 요약 통계
        st.markdown("##### 기간 내 요약 통계")
        summary_rows = []
        for col in show_all:
            subset = filtered[col]
            summary_rows.append({
                "항목": col,
                "최솟값": round(subset.min(), 2),
                "최댓값": round(subset.max(), 2),
                "평균": round(subset.mean(), 2),
                "표준편차": round(subset.std(), 2),
                "최고점 시점": filtered.loc[subset.idxmax(), "연월"],
                "최저점 시점": filtered.loc[subset.idxmin(), "연월"],
            })
        st.dataframe(
            pd.DataFrame(summary_rows),
            hide_index=True,
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 : 변동률 분석
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">변동률 분석</p>', unsafe_allow_html=True)

    change_type = st.radio(
        "변동률 유형",
        ["전년 동월 대비 (%)", "전월 대비 (%)"],
        horizontal=True,
    )

    yr_range = st.slider(
        "분석 연도 범위",
        min_value=min(years),
        max_value=max(years),
        value=(max(min(years), max(years) - 5), max(years)),
        key="change_slider",
    )

    cat_change = st.selectbox("분석 항목", list(INDEX_COLUMNS.keys()), key="change_cat")

    if change_type == "전년 동월 대비 (%)":
        change_df = calculate_yoy_change(df)
        change_col = f"{cat_change}_전년동월비"
        title_str = f"{cat_change} 전년 동월 대비 변동률 (%)"
    else:
        change_df = calculate_mom_change(df)
        change_col = f"{cat_change}_전월비"
        title_str = f"{cat_change} 전월 대비 변동률 (%)"

    filtered_chg = change_df[
        (change_df["연도"] >= yr_range[0]) & (change_df["연도"] <= yr_range[1])
    ].dropna(subset=[change_col])

    if filtered_chg.empty:
        st.info("해당 기간의 변동률 데이터가 없습니다.")
    else:
        # 색상 (양수=빨강, 음수=초록)
        bar_colors = [
            "#e03e3e" if v >= 0 else "#1d7e3a"
            for v in filtered_chg[change_col]
        ]

        fig_chg = go.Figure(
            go.Bar(
                x=filtered_chg["날짜"],
                y=filtered_chg[change_col],
                marker_color=bar_colors,
                hovertemplate="%{x|%Y년 %m월}<br>변동률: %{y:.2f}%<extra></extra>",
            )
        )
        fig_chg.add_hline(y=0, line_color="black", line_width=0.8)
        fig_chg.update_layout(
            title=title_str,
            xaxis_title="시점",
            yaxis_title="변동률 (%)",
            height=380,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig_chg, use_container_width=True)

        # 히트맵 - 연도×월 변동률
        st.markdown("##### 연도×월 변동률 히트맵")
        pivot_df = filtered_chg.pivot_table(
            index="연도", columns="월", values=change_col
        )
        month_labels = {i: f"{i}월" for i in range(1, 13)}
        pivot_df.columns = [month_labels.get(c, c) for c in pivot_df.columns]

        fig_heat = px.imshow(
            pivot_df,
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
            labels=dict(color="변동률(%)"),
            title="연도×월 변동률 히트맵",
        )
        fig_heat.update_layout(height=320, margin=dict(t=50, b=40))
        st.plotly_chart(fig_heat, use_container_width=True)

        # 최대·최소 구간
        max_idx = filtered_chg[change_col].idxmax()
        min_idx = filtered_chg[change_col].idxmin()
        mcol1, mcol2 = st.columns(2)
        mcol1.metric(
            "최대 상승 구간",
            f"{filtered_chg.loc[max_idx, '연월']}",
            f"+{filtered_chg.loc[max_idx, change_col]:.2f}%",
        )
        mcol2.metric(
            "최대 하락 구간",
            f"{filtered_chg.loc[min_idx, '연월']}",
            f"{filtered_chg.loc[min_idx, change_col]:.2f}%",
            delta_color="inverse",
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 : 데이터 조회
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-header">원시 데이터 조회 및 다운로드</p>', unsafe_allow_html=True)

    dc1, dc2, dc3, dc4 = st.columns(4)
    d_sy = dc1.selectbox("시작 연도", years, index=0, key="data_sy")
    d_sm = dc2.selectbox("시작 월", list(range(1, 13)), index=0, key="data_sm")
    d_ey = dc3.selectbox("종료 연도", years, index=len(years) - 1, key="data_ey")
    d_em = dc4.selectbox("종료 월", list(range(1, 13)), index=11, key="data_em")

    display_df = filter_by_period(df, d_sy, d_sm, d_ey, d_em)
    show_cols = ["연월"] + list(INDEX_COLUMNS.keys())
    display_df_show = display_df[show_cols].reset_index(drop=True)

    st.markdown(f"**총 {len(display_df_show)}건**")
    st.dataframe(
        display_df_show,
        use_container_width=True,
        height=400,
    )

    csv_data = display_df_show.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ 데이터 CSV 다운로드",
        data=csv_data,
        file_name=f"건설공사비지수_{d_sy}{d_sm:02d}_{d_ey}{d_em:02d}.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("##### 데이터 출처 및 안내")
    st.markdown(
        """
        - **출처**: 한국건설기술연구원(KICT) 건설공사비지수(KCCI)
        - **기준년도**: 2015년 = 100
        - **공표 주기**: 월별
        - **항목**: 종합 / 건축(주거용·비주거용) / 토목 / 기계설비
        - **활용**: 계약금액 조정, 공사비 소급 산정, 설계변경, 원가 분석 등
        - **공식 데이터**: [KOSIS 국가통계포털](https://kosis.kr) 또는 [한국건설기술연구원](https://www.kict.re.kr) 에서 최신 데이터를 다운로드하여 업로드 기능으로 사용하세요.
        """
    )
