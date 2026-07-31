# 🏗️ 건설공사비 지수 물가 계산기

건설공사비지수(KCCI)를 활용하여 건설 공사비의 시점 간 물가 변동을 계산하는 웹 애플리케이션입니다.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

---

## 주요 기능

| 탭 | 기능 |
|---|---|
| 💰 물가 계산 | 기준 시점과 비교 시점을 선택해 공사비 물가 변동 금액 계산 |
| 📈 지수 추이 | 기간별 지수 시계열 차트 및 연도별 평균 비교 |
| 📊 변동률 분석 | 전년 동월 대비 / 전월 대비 변동률, 히트맵 |
| 📋 데이터 조회 | 원시 데이터 필터링 및 CSV 다운로드 |

---

## 계산 방식

```
조정 금액 = 원래 금액 × (비교 시점 지수 / 기준 시점 지수)
```

- **기준년도**: 2015년 = 100
- **데이터 출처**: 한국건설기술연구원(KICT) 건설공사비지수(KCCI)
- **지수 항목**: 종합 / 건축(주거용·비주거용) / 토목 / 기계설비

---

## 로컬 실행

### 1. 저장소 클론

```bash
git clone https://github.com/<YOUR_USERNAME>/construction-cost-index.git
cd construction-cost-index
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

---

## Streamlit Cloud 배포 방법

1. 이 저장소를 GitHub에 Push합니다.
2. [share.streamlit.io](https://share.streamlit.io) 접속 후 GitHub 계정으로 로그인합니다.
3. **New app** 클릭 → 저장소·브랜치·파일(`app.py`) 선택 → **Deploy** 클릭
4. 배포 완료 후 공개 URL을 공유합니다.

> **무료 플랜**: public 저장소는 무료로 무제한 배포 가능합니다.

---

## 데이터 업데이트 방법

최신 데이터를 반영하려면 두 가지 방법을 사용할 수 있습니다.

### 방법 1: CSV 파일 직접 교체

`data/construction_cost_index.csv` 파일을 아래 형식에 맞게 수정합니다.

```
연도,월,종합,건축,주거용건축,비주거용건축,토목,기계설비
2025,7,153.2,151.9,...
```

### 방법 2: 웹앱에서 파일 업로드

사이드바의 **📂 데이터 파일 업로드** 기능을 통해 최신 CSV를 즉시 반영합니다.

최신 데이터는 아래에서 다운로드할 수 있습니다.
- [KOSIS 국가통계포털](https://kosis.kr) → 건설·주택·토지 → 건설공사비지수
- [한국건설기술연구원](https://www.kict.re.kr)

---

## 프로젝트 구조

```
construction-cost-index/
├── app.py                          # Streamlit 메인 앱
├── utils.py                        # 데이터 처리 유틸리티
├── requirements.txt                # Python 패키지 목록
├── .streamlit/
│   └── config.toml                 # Streamlit 테마 설정
├── data/
│   └── construction_cost_index.csv # 건설공사비 지수 데이터
└── README.md
```

---

## 라이선스

MIT License
