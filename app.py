import streamlit as st
import pdfplumber
import io
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google import genai
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# Page Config
st.set_page_config(
    page_title="Resume Parser",
    page_icon="📄",
    layout="wide"    
)

# Custom CSS
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }

        .metric-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .metric-number {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1f77b4;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: 4px;
        }
        .section-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1f77b4;
            border-bottom: 2px solid #1f77b4;
            padding-bottom: 6px;
            margin-bottom: 16px;
        }
        .stButton > button {
            width: 100%;
            background-color: #1f77b4;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px;
          font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #155a8a;
        }
    </style>
""", unsafe_allow_html=True)

# Gemini Setup
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Skills Data
target_skills = [
    'Python', 'C', 'C++', 'Java', 'JavaScript', 'TypeScript',
    'R', 'Go', 'Rust', 'Kotlin', 'Swift', 'Scala', 'PHP',
    'Ruby', 'Perl', 'MATLAB', 'Shell', 'Bash', 'PowerShell',
    'SQL', 'VHDL', 'Verilog', 'Assembly',
    'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Next.js',
    'Nuxt.js', 'Svelte', 'Bootstrap', 'Tailwind CSS',
    'jQuery', 'Redux', 'GraphQL', 'REST API', 'WebSockets',
    'Node.js', 'Express.js', 'Django', 'Flask', 'FastAPI',
    'Spring Boot', 'Laravel', 'Ruby on Rails', 'ASP.NET',
    'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis',
    'Cassandra', 'DynamoDB', 'Oracle', 'MariaDB', 'Firebase',
    'Elasticsearch', 'Neo4j', 'Snowflake', 'BigQuery',
    'NumPy', 'Pandas', 'Matplotlib', 'Seaborn', 'Plotly',
    'SciPy', 'Statsmodels', 'Excel', 'Power BI', 'Tableau',
    'Looker', 'Apache Spark', 'Hadoop', 'Kafka', 'Airflow',
    'dbt', 'Jupyter', 'TensorFlow', 'PyTorch', 'Keras',
    'Scikit-learn', 'XGBoost', 'LightGBM', 'CatBoost',
    'OpenCV', 'NLTK', 'SpaCy', 'Hugging Face', 'LangChain',
    'LLM', 'RAG', 'Stable Diffusion', 'YOLO', 'MLflow',
    'Git', 'GitHub', 'GitLab', 'Bitbucket', 'Docker',
    'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'CI/CD',
    'AWS', 'Azure', 'Google Cloud', 'Linux',
    'Android', 'iOS', 'React Native', 'Flutter',
    'ROS', 'ROS2', 'Arduino', 'Raspberry Pi', 'STM32',
    'Embedded C', 'Agile', 'Scrum', 'Jira', 'Figma',
    'Selenium', 'PyTest', 'Postman', 'Penetration Testing',
    'Ethical Hacking', 'Network Security',
]

skill_aliases = {
    'python3': 'Python', 'py': 'Python',
    'cpp': 'C++', 'c plus plus': 'C++',
    'js': 'JavaScript', 'es6': 'JavaScript',
    'ts': 'TypeScript', 'golang': 'Go',
    'sklearn': 'Scikit-learn', 'scikit learn': 'Scikit-learn',
    'pytorch': 'PyTorch', 'torch': 'PyTorch',
    'tensorflow 2': 'TensorFlow', 'tf': 'TensorFlow',
    'k8s': 'Kubernetes', 'docker compose': 'Docker',
    'pyspark': 'Apache Spark', 'amazon web services': 'AWS',
    'gcp': 'Google Cloud', 'google cloud platform': 'Google Cloud',
    'microsoft azure': 'Azure', 'postgres': 'PostgreSQL',
    'mongo': 'MongoDB', 'reactjs': 'React', 'react.js': 'React',
    'nodejs': 'Node.js', 'node js': 'Node.js',
    'vue': 'Vue.js', 'vuejs': 'Vue.js',
    'nextjs': 'Next.js', 'next js': 'Next.js',
    'tailwind': 'Tailwind CSS', 'tailwindcss': 'Tailwind CSS',
    'restful api': 'REST API', 'rest apis': 'REST API',
    'ci cd': 'CI/CD', 'cicd': 'CI/CD',
    'continuous integration': 'CI/CD',
    'huggingface': 'Hugging Face', 'transformers': 'Hugging Face',
    'cv2': 'OpenCV', 'open cv': 'OpenCV',
    'ubuntu': 'Linux', 'unix': 'Linux',
    'version control': 'Git', 'git bash': 'Git',
    'agile methodology': 'Agile', 'scrum master': 'Scrum',
    'pentesting': 'Penetration Testing', 'pen testing': 'Penetration Testing',
}

SHORT_SKILLS       = {'c', 'r', 'go', 'ts', 'js', 'py', 'sh'}
NORMALIZED_TARGETS = {re.sub(r'\s+', ' ', s.lower().strip()): s for s in target_skills}
NORMALIZED_ALIASES = {re.sub(r'\s+', ' ', k.lower().strip()): v for k, v in skill_aliases.items()}
email_expression   = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
number_expression  = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

# Helper Functions
def normalize_skill(raw):
    return re.sub(r'\s+', ' ', raw.lower().strip())

def extract_skills(resume_text):
    found = set()
    text  = normalize_skill(resume_text)
    for norm, canonical in NORMALIZED_TARGETS.items():
        if norm in SHORT_SKILLS:
            if re.search(r'\b' + re.escape(norm) + r'\b', text):
                found.add(canonical)
        else:
            if norm in text:
                found.add(canonical)
    for norm_alias, canonical in NORMALIZED_ALIASES.items():
        if norm_alias in text:
            found.add(canonical)
    return sorted(found)

def extract_with_gemini(resume_text):
    fallback     = {"name": None, "education": [], "experience": []}
    trimmed_text = resume_text[:3000] if len(resume_text) > 3000 else resume_text
    prompt = f"""
