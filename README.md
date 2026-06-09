# 🤖 AI Resume Screening System

An intelligent, full-stack resume screening system that automates candidate shortlisting using NLP and Machine Learning. Upload a Job Description and multiple resumes — the system ranks candidates by relevance using a production-grade 8-factor scoring pipeline.

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| Frontend | `https://resume-screener-frontend.onrender.com` |
| Backend API | `https://resume-screener-api.onrender.com` |
| API Docs | `https://resume-screener-api.onrender.com/docs` |

---

## ✨ Features

- 🔐 JWT-based HR login and registration
- 📄 Upload JD and resumes as PDF, DOCX, or TXT
- 🧠 8-factor weighted scoring pipeline
- 🤖 Sentence-BERT semantic similarity matching
- 🔁 Cross-Encoder re-ranking for higher accuracy
- 📊 Analytics dashboard with charts
- 💡 AI-generated explanation for each candidate
- 🎯 Works for any domain — tech, MBA, finance, healthcare, etc.

---

## 🏗️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| FastAPI | REST API framework |
| Sentence-BERT (`all-MiniLM-L6-v2`) | Semantic resume matching |
| Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) | Re-ranking pipeline |
| spaCy (`en_core_web_sm`) | NLP and entity extraction |
| pdfplumber | PDF text extraction |
| python-docx | Word document extraction |
| bcrypt + python-jose | Password hashing and JWT auth |
| FastAPI CORS Middleware | Frontend-backend communication |

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Tailwind CSS | Styling |
| React Router | Page navigation |
| Axios | API calls |
| Recharts | Analytics charts |
| Framer Motion | Animations |

---

## 🧠 Matching Pipeline

```
PDF / DOCX / TXT Resume
         ↓
   Text Extraction
         ↓
  Section Parsing
  (Education, Experience, Projects)
         ↓
   Skill Extraction
   (Universal 200+ skills list)
         ↓
  SBERT Embeddings
  (Semantic understanding)
         ↓
  8-Factor Weighted Scoring
         ↓
  Cross-Encoder Re-ranking
         ↓
  AI Explanation Generation
         ↓
  Ranked Candidate List
```

---

## ⚖️ Scoring Weights

| Factor | Weight | Description |
|---|---|---|
| Skills Match | **30%** | JD skills found in resume |
| Experience Relevance | **25%** | Work experience match with JD |
| Projects & Achievements | **20%** | Hands-on work, metrics, hackathons |
| Semantic Similarity | **10%** | BERT understands meaning not just keywords |
| Education | **5%** | Degree level and relevance |
| Certifications | **5%** | NPTEL, Coursera, AWS, etc. |
| Resume Quality | **3%** | Completeness — email, phone, sections |
| Extra Signals | **2%** | GitHub, LinkedIn, leadership, publications |

### Status Thresholds
| Status | Score |
|---|---|
| ✅ Shortlisted | 60% and above |
| 🔍 In Review | 40% – 59% |
| ❌ Rejected | Below 40% |

---

## 📡 API Endpoints

| Method | Endpoint | Auth |
|---|---|---|
| GET | `/` | Health check |
| POST | `/register` | Create HR account |
| POST | `/login` | Login, returns JWT token |
| GET | `/me` |  Get current user info |
| GET | `/candidates` | Get last screened candidates |
| POST | `/parse` | Parse a single resume file |
| POST | `/screen-with-jd-file` | Screen resumes against JD |

### `/screen-with-jd-file` Request

```
POST /screen-with-jd-file
Content-Type: multipart/form-data

jd_file  → File (PDF / DOCX / TXT)  — Job Description
files    → File[] (PDF / DOCX / TXT) — One or more resumes
```

### Response Format

```json
{
  "job_description_preview": "We are looking for a Python developer...",
  "ranked_candidates": [
    {
      "id": 1,
      "rank": 1,
      "name": "Soumya Prasad",
      "email": "prasadsoumya05@gmail.com",
      "phone": "+91-8467022084",
      "score": 72.4,
      "status": "Shortlisted",
      "skills": ["python", "machine learning", "react"],
      "missingSkills": ["docker", "aws"],
      "experience": "Full Stack Developer Intern at BHU...",
      "education": "B.Tech CSE, Manipal University Jaipur",
      "projects": "AI Resume Screening System...",
      "summary": "Soumya Prasad is a strong match with 72.4% overall score...",
      "filename": "soumya_resume.pdf"
    }
  ]
}
```

---

## 📁 Project Structure

```
resume-screening-system/
├── backend/
│   ├── main.py              ← FastAPI app, all endpoints
│   ├── resume_parser.py     ← PDF/DOCX/TXT text extraction
│   ├── matcher.py           ← 8-factor scoring pipeline
│   ├── auth.py              ← JWT + bcrypt authentication
│   ├── database.py          ← JSON-based user storage
│   ├── requirements.txt     ← Python dependencies
│   └── render.yaml          ← Render deployment config
│
├── frontend/
│   ├── public/
│   │   └── _redirects       ← React Router fix for Render
│   └── src/
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   └── Navbar.jsx
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   ├── Dashboard.jsx
│       │   ├── ResumeScreening.jsx
│       │   ├── Results.jsx
│       │   └── Analytics.jsx
│       ├── services/
│       │   └── api.js       ← All API calls
│       ├── App.jsx          ← Routing + protected routes
│       └── index.js
│
├── render.yaml              ← Full-stack deployment config
└── README.md
```

---

## 🚀 Run Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/resume-screening-system.git
cd resume-screening-system/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start backend
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd resume-screening-system/frontend

# Install dependencies
npm install

# Start frontend
npm start
```

Frontend runs at: `http://localhost:3000`

---

## 📦 Supported File Formats

| Format | Extension | Parser |
|---|---|---|
| PDF | `.pdf` | pdfplumber |
| Word Document | `.docx` | python-docx |
| Plain Text | `.txt` | built-in |

---

## 🔒 Security Notes

- Passwords are hashed using bcrypt — never stored as plain text
- JWT tokens expire after 8 hours
- `users.json` is excluded from Git via `.gitignore`
- CORS is configured to allow frontend origin only in production

---

## 📄 License

MIT License — free to use, modify, and distribute.
