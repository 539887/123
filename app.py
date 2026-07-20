# app.py - 防空白版
import streamlit as st
from openai import OpenAI
import pdfplumber
from docx import Document
import json

st.set_page_config(page_title="简历JD匹配分析", page_icon="📊", layout="wide")
st.title("📊 简历 vs 岗位匹配分析器")
st.markdown("上传简历，粘贴岗位描述，AI帮你分析匹配度并提供建议。")

# ---- API Key 读取 ----
api_key = None
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    pass

if not api_key:
    with st.sidebar:
        st.warning("⚠️ 请输入 DeepSeek API Key")
        api_key = st.text_input("API Key", type="password", placeholder="sk-...")
        st.caption("[获取 DeepSeek Key](https://platform.deepseek.com)")

client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ---- 文件读取函数（不变） ----
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_resume(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        return read_pdf(uploaded_file)
    elif uploaded_file.name.endswith('.docx'):
        return read_docx(uploaded_file)
    elif uploaded_file.name.endswith('.txt'):
        return uploaded_file.getvalue().decode("utf-8")
    else:
        raise ValueError("不支持的文件格式，请上传 PDF、DOCX 或 TXT")

def analyze(jd_text, resume_text):
    prompt = f"""
你是一位资深的HR和职业规划师。请严格根据以下提供的【职位描述】和【候选人简历】进行客观分析。
要求：你必须返回一个结构化的 JSON 对象，不要包含任何额外文字。

【职位描述】
{jd_text}

【候选人简历】
{resume_text}

请严格按照以下JSON格式返回分析结果（确保输出是合法的JSON）：
{{
    "综合匹配度": 0-100的整数,
    "匹配分析": {{
        "硬技能匹配": ["技能1", "技能2"],
        "软技能匹配": ["沟通能力", "团队协作"],
        "经验匹配": ["相关经验描述"]
    }},
    "关键缺失": {{
        "技能缺失": ["JD要求但简历未体现的技能"],
        "经验不足": ["经验要求未满足的地方"],
        "资格缺失": ["学历/证书等缺失项"]
    }},
    "简历优化建议": [
        "具体建议1（要针对这份JD）",
        "具体建议2",
        "具体建议3"
    ],
    "面试准备方向": [
        "这个岗位可能会问的技术问题方向",
        "需要重点准备的项目经历"
    ]
}}
"""
# ---- 主界面 ----
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("1️⃣ 上传简历")
    uploaded_file = st.file_uploader("选择文件（PDF/Word/TXT）", type=["pdf", "docx", "txt"])
    if uploaded_file:
        try:
            resume_text = read_resume(uploaded_file)
            st.success(f"✅ 简历读取成功，共 {len(resume_text)} 字符")
        except Exception as e:
            st.error(f"❌ 读取失败：{e}")

with col2:
    st.subheader("2️⃣ 粘贴职位描述")
    jd_text = st.text_area("将完整的岗位JD粘贴到这里", height=300)

if st.button("🔍 开始分析", type="primary", use_container_width=True):
    if not client:
        st.error("请先在左侧边栏输入 DeepSeek API Key")
    elif not uploaded_file:
        st.warning("请先上传简历文件")
    elif len(jd_text) < 50:
        st.warning("职位描述至少需要50个字符")
    else:
        with st.spinner("AI 正在分析中..."):
            result = analyze(jd_text, resume_text)
        if "error" in result:
            st.error(f"分析失败：{result['error']}")
        else:
            # ... 结果展示（和之前一样，略）
            st.success("分析完成！")
            st.metric("综合匹配度", f"{result.get('综合匹配度', 0)}%")