You are an expert HR assistant that extracts structured information from resumes.
STRICT RULES:
1. Return ONLY a valid JSON object. No explanation, no markdown, no code fences.
2. If a field is not found, use null for strings or [] for lists.

Return ONLY this structure:
{{
  "name": "Full name or null",
  "education": [
    {{
      "degree"     : "Degree name or null",
      "institution": "College name or null",
      "year"       : "Year or duration or null",
      "grade"      : "CGPA or percentage or null"
    }}
  ],
  "experience": [
    {{
      "company"    : "Company name or null",
      "role"       : "Job title or null",
      "duration"   : "Duration or null",
      "description": "One line summary or null"
    }}
  ]
}}
RESUME TEXT:
{trimmed_text}
"""
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = json.loads(raw)
        return {
            "name"      : parsed.get("name"),
            "education" : parsed.get("education", []),
            "experience": parsed.get("experience", [])
        }
    except Exception as e:
        st.warning(f"⚠️ Gemini error: {e}")
        return fallback

def process_single_resume(uploaded_file):
    pdf_bytes   = uploaded_file.read()
    resume_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                resume_text += text + "\n"
    if not resume_text.strip():
        return None
    email_match = re.search(email_expression, resume_text)
    phone_match = re.search(number_expression, resume_text)
    gemini_data = extract_with_gemini(resume_text)
    return {
        "file"      : uploaded_file.name,
        "name"      : gemini_data.get("name"),
        "email"     : email_match.group() if email_match else None,
        "phone"     : phone_match.group() if phone_match else None,
        "skills"    : extract_skills(resume_text),
        "education" : gemini_data.get("education", []),
        "experience": gemini_data.get("experience", [])
    }

def build_flat_dataframe(all_results):
    flat_data = []
    for result in all_results:
        first_edu = result["education"][0] if result.get("education") else {}
        first_exp = result["experience"][0] if result.get("experience") else {}
        flat_data.append({
            "File"       : result.get("file"),
            "Name"       : result.get("name"),
            "Email"      : result.get("email"),
            "Phone"      : result.get("phone"),
            "Skills"     : ", ".join(result.get("skills") or []),
            "Degree"     : first_edu.get("degree"),
            "Institution": first_edu.get("institution"),
            "Year"       : first_edu.get("year"),
            "Grade"      : first_edu.get("grade"),
            "Company"    : first_exp.get("company"),
            "Role"       : first_exp.get("role"),
            "Duration"   : first_exp.get("duration"),
        })
    return pd.DataFrame(flat_data)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=72)
    st.title("Resume Parser")
    st.markdown("AI-powered resume analysis using **Gemini 2.5 Flash**")
    st.markdown("---")

    # File Uploader inside sidebar
    st.markdown("### 📂 Upload Resumes")
    uploaded_files = st.file_uploader(
        label="Drop PDF resumes here",
        type=["pdf"],
        accept_multiple_files=True,
        help="Only PDF format is supported",
        label_visibility="collapsed"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) ready")
        st.markdown("**Uploaded Files:**")
        for f in uploaded_files:
            size_kb = f.size / 1024
            st.markdown(f"- 📄 `{f.name}` ({size_kb:.1f} KB)")

    st.markdown("---")
    parse_clicked = st.button("🚀 Parse All Resumes", disabled=not uploaded_files)

    st.markdown("---")
    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    1. 📤 Upload PDF resumes
    2. 🤖 Gemini extracts name, education & experience
    3. 🔍 Skill matcher scans 175+ skills
    4. 📊 Analytics chart is generated
    5. ⬇️ Download results as JSON
    """)
    st.markdown("---")
    st.caption("Built with Streamlit + Gemini API")

# Main Content
st.title("📄 Resume Parser")
st.markdown("#### Extract skills, experience & education from your resumes instantly")
st.markdown("---")

