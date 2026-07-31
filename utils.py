"""
건설공사비 지수 데이터 처리 유틸리티 모듈
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 기준년도 (2015 = 100)
BASE_YEAR = 2015

# 데이터 파일 경로
DATA_PATH = Path(__file__).parent / "data" / "construction_cost_index.csv"

# 지수 항목 한글명 매핑
INDEX_COLUMNS = {
    "종합": "종합",
    "건축": "건축 (합계)",
    "주거용건축": "건축 > 주거용",
    "비주거용건축": "건축 > 비주거용",
    "토목": "토목",
    "기계설비": "기계설비",
}

COLUMN_DISPLAY = {v: k for k, v in INDEX_COLUMNS.items()}


def load_data(uploaded_file=None) -> pd.DataFrame:
    """
    건설공사비 지수 CSV 데이터를 로드합니다.
    uploaded_file이 있으면 업로드된 파일을, 없으면 내장 데이터를 사용합니다.
    """
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(DATA_PATH)

    df = _preprocess(df)
    return df


def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 전처리: 날짜 컬럼 생성 및 타입 정리"""
    df = df.copy()
    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)
    # 날짜 컬럼 추가 (매월 1일 기준)
    df["날짜"] = pd.to_datetime(
        df["연도"].astype(str) + "-" + df["월"].astype(str).str.zfill(2) + "-01"
    )
    df["연월"] = df["날짜"].dt.strftime("%Y-%m")
    df = df.sort_values("날짜").reset_index(drop=True)
    return df


def get_available_years(df: pd.DataFrame) -> list[int]:
    """사용 가능한 연도 목록 반환"""
    return sorted(df["연도"].unique().tolist())


def get_available_months() -> list[int]:
    return list(range(1, 13))


def get_index_value(
    df: pd.DataFrame, year: int, month: int, category: str
) -> float | None:
    """특정 연도/월/항목의 지수값 반환"""
    row = df[(df["연도"] == year) & (df["월"] == month)]
    if row.empty:
        return None
    return float(row[category].values[0])


def calculate_price_change(
    df: pd.DataFrame,
    base_year: int,
    base_month: int,
    target_year: int,
    target_month: int,
    category: str,
    original_amount: float,
) -> dict:
    """
    기준 시점 대비 목표 시점의 물가 변동 계산

    Returns:
        dict: {
            base_index, target_index,
            change_rate, adjusted_amount,
            change_amount
        }
    """
    base_index = get_index_value(df, base_year, base_month, category)
    target_index = get_index_value(df, target_year, target_month, category)

    if base_index is None or target_index is None:
        return None

    if base_index == 0:
        return None

    change_rate = (target_index - base_index) / base_index * 100
    adjusted_amount = original_amount * (target_index / base_index)
    change_amount = adjusted_amount - original_amount

    return {
        "base_index": round(base_index, 2),
        "target_index": round(target_index, 2),
        "change_rate": round(change_rate, 2),
        "adjusted_amount": round(adjusted_amount, 2),
        "change_amount": round(change_amount, 2),
    }


def calculate_annual_average(df: pd.DataFrame) -> pd.DataFrame:
    """연도별 평균 지수 계산"""
    numeric_cols = ["종합", "건축", "주거용건축", "비주거용건축", "토목", "기계설비"]
    annual = df.groupby("연도")[numeric_cols].mean().round(2).reset_index()
    return annual


def calculate_yoy_change(df: pd.DataFrame) -> pd.DataFrame:
    """전년 동월 대비 등락률 계산"""
    df = df.copy().sort_values("날짜")
    numeric_cols = ["종합", "건축", "주거용건축", "비주거용건축", "토목", "기계설비"]
    change_cols = {col: f"{col}_전년동월비" for col in numeric_cols}

    df = df.set_index("날짜")
    for col in numeric_cols:
        df[change_cols[col]] = df[col].pct_change(12).mul(100).round(2)
    df = df.reset_index()
    return df


def calculate_mom_change(df: pd.DataFrame) -> pd.DataFrame:
    """전월 대비 등락률 계산"""
    df = df.copy().sort_values("날짜")
    numeric_cols = ["종합", "건축", "주거용건축", "비주거용건축", "토목", "기계설비"]
    change_cols = {col: f"{col}_전월비" for col in numeric_cols}

    df = df.set_index("날짜")
    for col in numeric_cols:
        df[change_cols[col]] = df[col].pct_change(1).mul(100).round(2)
    df = df.reset_index()
    return df


def get_period_summary(
    df: pd.DataFrame,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    category: str,
) -> dict:
    """기간 내 지수 요약 통계"""
    mask = (
        (df["연도"] > start_year)
        | ((df["연도"] == start_year) & (df["월"] >= start_month))
    ) & (
        (df["연도"] < end_year)
        | ((df["연도"] == end_year) & (df["월"] <= end_month))
    )
    subset = df[mask][category]

    if subset.empty:
        return {}

    return {
        "최솟값": round(subset.min(), 2),
        "최댓값": round(subset.max(), 2),
        "평균": round(subset.mean(), 2),
        "표준편차": round(subset.std(), 2),
        "데이터 수": len(subset),
    }


def filter_by_period(
    df: pd.DataFrame,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> pd.DataFrame:
    """기간으로 데이터 필터링"""
    start_date = pd.Timestamp(f"{start_year}-{start_month:02d}-01")
    end_date = pd.Timestamp(f"{end_year}-{end_month:02d}-01")
    return df[(df["날짜"] >= start_date) & (df["날짜"] <= end_date)].copy()
