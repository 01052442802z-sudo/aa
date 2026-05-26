
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import urllib.parse

# =========================
# 기본 설정
# =========================

st.set_page_config(
    page_title="에어케어 매니저",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CSS
# =========================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-size:18px;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 5rem;
}

div.stButton > button {
    width:100%;
    height:60px;
    font-size:20px;
    border-radius:15px;
}

.card {
    padding:20px;
    border-radius:20px;
    margin-bottom:15px;
    background-color:#f7f7f7;
    box-shadow:0 2px 10px rgba(0,0,0,0.1);
}

.status-연락전 {
    border-left:10px solid gray;
}

.status-통화완료 {
    border-left:10px solid orange;
}

.status-일정확정 {
    border-left:10px solid blue;
}

.status-완료 {
    border-left:10px solid green;
}

.status-취소 {
    border-left:10px solid red;
}

</style>
""", unsafe_allow_html=True)

# =========================
# 폴더 생성
# =========================

os.makedirs("data/uploads", exist_ok=True)

MASTER_FILE = "data/customers_master.csv"
SCHEDULE_FILE = "data/schedules.csv"
HISTORY_FILE = "data/history.csv"

# =========================
# 초기 파일 생성
# =========================

if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=[
        "고객ID",
        "고객명",
        "전화번호",
        "주소",
        "에어컨종류",
        "작업종류",
        "특이사항",
        "금액",
        "상태",
        "날짜",
        "시간"
    ]).to_csv(MASTER_FILE, index=False)

if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=[
        "고객ID",
        "변경전날짜",
        "변경후날짜",
        "변경시간"
    ]).to_csv(HISTORY_FILE, index=False)

# =========================
# 데이터 로드
# =========================

master_df = pd.read_csv(MASTER_FILE)
history_df = pd.read_csv(HISTORY_FILE)

# =========================
# 메뉴
# =========================

selected = option_menu(
    menu_title=None,
    options=[
        "오늘 일정",
        "캘린더",
        "고객 관리",
        "매출",
        "업로드"
    ],
    icons=[
        "house",
        "calendar",
        "people",
        "cash",
        "upload"
    ],
    orientation="horizontal"
)

# =========================
# 오늘 일정
# =========================

if selected == "오늘 일정":

    st.title("📅 오늘 일정")

    today = datetime.now().strftime("%Y-%m-%d")

    today_df = master_df[
        master_df["날짜"].astype(str) == today
    ]

    st.metric(
        "오늘 예상 매출",
        f"{today_df['금액'].fillna(0).sum():,.0f} 원"
    )

    if today_df.empty:
        st.info("오늘 일정 없음")

    for idx, row in today_df.iterrows():

        phone = str(row["전화번호"])

        address_encoded = urllib.parse.quote(str(row["주소"]))

        naver_map = f"https://map.naver.com/v5/search/{address_encoded}"

        st.markdown(
            f"""
            <div class="card status-{row['상태']}">
                <h3>{row['시간']} - {row['고객명']}</h3>
                <p>📍 {row['주소']}</p>
                <p>📞 {row['전화번호']}</p>
                <p>❄ {row['에어컨종류']}</p>
                <p>🧹 {row['작업종류']}</p>
                <p>💰 {row['금액']} 원</p>
                <p>📌 상태: {row['상태']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.link_button(
                "📞 전화",
                f"tel:{phone}"
            )

        with col2:
            st.link_button(
                "🗺 지도",
                naver_map
            )

        with col3:
            if st.button("✅ 완료", key=f"done_{idx}"):

                master_df.loc[idx, "상태"] = "완료"

                master_df.to_csv(MASTER_FILE, index=False)

                st.success("완료 처리됨")
                st.rerun()

# =========================
# 캘린더
# =========================

elif selected == "캘린더":

    st.title("🗓 일정 캘린더")

    events = []

    for _, row in master_df.iterrows():

        if pd.notna(row["날짜"]):

            events.append({
                "title": f"{row['고객명']} ({row['시간']})",
                "start": row["날짜"]
            })

    calendar(events=events)

# =========================
# 고객 관리
# =========================

elif selected == "고객 관리":

    st.title("👥 고객 관리")

    search = st.text_input("고객 검색")

    filtered_df = master_df.copy()

    if search:

        filtered_df = filtered_df[
            filtered_df["고객명"].astype(str).str.contains(search)
        ]

    st.dataframe(filtered_df, use_container_width=True)

    st.divider()

    st.subheader("고객 일정 수정")

    if not filtered_df.empty:

        customer = st.selectbox(
            "고객 선택",
            filtered_df["고객명"].tolist()
        )

        row_idx = filtered_df[
            filtered_df["고객명"] == customer
        ].index[0]

        row = master_df.loc[row_idx]

        new_date = st.date_input(
            "날짜",
            value=pd.to_datetime(row["날짜"])
        )

        new_time = st.text_input(
            "시간",
            value=str(row["시간"])
        )

        new_status = st.selectbox(
            "상태",
            [
                "연락전",
                "통화완료",
                "일정확정",
                "완료",
                "취소"
            ],
            index=[
                "연락전",
                "통화완료",
                "일정확정",
                "완료",
                "취소"
            ].index(row["상태"])
        )

        if st.button("수정 저장"):

            history_df.loc[len(history_df)] = {
                "고객ID": row["고객ID"],
                "변경전날짜": row["날짜"],
                "변경후날짜": str(new_date),
                "변경시간": str(datetime.now())
            }

            history_df.to_csv(HISTORY_FILE, index=False)

            master_df.loc[row_idx, "날짜"] = str(new_date)
            master_df.loc[row_idx, "시간"] = new_time
            master_df.loc[row_idx, "상태"] = new_status

            master_df.to_csv(MASTER_FILE, index=False)

            st.success("수정 완료")
            st.rerun()

# =========================
# 매출
# =========================

elif selected == "매출":

    st.title("💰 매출 통계")

    master_df["금액"] = pd.to_numeric(
        master_df["금액"],
        errors="coerce"
    ).fillna(0)

    today = datetime.now().strftime("%Y-%m-%d")

    today_sales = master_df[
        master_df["날짜"].astype(str) == today
    ]["금액"].sum()

    current_month = datetime.now().strftime("%Y-%m")

    month_df = master_df[
        master_df["날짜"].astype(str).str.startswith(current_month)
    ]

    month_sales = month_df["금액"].sum()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "오늘 매출",
            f"{today_sales:,.0f} 원"
        )

    with col2:
        st.metric(
            "이번달 매출",
            f"{month_sales:,.0f} 원"
        )

    st.subheader("작업 종류별 매출")

    type_sales = master_df.groupby(
        "작업종류"
    )["금액"].sum()

    st.bar_chart(type_sales)

