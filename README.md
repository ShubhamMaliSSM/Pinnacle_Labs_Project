# AI-Powered Resume Parser 📄

An AI-powered resume parsing web app built with **Streamlit** and **Google's Gemini API**. Upload multiple PDF resumes and instantly get structured data — contact info, education, experience, and skill matching — plus visual analytics across the whole batch.

Built as part of my AI/ML internship at **Pinnacle Labs**.

---

## 🖼️ Screenshots

**1. Home screen / upload interface**
![Home Screen](screenshots/home.png)
📌 *Capture: The sidebar with the file uploader, and the 3 stat cards (175+ Skills Tracked, 300+ Skill Aliases, Gemini 2.5 Flash) on the main screen before any resumes are uploaded.*

**2. Parsing in progress**
![Parsing](screenshots/parsing.png)
📌 *Capture: The progress bar / spinner while resumes are being parsed ("Parsed X of Y resumes...").*

**3. Summary metrics + table**
![Summary Table](screenshots/summary.png)
📌 *Capture: The 4 metric cards (Resumes Parsed, Total Skills Found, Unique Skills, Avg Skills/Resume) and the summary data table below it.*

**4. Individual resume detail view**
![Resume Detail](screenshots/detail.png)
📌 *Capture: One expanded resume card showing contact info, skill tags, education, and experience sections.*

**5. Skills analytics chart**
![Skills Analytics](screenshots/analytics.png)
📌 *Capture: The horizontal bar chart showing "Top 15 Skills Across N Resumes" with the skill counts table beside it.*

---

## 🚀 Features

- **Bulk PDF parsing** — upload and process multiple resumes at once, in parallel (via `ThreadPoolExecutor`)
- **AI-powered extraction** — Gemini API extracts name, education, and work experience into structured JSON
- **Skill matching engine** — matches resume text against a curated list of 175+ skills, with a 300+ entry alias dictionary so variants like "JS," "sklearn," or "k8s" are correctly normalized
- **Contact info extraction** — regex-based email and phone number detection
- **Resume quality metrics** — per-batch stats like total skills found, unique skills, and average skills per resume
- **Interactive analytics** — Seaborn/Matplotlib bar chart of the top 15 most common skills across all parsed resumes
- **Export results** — download all parsed data as a single JSON file
- **Clean, responsive UI** — custom-styled Streamlit interface with metric cards, skill tags, and expandable resume details

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| App/UI | Streamlit |
| AI Extraction | Google Gemini API (`gemini-2.5-flash`) |
| PDF Parsing | pdfplumber |
| Data Handling | Pandas |
| Visualization | Matplotlib, Seaborn |
| Concurrency | ThreadPoolExecutor (parallel resume processing) |
| Pattern Matching | Python `re` (regex for email/phone/skill extraction) |

## 📦 Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ShubhamMaliSSM/Pinnacle_Labs_Project.git
   cd Pinnacle_Labs_Project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your Gemini API key.** Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

5. Open the local URL Streamlit prints (usually `http://localhost:8501`) and upload PDF resumes from the sidebar.

## 🎯 How It Works

1. Upload one or more PDF resumes from the sidebar
2. Text is extracted from each PDF using `pdfplumber`
3. The extracted text is sent to Gemini, which returns structured JSON (name, education, experience)
4. A local regex/alias-matching engine independently scans the text for known skills — this runs without relying on the AI, so skill detection stays fast and consistent
5. Regex also pulls out email and phone number directly from the raw text
6. All resumes are processed in parallel using a thread pool, with a live progress bar
7. Results are shown as a searchable summary table, expandable per-resume cards, and an aggregate skills chart
8. Everything can be exported as a single JSON file

## 🔮 Future Improvements

- Add DOCX/TXT support alongside PDF
- Resume-to-job-description matching/ranking
- Persist results to a database instead of in-session only
- Export to CSV/Excel in addition to JSON

## 📄 License

*(Add one if you'd like — MIT is a common default for portfolio projects)*

---

Built by [Shubham Mali](https://github.com/ShubhamMaliSSM)