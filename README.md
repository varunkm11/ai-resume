# FairMatch AI
## Intelligent Resume Screening and Job Recommendation System

This is a runnable research prototype based on the uploaded research paper's proposed unified pipeline:
resume parsing → feature representation → semantic matching → ranking → explainability → job recommendation.

### What this project solves
Traditional keyword ATS can miss candidates who describe the same capability using different wording. FairMatch combines:
1. PDF/DOCX/TXT resume parsing
2. Skill extraction from a configurable skill taxonomy
3. Transformer sentence embeddings (`all-MiniLM-L6-v2`)
4. Cosine semantic similarity between resume and job description
5. Explicit required-skill coverage
6. Explainable score breakdown and skill gaps
7. Content-based job recommendation
8. Human-in-the-loop warning instead of automatic rejection
9. Raw resume is processed in memory and not persisted by this demo

### Tech stack
- Python + FastAPI
- Sentence Transformers
- scikit-learn
- pypdf + python-docx
- HTML/CSS/JavaScript frontend
- JSON job store

### Run in VS Code

#### 1) Open the folder
Open `resume_ai_project` in VS Code.

#### 2) Create virtual environment
Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use Command Prompt:
```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
```

#### 3) Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4) Start the server
```bash
uvicorn backend.app.main:app --reload
```

#### 5) Open
Go to:
http://127.0.0.1:8000

The first analysis downloads the Sentence Transformer model. Keep the terminal open.

### How to test
1. Upload a real PDF/DOCX resume.
2. Select Machine Learning Engineer Intern.
3. Click Analyze Resume.
4. Review semantic score, skill coverage, matched skills and missing skills.
5. Click Recommend Jobs to rank the demo job catalogue.

### Add your own jobs
Edit:
`data/jobs.json`

Each job needs:
- id
- title
- company
- location
- skills
- description

### Make the research version stronger
The current prototype is a real baseline. For a publishable experimental system, add:
- labelled resume-job relevance dataset
- BERT/DeBERTa fine-tuning
- NDCG@K, Precision@K, Recall@K and mAP
- fairness evaluation
- multilingual resume support
- PostgreSQL for controlled storage
- authentication/RBAC
- audit logs
- recruiter feedback loop
- OCR for scanned resumes
- calibrated thresholds and cross-validation

### Important research/ethics note
Do not use gender, race, religion, age, disability, photo, marital status or other protected/sensitive attributes as ranking features. AI output should support, not replace, human hiring decisions.
