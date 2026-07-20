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
    def analyze(jd_text, resume_text):
    max_len = 8000
    jd_text = jd_text[:max_len]
    resume_text = resume_text[:max_len]

    prompt = f"""
你是一位资深的HR和职业规划师。请严格根据以下提供的【职位描述】和【候选人简历】进行客观分析。
要求：你必须返回一个结构化的 JSON 对象，不要包含任何额外文字。请在输出中包含单词 json。

【职位描述】
{jd_text}

【候选人简历】
{resume_text}

请返回如下JSON：
{{
    "综合匹配度": 0-100的整数,
    "匹配分析": {{
        "硬技能匹配": [],
        "软技能匹配": [],
        "经验匹配": []
    }},
    "关键缺失": {{
        "技能缺失": [],
        "经验不足": [],
        "资格缺失": []
    }},
    "简历优化建议": [],
    "面试准备方向": []
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        # 尝试解析 JSON，如果失败则返回原始内容作为错误信息
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"error": f"AI返回了非JSON格式的内容：{content[:200]}"}
    except Exception as e:
        return {"error": str(e)}
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
    max_len = 8000
    jd_text = jd_text[:max_len]
    resume_text = resume_text[:max_len]

    prompt = f"""
你是一位资深的HR和职业规划师。请严格根据以下提供的【职位描述】和【候选人简历】进行客观分析。
要求：你必须返回一个结构化的 JSON 对象，不要包含任何额外文字。

【职位描述】
{jd_text}

【候选人简历】
{resume_text}

请返回如下JSON：
{{
    "综合匹配度": 0-100的整数,
    "匹配分析": {{
        "硬技能匹配": [],
        "软技能匹配": [],
        "经验匹配": []
    }},
    "关键缺失": {{
        "技能缺失": [],
        "经验不足": [],
        "资格缺失": []
    }},
    "简历优化建议": [],
    "面试准备方向": []
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"error": f"AI返回了非JSON格式的内容：{content[:200]}"}
    except Exception as e:
        return {"error": str(e)}
