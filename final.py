import streamlit as st
import PyPDF2
import json
import google.generativeai as genai

# ——————————— 설정 ———————————
st.set_page_config(page_title="📄 Multi-PDF→JSON → Gemini Q&A", layout="wide")

# 사이드바: API 키 및 모델 설정
st.sidebar.header("🔑 설정")
api_key = st.sidebar.text_input("Gemini API 키 입력", type="password")
model_name = st.sidebar.selectbox(
    "모델 선택",
    ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-prob-latest", "gemini-1.0"]
)

if api_key:
    genai.configure(api_key=api_key)
else:
    st.sidebar.warning("API 키를 입력해주세요.")

# ————— PDF → JSON 변환 함수 —————
@st.cache_data(show_spinner=False)
def pdf_to_json(file) -> dict:
    reader = PyPDF2.PdfReader(file)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text})
    return pages

# ————— Q&A 함수 —————
@st.cache_data(show_spinner=False)
def ask_gemini(context: str, question: str, model: str) -> str:
    prompt = f"""
다음은 여러 논문에서 추출된 본문입니다.
---
{context}
---
위 내용을 바탕으로 질문에 답해주세요:
{question}
"""
    gm = genai.GenerativeModel(model)
    response = gm.generate_content(prompt)
    return response.text.strip()

# ——————————— UI ———————————
st.title("📄 Multi-PDF → JSON 변환 & Gemini Q&A")

# 1) 여러 PDF 업로드 및 JSON 변환
uploaded_pdfs = st.file_uploader(
    "🔄 PDF 파일 여러 개 업로드", type=["pdf"], accept_multiple_files=True
)

paper_json_list = []
if uploaded_pdfs:
    with st.spinner("PDF들을 JSON으로 변환 중..."):
        for pdf_file in uploaded_pdfs:
            pages = pdf_to_json(pdf_file)
            paper_json_list.append({
                "filename": pdf_file.name,
                "pages": pages
            })

    # 통합 JSON 다운로드 버튼
    combined = {"papers": paper_json_list}
    json_str = json.dumps(combined, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 모든 논문 JSON 다운로드",
        data=json_str,
        file_name="all_papers.json",
        mime="application/json"
    )

    # 2) 질문 입력
    st.subheader("❓ 업로드한 논문들에 대해 질문하기")
    question = st.text_input("질문을 입력하세요:")
    if question:
        if not api_key:
            st.error("먼저 사이드바에 API 키를 입력해주세요.")
        else:
            with st.spinner("질문에 답변 생성 중..."):
                # 모든 논문의 텍스트를 이어붙여 컨텍스트 생성
                chunks = []
                for paper in paper_json_list:
                    header = f"[{paper['filename']}]"
                    body = "\n\n".join(p["text"] for p in paper["pages"])
                    chunks.append(f"{header}\n{body}")
                context = "\n\n".join(chunks)

                answer = ask_gemini(context, question, model_name)
            st.markdown("**🧠 AI의 응답:**")
            st.write(answer)