# =========================
# 업로드
# =========================

elif selected == "업로드":

    st.title("📤 업체 엑셀 업로드")

    uploaded_file = st.file_uploader(
        "엑셀 업로드",
        type=["xlsx"]
    )

    if uploaded_file:

        upload_df = pd.read_excel(uploaded_file)

        st.write("업로드 데이터")

        st.dataframe(upload_df)

        # 전화번호 기준 고객ID 생성
        upload_df["고객ID"] = upload_df["전화번호"].astype(str).str.replace("-", "")

        # 신규 고객 판별
        existing_ids = master_df["고객ID"].astype(str).tolist()

        new_customers = upload_df[
            ~upload_df["고객ID"].astype(str).isin(existing_ids)
        ]

        if new_customers.empty:

            st.warning("신규 고객 없음")

        else:

            new_customers["상태"] = "연락전"

            if "날짜" not in new_customers.columns:
                new_customers["날짜"] = ""

            if "시간" not in new_customers.columns:
                new_customers["시간"] = ""

            master_df = pd.concat(
                [master_df, new_customers],
                ignore_index=True
            )

            master_df.to_csv(MASTER_FILE, index=False)

            st.success(
                f"{len(new_customers)}명 신규 고객 추가 완료"
            )

            st.dataframe(new_customers)

# =========================
# 하단
# =========================

st.divider()

st.caption("에어케어 매니저 v1.0")