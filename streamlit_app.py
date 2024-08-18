import streamlit as st
import requests
from bs4 import BeautifulSoup
from docx import Document
from io import BytesIO
import base64

@st.cache_data
def search_naver_news(keyword, num_articles):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_jum&sort=0"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    news_list = []
    seen_titles = set()

    news_elements = soup.select("ul.list_news > li")

    for element in news_elements[:num_articles]:
        title = element.select_one("a.news_tit").get_text()
        summary = element.select_one("div.news_dsc").get_text()
        link = element.select_one("a.news_tit")['href']

        if title not in seen_titles:
            seen_titles.add(title)
            news_list.append({
                'title': title,
                'summary': summary,
                'link': link
            })

    return news_list

def create_word_document(news_list, keyword):
    doc = Document()
    doc.add_heading(f"'{keyword}' 관련 뉴스", 0)

    for idx, news in enumerate(news_list, 1):
        doc.add_heading(f"{idx}. {news['title']}", level=1)
        doc.add_paragraph(news['summary'])
        doc.add_paragraph(f"링크: {news['link']}")
        doc.add_paragraph("\n")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def get_download_link(buffer, filename):
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}">다운로드</a>'

st.set_page_config(page_title="네이버 뉴스 크롤러", page_icon="📰", layout="wide")

st.title("📰 네이버 뉴스 크롤러")

st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .news-item {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .news-title {
        font-weight: bold;
        color: #1e3a8a;
    }
    .news-summary {
        font-size: 0.9em;
        color: #374151;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

keyword = st.text_input("검색할 키워드를 입력하세요:")
num_articles = st.slider("가져올 기사 수", 1, 20, 5)

col1, col2, col3 = st.columns([2, 2, 1])

if col2.button("뉴스 검색"):
    if keyword:
        with st.spinner("뉴스를 검색 중입니다..."):
            news_results = search_naver_news(keyword, num_articles)
        
        if news_results:
            st.session_state.news_results = news_results
            st.success(f"'{keyword}'에 대한 상위 {len(news_results)}개 뉴스를 찾았습니다!")
            for idx, news in enumerate(news_results, 1):
                st.markdown(f"""
                <div class="news-item">
                    <p class="news-title">{idx}. {news['title']}</p>
                    <p class="news-summary">{news['summary']}</p>
                    <a href="{news['link']}" target="_blank">기사 읽기</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("검색 결과가 없습니다. 다른 키워드로 시도해보세요.")
    else:
        st.error("키워드를 입력해주세요.")

if col3.button("다운로드"):
    if 'news_results' in st.session_state and st.session_state.news_results:
        word_buffer = create_word_document(st.session_state.news_results, keyword)
        st.markdown(get_download_link(word_buffer, f"{keyword}_news.docx"), unsafe_allow_html=True)
    else:
        st.warning("먼저 뉴스를 검색해주세요.")