# Default State
if not uploaded_files:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-number">175+</div>
            <div class="metric-label">Skills Tracked</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-number">300+</div>
            <div class="metric-label">Skill Aliases</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-number">AI</div>
            <div class="metric-label">Gemini 2.5 Flash</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Upload your PDF resumes from the sidebar to get started.")

# Parse & Display Results
if parse_clicked and uploaded_files:
    all_results = []

    # Spinner
    with st.spinner("🤖 AI is processing your resumes — please wait..."):
        progress_bar = st.progress(0, text="Starting...")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_single_resume, f): f for f in uploaded_files}
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                if result:
                    all_results.append(result)
                progress_bar.progress(
                    (i + 1) / len(uploaded_files),
                    text=f"⚙️ Parsed {i + 1} of {len(uploaded_files)} resume(s)..."
                )

        progress_bar.empty()

    st.success(f"✅ Successfully parsed {len(all_results)} resume(s)!")
    st.markdown("---")

    # Metric Cards
    all_skills_flat = []
    for r in all_results:
        all_skills_flat.extend(r.get("skills", []))

    total_skills    = len(all_skills_flat)
    unique_skills   = len(set(all_skills_flat))
    avg_skills      = round(total_skills / len(all_results), 1) if all_results else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(all_results)}</div>
            <div class="metric-label">Resumes Parsed</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_skills}</div>
            <div class="metric-label">Total Skills Found</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{unique_skills}</div>
            <div class="metric-label">Unique Skills</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{avg_skills}</div>
            <div class="metric-label">Avg Skills / Resume</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary Table + Download
    st.markdown('<div class="section-header">📋 Summary Table</div>', unsafe_allow_html=True)

    df = build_flat_dataframe(all_results)

    col1, col2 = st.columns([4, 1])
    with col2:
        st.download_button(
            label="⬇️ Download JSON File",
            data=json.dumps(all_results, indent=2),
            file_name="parsed_resumes.json",
            mime="application/json"
        )

    st.dataframe(df, use_container_width=True)
    st.markdown("---")

    # Individual Resume Details 
    st.markdown('<div class="section-header">🔍 Individual Resume Details</div>', unsafe_allow_html=True)

    for result in all_results:
        with st.expander(f"📄 {result['file']}  —  {result.get('name', 'Unknown')}"):

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**👤 Contact Info**")
                st.write(f"**Name:**  {result.get('name')  or 'N/A'}")
                st.write(f"**Email:** {result.get('email') or 'N/A'}")
                st.write(f"**Phone:** {result.get('phone') or 'N/A'}")

            with col2:
                st.markdown("**🛠️ Skills Detected**")
                skills = result.get("skills", [])
                if skills:
                    # Display as colored tags
                    tags_html = " ".join(
                        f'<span style="background:#e3f0fb;color:#1f77b4;'
                        f'padding:3px 10px;border-radius:12px;'
                        f'font-size:0.82rem;margin:2px;display:inline-block">{s}</span>'
                        for s in skills
                    )
                    st.markdown(tags_html, unsafe_allow_html=True)
                else:
                    st.write("No skills found.")

            st.markdown("<br>", unsafe_allow_html=True)

            col3, col4 = st.columns(2)
            with col3:
                st.markdown("**🎓 Education**")
                for edu in result.get("education", []):
                    st.markdown(
                        f"- **{edu.get('degree') or 'N/A'}** — "
                        f"{edu.get('institution') or 'N/A'} "
                        f"({edu.get('year') or 'N/A'}) "
                        f"| {edu.get('grade') or 'N/A'}"
                    )

            with col4:
                st.markdown("**💼 Experience**")
                for exp in result.get("experience", []):
                    st.markdown(
                        f"- **{exp.get('role') or 'N/A'}** at "
                        f"{exp.get('company') or 'N/A'} "
                        f"({exp.get('duration') or 'N/A'})"
                    )

    st.markdown("---")

    # Analytics Chart
    st.markdown('<div class="section-header">📊 Skills Analytics</div>', unsafe_allow_html=True)

    if all_skills_flat:
        skill_counts = Counter(all_skills_flat)
        top_skills   = skill_counts.most_common(15)

        skill_names  = [s[0] for s in top_skills]
        skill_values = [s[1] for s in top_skills]

        col1, col2 = st.columns([3, 1])

        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x=skill_values, y=skill_names, palette="Blues_r", ax=ax)
            ax.set_title(
                f"Top 15 Skills Across {len(all_results)} Resume(s)",
                fontsize=14, fontweight="bold", pad=15
            )
            ax.set_xlabel("Number of Resumes", fontsize=11)
            ax.set_ylabel("")
            for i, v in enumerate(skill_values):
                ax.text(v + 0.05, i, str(v), va="center", fontsize=10)
            ax.set_xlim(0, max(skill_values) + 1)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col2:
            st.markdown("**📋 Skill Counts**")
            skill_df = pd.DataFrame(
                skill_counts.most_common(),
                columns=["Skill", "Count"]
            )
            st.dataframe(skill_df, use_container_width=True, height=400)
    else:
        st.warning("No skills found to display.")
