# app.py - 简历JD深度匹配分析器（美化版）
import streamlit as st
from openai import OpenAI
import pdfplumber
from docx import Document
import json

# ========== 页面基本设置 ==========
st.set_page_config(page_title="简历JD匹配分析", page_icon="📊", layout="wide")

# ========== 自定义 CSS 样式 ==========
def local_css():
    st.markdown("""
    <style>
    /* 整体背景渐变 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    /* 卡片容器（用于 expander） */
    .stExpander {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 10px;
        margin-bottom: 10px;
    }
    /* 标题颜色 */
    h1 { color: #2c3e50; font-weight: 700; }
    h2, h3 { color: #34495e; }
    /* 主按钮渐变 */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 10px 25px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(102,126,234,0.4);
    }
    /* 进度条颜色 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    /* 文件上传区域虚线边框 */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ========== 标题区（居中 + 描述） ==========
st.markdown("""
<div style="text-align: center; padding: 30px 0 10px 0;">
    <h1>📊 简历 vs 岗位深度匹配分析器</h1>
    <p style="font-size: 1.2rem; color: #555;">上传简历 + 粘贴 JD，AI 为你定制求职方案</p>
</div>
""", unsafe_allow_html=True)

# ========== API Key 读取（侧边栏美化） ==========
api_key = None
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    pass

with st.sidebar:
    st.markdown("## 🔐 设置 API Key")
    st.markdown("---")
    if not api_key:
        st.warning("请输入 DeepSeek API Key 解锁功能")
        api_key = st.text_input("API Key", type="password", placeholder="sk-...")
        st.caption("[🔗 获取 DeepSeek Key](https://platform.deepseek.com)")
    else:
        st.success("✅ API Key 已就绪")

client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ========== 文件读取函数 ==========
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

# ========== 核心分析函数（强化 Prompt） ==========
def analyze(jd_text, resume_text):
    max_len = 8000
    jd_text = jd_text[:max_len]
    resume_text = resume_text[:max_len]

    prompt = f"""
你是一位顶尖的职业规划师和企业招聘专家。请对【职位描述】和【候选人简历】进行深度分析，给出专业、具体、可执行的建议。
必须返回一个结构化的 JSON 对象，不要任何额外文字。

【职位描述】
{jd_text}

【候选人简历】
{resume_text}

分析要求：
1. 综合匹配度：给出 0-100 的分数，并解释打分的核心依据（1-2句话，放在 JSON 的 "评分说明" 字段中）。
2. 匹配分析：列出所有匹配的硬技能、软技能、经验，每一项都要简要说明“简历中的哪段经历/技能与此相关”。
3. 关键缺失：对每一项缺失项，不仅要列出，还要提供“如何弥补”的具体建议（例如学习平台、认证考试、项目实践方向）。每个缺失项包含 "缺失项" 和 "弥补建议" 两个子字段。
4. 简历优化建议：至少 5 条，每条要给出具体的修改示范（比如“将‘负责XX’改为‘通过XX方法，实现XX量化结果’”），并说明为什么这样改。
5. 面试准备方向：至少列出 5 个该岗位可能问到的技术/行为面试问题，并针对每个问题给出回答要点。
6. 技能提升路线图：给出一个 3 个月的短期学习计划，明确每个月该学什么、做什么项目，以补齐最大的 2-3 个短板。

请严格按照以下 JSON 格式返回（使用双引号，确保合法）：
{{
    "综合匹配度": 0-100的整数,
    "评分说明": "打分的核心依据",
    "匹配分析": {{
        "硬技能匹配": [{{"技能": "技能名", "关联经历": "简历中的对应描述"}}],
        "软技能匹配": [{{"技能": "技能名", "关联经历": "简历中的对应描述"}}],
        "经验匹配": [{{"经验要求": "JD要求", "关联经历": "简历中的对应描述"}}]
    }},
    "关键缺失": {{
        "技能缺失": [{{"缺失项": "技能名", "弥补建议": "具体学习路径/资源"}}],
        "经验不足": [{{"缺失项": "经验要求", "弥补建议": "如何获得相关经验"}}],
        "资格缺失": [{{"缺失项": "证书/学历等", "弥补建议": "获取途径"}}]
    }},
    "简历优化建议": [
        {{
            "建议": "修改方向",
            "修改示范": "原文：... 建议改为：...",
            "理由": "为什么这样改"
        }}
    ],
    "面试准备方向": [
        {{"问题类型": "技术/行为", "可能的问题": "...", "回答要点": "..."}}
    ],
    "技能提升路线图": {{
        "第1个月": {{
            "目标": "...",
            "学习内容": ["..."],
            "实践项目": "..."
        }},
        "第2个月": {{"目标": "...", "学习内容": ["..."], "实践项目": "..."}},
        "第3个月": {{"目标": "...", "学习内容": ["..."], "实践项目": "..."}}
    }}
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"error": f"AI返回了非JSON格式的内容：{content[:300]}"}
    except Exception as e:
        return {"error": str(e)}

# ========== 报告展示函数（美化版） ==========
def print_report(result):
    # 动态匹配度颜色和图标
    score = result.get("综合匹配度", 0)
    if score >= 80:
        color = "#27ae60"
        emoji = "🟢"
    elif score >= 60:
        color = "#f39c12"
        emoji = "🟡"
    else:
        color = "#e74c3c"
        emoji = "🔴"

    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <span style="font-size: 3rem; font-weight: bold; color: {color};">{score}%</span> {emoji}
        <p style="color: #666; margin-top: 10px;">{result.get('评分说明', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(score / 100)

    # 匹配分析
    st.subheader("✅ 匹配分析")
    match = result.get("匹配分析", {})
    if match.get("硬技能匹配"):
        st.write("**🔧 硬技能匹配：**")
        for item in match["硬技能匹配"]:
            with st.expander(f"✅ {item.get('技能', '')}"):
                st.write(f"**关联经历：** {item.get('关联经历', '')}")
    if match.get("软技能匹配"):
        st.write("**🤝 软技能匹配：**")
        for item in match["软技能匹配"]:
            with st.expander(f"✅ {item.get('技能', '')}"):
                st.write(f"**关联经历：** {item.get('关联经历', '')}")
    if match.get("经验匹配"):
        st.write("**💼 经验匹配：**")
        for item in match["经验匹配"]:
            with st.expander(f"✅ {item.get('经验要求', '')}"):
                st.write(f"**关联经历：** {item.get('关联经历', '')}")

    # 关键缺失
    st.subheader("❌ 关键缺失")
    missing = result.get("关键缺失", {})
    if missing.get("技能缺失"):
        st.write("**🎯 技能缺失：**")
        for item in missing["技能缺失"]:
            with st.expander(f"❌ {item.get('缺失项', '')}"):
                st.write(f"**💡 弥补建议：** {item.get('弥补建议', '')}")
    if missing.get("经验不足"):
        st.write("**⏳ 经验不足：**")
        for item in missing["经验不足"]:
            with st.expander(f"❌ {item.get('缺失项', '')}"):
                st.write(f"**💡 弥补建议：** {item.get('弥补建议', '')}")
    if missing.get("资格缺失"):
        st.write("**📜 资格缺失：**")
        for item in missing["资格缺失"]:
            with st.expander(f"❌ {item.get('缺失项', '')}"):
                st.write(f"**💡 弥补建议：** {item.get('弥补建议', '')}")

    # 简历优化建议
    st.subheader("💡 简历优化建议")
    for i, sug in enumerate(result.get("简历优化建议", []), 1):
        with st.expander(f"建议 {i}: {sug.get('建议', '')}"):
            st.markdown(f"**✍️ 修改示范：** {sug.get('修改示范', '')}")
            st.markdown(f"**📌 理由：** {sug.get('理由', '')}")

    # 面试准备
    st.subheader("🎯 面试准备方向")
    for i, q in enumerate(result.get("面试准备方向", []), 1):
        with st.expander(f"Q{i}: {q.get('可能的问题', '')}"):
            st.write(f"**类型：** {q.get('问题类型', '')}")
            st.write(f"**回答要点：** {q.get('回答要点', '')}")

    # 提升路线图
    roadmap = result.get("技能提升路线图", {})
    if roadmap:
        st.subheader("🗺️ 技能提升路线图（3个月冲刺计划）")
        for month, plan in roadmap.items():
            with st.expander(month):
                st.write(f"**🎯 目标：** {plan.get('目标', '')}")
                st.write(f"**📚 学习内容：**")
                for content in plan.get("学习内容", []):
                    st.markdown(f"- {content}")
                st.write(f"**🔨 实践项目：** {plan.get('实践项目', '')}")

# ========== 主界面（卡片式布局） ==========
col1, col2 = st.columns([1, 1])

with col1:
    with st.container():
        st.markdown("""<div style="background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">""", unsafe_allow_html=True)
        st.subheader("📄 上传简历")
        uploaded_file = st.file_uploader("选择文件（PDF/Word/TXT）", type=["pdf", "docx", "txt"])
        if uploaded_file:
            try:
                resume_text = read_resume(uploaded_file)
                st.success(f"✅ 简历读取成功，共 {len(resume_text)} 字符")
            except Exception as e:
                st.error(f"❌ 读取失败：{e}")
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("""<div style="background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">""", unsafe_allow_html=True)
        st.subheader("📋 粘贴职位描述")
        jd_text = st.text_area("将完整的岗位JD粘贴到这里", height=300)
        st.markdown("</div>", unsafe_allow_html=True)

# 分析按钮
if st.button("🔍 开始深度分析", type="primary", use_container_width=True):
    if not client:
        st.error("请先在左侧边栏输入 DeepSeek API Key")
    elif not uploaded_file:
        st.warning("请先上传简历文件")
    elif len(jd_text) < 50:
        st.warning("职位描述至少需要50个字符")
    else:
        with st.spinner("🤖 AI 正在仔细比对简历与岗位要求，生成详细报告..."):
            result = analyze(jd_text, resume_text)
        if not isinstance(result, dict):
            st.error(f"未知错误：{result}")
        elif "error" in result:
            st.error(f"分析失败：{result['error']}")
        else:
            st.success("分析完成！以下是详细报告 👇")
            print_report(result)

# ========== 页脚美化 ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #999;">
    <small>🔒 你的简历和JD仅用于本次分析，不会被存储。<br>
    Made with ❤️ using Streamlit & DeepSeek</small>
</div>
""", unsafe_allow_html=True)
