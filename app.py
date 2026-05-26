import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="에어컨 일정관리",
    layout="wide"
)

# ------------------
# 사이드 메뉴
# ------------------
menu = st.sidebar.radio(
    "메뉴",
    [
        "대시보드",
        "업체 엑셀 업로드",
        "오늘 일정",
        "캘린더",
        "고객관리",
        "동선표",
        "매출관리"
    ]
)

# ------------------
# 세션 데이터
# ------------------
if "customers" not in st.session_state:
    st.session_state.customers = pd.DataFrame(columns=[
        "고객명",
        "전화번호",
        "주소",
        "작업종류",
        "날짜",
        "시간",
        "금액",
        "상태",
        "특이사항"
    ])

# ------------------
# 대시보드
# ------------------
if menu == "대시보드":

    st.title("에어컨 청소 일정관리")

    total = len(st.session_state.customers)

    today = datetime.today().strftime("%Y-%m-%d")

    today_count = len(
        st.session_state.customers[
            st.session_state.customers["날짜"] == today
        ]
    )

    done_count = len(
        st.session_state.customers[
            st.session_state.customers["상태"] == "완료"
        ]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("전체 고객", total)
    col2.metric("오늘 일정", today_count)
    col3.metric("완료", done_count)

    st.divider()

    st.subheader("최근 일정")
    st.dataframe(st.session_state.customers.tail(10), use_container_width=True)

# ------------------
# 엑셀 업로드
# ------------------
elif menu == "업체 엑셀 업로드":

    st.title("업체 엑셀 업로드")

    uploaded = st.file_uploader(
        "엑셀 파일 업로드",
        type=["xlsx", "xls"]
    )

    if uploaded:

        try:
            xls = pd.ExcelFile(uploaded)

            st.success("엑셀 읽기 성공")

            st.write("시트 목록")
            st.write(xls.sheet_names)

            selected_sheet = st.selectbox(
                "시트 선택",
                xls.sheet_names
            )

            df = pd.read_excel(uploaded, sheet_name=selected_sheet)

            st.subheader("원본 데이터")
            st.dataframe(df, use_container_width=True)

            st.divider()

            st.subheader("고객 데이터 등록")

            customer_name = st.text_input("고객명 컬럼명")
            phone_col = st.text_input("전화번호 컬럼명")
            address_col = st.text_input("주소 컬럼명")

            if st.button("고객 리스트 생성"):

                try:

                    new_df = pd.DataFrame({
                        "고객명": df[customer_name],
                        "전화번호": df[phone_col],
                        "주소": df[address_col],
                        "작업종류": "미정",
                        "날짜": "",
                        "시간": "",
                        "금액": 0,
                        "상태": "연락전",
                        "특이사항": ""
                    })

                    st.session_state.customers = pd.concat([
                        st.session_state.customers,
                        new_df
                    ]).drop_duplicates()

                    st.success("고객 등록 완료")

                except Exception as e:
                    st.error(e)

        except Exception as e:
            st.error(e)

# ------------------
# 오늘 일정
# ------------------
elif menu == "오늘 일정":

    st.title("오늘 일정")

    today = datetime.today().strftime("%Y-%m-%d")

    today_df = st.session_state.customers[
        st.session_state.customers["날짜"] == today
    ]

    st.dataframe(today_df, use_container_width=True)

# ------------------
# 캘린더
# ------------------
elif menu == "캘린더":

    st.title("날짜별 일정")

    selected_date = st.date_input("날짜 선택")

    filtered = st.session_state.customers[
        st.session_state.customers["날짜"] == str(selected_date)
    ]

    st.subheader(f"{selected_date} 일정")

    st.dataframe(filtered, use_container_width=True)

# ------------------
# 고객관리
# ------------------
elif menu == "고객관리":

    st.title("고객관리")

    df = st.session_state.customers

    st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

# ------------------
# 동선표
# ------------------
elif menu == "동선표":

    st.title("하루 동선표")

    selected_date = st.date_input("동선 날짜")

    route_df = st.session_state.customers[
        st.session_state.customers["날짜"] == str(selected_date)
    ]

    st.subheader("방문 순서")

    for i, row in route_df.iterrows():

        st.info(
            f"{row['시간']} - {row['주소']} ({row['고객명']})"
        )

# ------------------
# 매출관리
# ------------------
elif menu == "매출관리":

    st.title("매출관리")

    df = st.session_state.customers.copy()

    df["금액"] = pd.to_numeric(df["금액"], errors="coerce").fillna(0)

    today = datetime.today().strftime("%Y-%m-%d")

    today_sales = df[df["날짜"] == today]["금액"].sum()

    month_sales = df["금액"].sum()

    col1, col2 = st.columns(2)

    col1.metric("오늘 매출", f"{today_sales:,.0f}원")
    col2.metric("전체 매출", f"{month_sales:,.0f}원")

    st.divider()

    st.subheader("작업별 통계")

    st.dataframe(
        df.groupby("작업종류")["금액"].sum().reset_index(),
        use_container_width=True
    )