import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq
import re

# --- Setup ---
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- PDF extract ---
def extract_text_from_pdf(uploaded_file):
    pdf = PdfReader(uploaded_file)
    return "".join(page.extract_text() or "" for page in pdf.pages)

# --- Basic resume content check ---
def is_resume(text):
    keywords = ["education", "experience", "skills", "projects", "resume", "profile", "certification"]
    match_count = sum(1 for word in keywords if re.search(word, text, re.IGNORECASE))
    return match_count >= 2

# --- Template suggestion mapping ---
def get_template_image_url(template_name):
    template_map = {
        "Minimalist Classic": {
            "img": "https://cdn.jsdelivr.net/gh/OpenAI-Designs/templates/minimalist-classic.png",
            "link": "https://www.canva.com/resumes/templates/minimalist/"
        },
        "Modern Creative": {
            "img": "https://cdn.jsdelivr.net/gh/OpenAI-Designs/templates/modern-creative.png",
            "link": "https://www.canva.com/resumes/templates/creative/"
        },
        "One-page Professional": {
            "img": "https://cdn.jsdelivr.net/gh/OpenAI-Designs/templates/onepage-professional.png",
            "link": "https://www.canva.com/resumes/templates/professional/"
        }
    }
    return template_map.get(template_name, {})

# --- AI analysis ---
def analyze_resume(text):
    prompt = f"""
You are an expert career coach. Analyze this resume and provide:
1.  Suggested Job Titles
2.  Key Strengths
3.  Areas of Improvement
4.  Missing Keywords for data science
5.  Estimated ATS pass probability (0–100%)
6.  Section recommendations (e.g., add Projects, Portfolio link)
7.  Resume style feedback
8.  Suggest one best-fitting resume template name from only these options: Minimalist Classic, Modern Creative, One-page Professional. Return only one name.

Resume:
{text}
"""
    resp = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return resp.choices[0].message.content

# --- Extract recommended template name from AI output ---
def extract_template_name(response_text):
    for name in ["Minimalist Classic", "Modern Creative", "One-page Professional"]:
        pattern = rf"\b{name}\b"
        if re.search(pattern, response_text):
            return name
    return None

# --- Streamlit UI ---
st.set_page_config(page_title="Enhanced AI Resume Coach", layout="centered")
st.title(" AI Resume Analyzer & Template Advisor")

uploaded_files = st.file_uploader("Upload one or more resumes (PDFs)", type=["pdf"], accept_multiple_files=True)
if uploaded_files:
    for uploaded in uploaded_files:
        st.markdown(f"---\n### 📄 Analyzing: {uploaded.name}")
        text = extract_text_from_pdf(uploaded)
        if text.strip():
            if not is_resume(text):
                st.error("❌ This doesn't appear to be a resume. Please upload a valid resume PDF.")
            else:
                with st.spinner(" Analyzing with AI..."):
                    result = analyze_resume(text)
                st.markdown("####  AI Feedback:")
                st.markdown(result, unsafe_allow_html=True)

                recommended_template = extract_template_name(result)
                if recommended_template:
                    template_info = get_template_image_url(recommended_template)
                    if template_info:
                        st.markdown("####  Recommended Resume Template")
                        st.image(template_info["img"], use_container_width=True)
                        st.markdown(f"**Recommended Style**: {recommended_template}")
                        st.markdown(f"[ View or Download Template]({template_info['link']})")
        else:
            st.error("Couldn't extract text, try another PDF.")
