import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq
import re

# ---------------- SETUP ----------------
st.set_page_config(page_title="Enhanced AI Resume Coach", layout="centered")

api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("❌ GROQ_API_KEY not found in Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ---------------- PDF TEXT EXTRACTION ----------------
def extract_text_from_pdf(uploaded_file):
    try:
        pdf = PdfReader(uploaded_file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""

# ---------------- RESUME VALIDATION ----------------
def is_resume(text):
    keywords = [
        "education", "experience", "skills", "projects",
        "resume", "profile", "certification"
    ]
    match_count = sum(1 for word in keywords if re.search(word, text, re.IGNORECASE))
    return match_count >= 2

# ---------------- TEMPLATE MAP ----------------
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

# ---------------- AI ANALYSIS (FIXED) ----------------
def analyze_resume(text):
    # 🔒 Token safety (MOST IMPORTANT FIX)
    text = text[:6000]

    prompt = f"""
You are an expert career coach. Analyze this resume and provide:
1. Suggested Job Titles
2. Key Strengths
3. Areas of Improvement
4. Missing Keywords for Data Science
5. Estimated ATS pass probability (0–100%)
6. Section recommendations
7. Resume style feedback
8. Suggest ONE best-fitting resume template name from ONLY these:
   - Minimalist Classic
   - Modern Creative
   - One-page Professional

Resume:
{text}
"""

    messages = [
        {"role": "system", "content": "You are a professional resume reviewer."},
        {"role": "user", "content": prompt}
    ]

    try:
        # 🔥 Try large model first
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.2,
            max_tokens=900
        )
    except Exception as e:
        # ❗ Show exact error message (debug)
        st.error(f"❌ AI analysis failed: {e}")
        st.stop()

        # Fallback model (if needed)
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.2,
            max_tokens=900
        )

    return resp.choices[0].message.content

# ---------------- TEMPLATE NAME EXTRACTION ----------------
def extract_template_name(response_text):
    for name in ["Minimalist Classic", "Modern Creative", "One-page Professional"]:
        if re.search(rf"\b{name}\b", response_text):
            return name
    return None

# ---------------- STREAMLIT UI ----------------
st.title("🧠 AI Resume Analyzer & Template Advisor")

uploaded_files = st.file_uploader(
    "Upload one or more resumes (PDF only)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded in uploaded_files:
        st.markdown("---")
        st.subheader(f"📄 Analyzing: {uploaded.name}")

        text = extract_text_from_pdf(uploaded)

        if not text:
            st.error("❌ Unable to extract text. Try another PDF.")
            continue

        if not is_resume(text):
            st.error("❌ This does not appear to be a valid resume.")
            continue

        with st.spinner("🔍 Analyzing with AI..."):
            try:
                result = analyze_resume(text)
            except Exception as e:
                st.error(f"❌ AI analysis failed: {e}")
                continue

        st.markdown("### 📊 AI Feedback")
        st.markdown(result)

        recommended_template = extract_template_name(result)
        if recommended_template:
            template_info = get_template_image_url(recommended_template)
            if template_info:
                st.markdown("### 🎨 Recommended Resume Template")
                st.image(template_info["img"], use_container_width=True)
                st.markdown(f"**Style**: {recommended_template}")
                st.markdown(f"[🔗 View Template]({template_info['link']})")
