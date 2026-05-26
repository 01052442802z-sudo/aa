# app.py

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
    height:55px;
    font-size:18px;
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

    today_sales = pd.to_numeric(
        today_df["금액"],
        errors="coerce"
    ).fillna(0).sum()

    st.metric(
        "오늘 예상 매출",
        f"{today_sales:,.0f} 원"
    )

    if today_df.empty:
        st.info("오늘 일정 없음")

    for idx, row in today_df.iterrows():

        phone = str(row["전화번호"])

        address_encoded = urllib.parse.quote(
            str(row["주소"])
        )

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
                <p>📝 {row['특이사항']}</p>
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

                master_df.to_csv(
                    MASTER_FILE,
                    index=False
                )

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

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    st.divider()

    # =========================
    # 고객 수정
    # =========================

    st.subheader("✏ 고객 일정 수정")

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

            history_df.to_csv(
                HISTORY_FILE,
                index=False
            )

            master_df.loc[row_idx, "날짜"] = str(new_date)
            master_df.loc[row_idx, "시간"] = new_time
            master_df.loc[row_idx, "상태"] = new_status

            master_df.to_csv(
                MASTER_FILE,
                index=False
            )

            st.success("수정 완료")
            st.rerun()

    st.divider()

    # =========================
    # 신규 고객 등록
    # =========================

    st.subheader("➕ 신규 고객 직접 등록")

    with st.form("add_customer_form"):

        new_name = st.text_input("고객명")

        new_phone = st.text_input("전화번호")

        new_address = st.text_input("주소")

        new_ac = st.selectbox(
            "에어컨 종류",
            [
                "벽걸이",
                "스탠드",
                "2in1",
                "천장형",
                "시스템"
            ]
        )

        new_work = st.selectbox(
            "작업 종류",
            [
                "분해청소",
                "완전분해",
                "가스충전",
                "점검",
                "기타"
            ]
        )

        new_note = st.text_area("특이사항")

        new_price = st.number_input(
            "금액",
            min_value=0,
            step=10000
        )

        new_date = st.date_input("작업 날짜")

        new_time = st.text_input(
            "시간",
            placeholder="예: 14:00"
        )

        submit = st.form_submit_button("고객 등록")

        if submit:

            customer_id = new_phone.replace("-", "")

            # 중복 체크
            if customer_id in master_df["고객ID"].astype(str).tolist():

                st.error("이미 등록된 고객")

            else:

                new_row = {
                    "고객ID": customer_id,
                    "고객명": new_name,
                    "전화번호": new_phone,
                    "주소": new_address,
                    "에어컨종류": new_ac,
                    "작업종류": new_work,
                    "특이사항": new_note,
                    "금액": new_price,
                    "상태": "일정확정",
                    "날짜": str(new_date),
                    "시간": new_time
                }

                master_df.loc[len(master_df)] = new_row

                master_df.to_csv(
                    MASTER_FILE,
                    index=False
                )

                st.success("신규 고객 등록 완료")

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

        st.subheader("업로드 데이터")

        st.dataframe(
            upload_df,
            use_container_width=True
        )

        # 전화번호 기준 ID 생성
        upload_df["고객ID"] = upload_df[
            "전화번호"
        ].astype(str).str.replace("-", "")

        existing_ids = master_df[
            "고객ID"
        ].astype(str).tolist()

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

            master_df.to_csv(
                MASTER_FILE,
                index=False
            )

            st.success(
                f"{len(new_customers)}명 신규 고객 추가 완료"
            )

            st.dataframe(
                new_customers,
                use_container_width=True
            )

# =========================
# 하단
# =========================

st.divider()

st.caption("에어케어 매니저 v1.1")