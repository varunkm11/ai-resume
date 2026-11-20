from pathlib import Path
import json
import re

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import JOBS_FILE
from .parsers import extract_text
from .matcher import analyze_match
from .skills import extract_skills

app = FastAPI(
    title="FairMatch AI - Resume Screening & Job Recommendation",
    version="1.0.0",
    description="Explainable, semantic resume-to-job matching with human-in-the-loop screening."
)

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "frontend" / "static"


def load_jobs():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "FairMatch AI"}


@app.get("/api/jobs")
def jobs():
    return load_jobs()


@app.post("/api/analyze")
async def analyze(
    resume: UploadFile = File(...),
    job_id: str = Form(...),
):
    jobs_data = load_jobs()
    job = next((j for j in jobs_data if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    content = await resume.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume must be under 5 MB")

    try:
        text = extract_text(resume.filename or "resume.txt", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(text.strip()) < 80:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the resume.")

    result = analyze_match(
        resume_text=text,
        job_title=job["title"],
        job_description=job["description"],
        required_skills=job["skills"],
    )

    # Raw resume content is intentionally not returned or persisted.
    return {
        "candidate": resume.filename,
        "job": job,
        "analysis": result,
        "privacy": "Raw resume is processed in memory and is not persisted by this demo.",
    }


@app.post("/api/recommend")
async def recommend(resume: UploadFile = File(...)):
    jobs_data = load_jobs()
    content = await resume.read()

    try:
        text = extract_text(resume.filename or "resume.txt", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(text.strip()) < 80:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the resume.")

    results = []
    for job in jobs_data:
        analysis = analyze_match(
            resume_text=text,
            job_title=job["title"],
            job_description=job["description"],
            required_skills=job["skills"],
        )
        results.append({
            "job": job,
            "analysis": analysis,
        })

    results.sort(key=lambda x: x["analysis"]["score"], reverse=True)
    return {
        "candidate": resume.filename,
        "recommendations": results,
        "privacy": "Raw resume is processed in memory and is not persisted by this demo.",
    }


@app.post("/api/roadmap")
async def career_roadmap(
    resume: UploadFile = File(...),
    job_id: str = Form(...),
):
    """Build a practical, gap-led learning roadmap for the selected target role."""
    jobs_data = load_jobs()
    job = next((j for j in jobs_data if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    content = await resume.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume must be under 5 MB")
    try:
        text = extract_text(resume.filename or "resume.txt", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if len(text.strip()) < 80:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the resume.")

    result = analyze_match(text, job["title"], job["description"], job["skills"])
    gaps = result["missing_skills"]
    focus = gaps[:4] or result["matched_skills"][:3] or job["skills"][:3]
    role = job["title"]
    course_catalog = {
        "python": "Python for Everybody (University of Michigan)",
        "machine learning": "Machine Learning Specialization (DeepLearning.AI / Stanford Online)",
        "pandas": "Kaggle Learn: Pandas",
        "numpy": "NumPy official beginner tutorials",
        "scikit-learn": " scikit-learn MOOC (Inria) ",
        "sql": "SQLBolt interactive lessons",
        "git": "GitHub Skills: Introduction to GitHub",
        "rest api": "Postman API Fundamentals Student Expert",
        "power bi": "Microsoft Learn: Get started building with Power BI",
        "statistics": "Khan Academy: Statistics and probability",
        "excel": "Excel Skills for Business (Macquarie University)",
        "llm": "Hugging Face: LLM Course",
        "generative ai": "Microsoft Learn: Generative AI for Beginners",
        "rag": "DeepLearning.AI: Retrieval Augmented Generation (RAG)",
        "transformers": "Hugging Face: Transformers course",
        "fastapi": "FastAPI official tutorial",
        "javascript": "freeCodeCamp: JavaScript Algorithms and Data Structures",
        "react": "React official Learn course",
        "node.js": "The Odin Project: NodeJS path",
        "html": "MDN: Learn HTML",
        "css": "MDN: Learn CSS",
    }

    def skill_action(skill: str, phase: str) -> dict:
        if phase == "learn":
            course = course_catalog.get(skill.lower(), f"A beginner-to-intermediate course in {skill}")
            return {
                "title": f"Course: {course.strip()}",
                "kind": "Course",
                "detail": f"Use this learning path to close the {skill} gap. Prioritize core concepts and guided exercises; write short notes on what you learned.",
                "evidence": f"Finish the course modules and solve 3 practice exercises in {skill}.",
            }
        if phase == "practice":
            return {
                "title": f"Practise {skill} in realistic tasks",
                "kind": "Practice",
                "detail": f"Work through role-relevant exercises using {skill}. Explain your approach in a README and review the result against documentation or a peer review.",
                "evidence": f"Complete 5 exercises and document 2 lessons learned about {skill}.",
            }
        return {
            "title": f"Show {skill} in a portfolio project",
            "kind": "Project",
            "detail": f"Build and publish a small, end-to-end {role} project that uses {skill}. Include setup instructions, a concise design explanation, and a demo or screenshots.",
            "evidence": f"Publish a working project with a README, demo, and at least 3 measurable tests or examples.",
        }

    phases = [
        {
            "days": "1-30", "title": "Close the foundations gap", "theme": "Learn",
            "summary": "Choose a narrow skill focus, learn the essentials, and set a baseline you can improve.",
            "actions": [skill_action(s, "learn") for s in focus[:2]] + [
                {"title": "Set your starting baseline", "kind": "Milestone", "detail": f"Review 3 current job descriptions for {role}. Note repeated requirements and compare them with this analysis; pick one weekly study schedule you can sustain.", "evidence": "Save a one-page baseline and schedule 4 focused learning sessions per week."}
            ],
        },
        {
            "days": "31-60", "title": "Turn learning into practice", "theme": "Practise",
            "summary": "Apply the new concepts in small exercises and get feedback before building something larger.",
            "actions": [skill_action(s, "practice") for s in focus[:2]] + [
                {"title": "Get an outside review", "kind": "Milestone", "detail": "Ask a mentor, peer, or community to review one exercise or code sample. Use the feedback to revise it.", "evidence": "Record 3 pieces of feedback and show the updated work."}
            ],
        },
        {
            "days": "61-90", "title": "Build proof and target applications", "theme": "Demonstrate",
            "summary": "Ship one clear portfolio artifact and make your new capability easy for employers to verify.",
            "actions": [skill_action(s, "project") for s in focus[:2]] + [
                {"title": "Refresh your role narrative", "kind": "Milestone", "detail": f"Update your resume and portfolio to describe the project, your contribution, and its outcome. Tailor the summary to {role} openings.", "evidence": "Publish the project and prepare 2 concise examples for interviews."}
            ],
        },
    ]
    return {
        "candidate": resume.filename or "Resume",
        "job": job,
        "match_score": result["score"],
        "starting_point": "skill gaps" if gaps else "strengthen existing skills",
        "focus_skills": focus,
        "matched_skills": result["matched_skills"],
        "missing_skills": gaps,
        "phases": phases,
        "privacy": "Raw resume is processed in memory and is not persisted by this demo.",
    }


def _resume_lines(text: str) -> list[str]:
    """Return short, original resume lines suitable for evidence-backed suggestions."""
    lines = []
    for raw_line in re.split(r"[\r\n]+", text):
        line = re.sub(r"\s+", " ", raw_line).strip(" •\t-")
        if len(line) >= 24 and len(line) <= 500:
            lines.append(line)
        elif len(line) > 500:
            lines.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if 24 <= len(part.strip()) <= 500)
    return lines


def _rank_resume_evidence(lines: list[str], reference_text: str) -> list[dict]:
    stop_words = {"about", "after", "also", "and", "are", "been", "build", "built", "can", "for", "from", "have", "into", "its", "more", "our", "project", "role", "that", "the", "their", "then", "this", "through", "using", "with", "work", "your"}
    reference_words = {word for word in re.findall(r"[a-z][a-z0-9+#.]*", reference_text.lower()) if len(word) > 2 and word not in stop_words}
    scored = []
    for line in lines:
        words = {word for word in re.findall(r"[a-z][a-z0-9+#.]*", line.lower()) if len(word) > 2 and word not in stop_words}
        overlap = words & reference_words
        matched_skills = extract_skills(line)
        score = len(matched_skills) * 4 + len(overlap)
        if score:
            scored.append({"text": line, "matched_skills": matched_skills, "matched_terms": sorted(overlap)[:8], "_score": score})
    scored.sort(key=lambda item: item["_score"], reverse=True)
    return [{key: value for key, value in item.items() if key != "_score"} for item in scored[:8]]


async def _read_resume_upload(resume: UploadFile) -> tuple[str, str]:
    content = await resume.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume must be under 5 MB")
    try:
        text = extract_text(resume.filename or "resume.txt", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if len(text.strip()) < 80:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the resume.")
    return text, resume.filename or "Resume"


@app.post("/api/tailor")
async def tailor_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    target_role: str = Form("Target role"),
):
    """Suggest resume emphasis using only evidence that exists in the uploaded resume."""
    if len(job_description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Paste a fuller job description (at least 30 characters).")
    if len(job_description) > 12000:
        raise HTTPException(status_code=413, detail="Job description must be under 12,000 characters.")
    text, filename = await _read_resume_upload(resume)
    resume_skills = extract_skills(text)
    required_skills = extract_skills(job_description)
    matched = sorted(set(resume_skills) & set(required_skills))
    missing = sorted(set(required_skills) - set(resume_skills))
    evidence = _rank_resume_evidence(_resume_lines(text), job_description)
    suggestions = [
        {
            "skill": skill,
            "action": f"Bring forward the resume line that demonstrates {skill}.",
            "evidence": next((line for line in _resume_lines(text) if skill in extract_skills(line)), ""),
        }
        for skill in matched
    ]
    return {
        "candidate": filename,
        "target_role": target_role.strip() or "Target role",
        "matched_skills": matched,
        "not_found_skills": missing,
        "evidence": evidence,
        "suggestions": suggestions,
        "grounding_note": "Suggestions quote text from your resume. Skills marked not found were not detected; add them only if they accurately describe your experience.",
        "privacy": "Resume text is processed in memory and is not persisted by this demo.",
    }


@app.post("/api/interview/questions")
async def interview_questions(
    resume: UploadFile = File(...),
    job_id: str = Form(...),
):
    jobs_data = load_jobs()
    job = next((item for item in jobs_data if item["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    text, filename = await _read_resume_upload(resume)
    lines = _resume_lines(text)
    project_anchor = next((line for line in lines if re.search(r"\b(project|built|developed|created|implemented)\b", line, re.I)), "")
    resume_skills = extract_skills(text)
    matched_skills = [skill for skill in job["skills"] if skill in resume_skills]
    focus_skill = matched_skills[0] if matched_skills else job["skills"][0]
    project_name = "your project"
    if project_anchor:
        candidate_name = re.split(r"[,;|]", project_anchor)[0].strip()
        project_name = candidate_name[:90]

    questions = [
        {"id": "project-story", "type": "Resume project", "question": f"Walk me through {project_name}. What problem were you solving, what was your specific contribution, and what was the outcome?", "anchor": project_anchor or "No clearly labeled project line was found; choose a project from your resume."},
        {"id": "skill-example", "type": "Skill evidence", "question": f"Your resume lists {focus_skill}. Tell me about a time you used it: what did you do, and how did you know it worked?", "anchor": next((line for line in lines if focus_skill in extract_skills(line)), f"{focus_skill} is listed as a required role skill." )},
        {"id": "role-approach", "type": "Role scenario", "question": f"For a {job['title']} task involving {job['skills'][0]}, how would you break the work into steps and check the result?", "anchor": f"Target role: {job['title']}"},
        {"id": "tradeoff", "type": "Problem solving", "question": f"Describe a challenge from your experience that is relevant to {job['title']}. What options did you consider, and why did you choose your approach?", "anchor": project_anchor or f"Target role: {job['title']}"},
        {"id": "growth", "type": "Reflection", "question": f"Which skill from this role would you most like to improve next, and what is one practical step you would take?", "anchor": f"Role skills: {', '.join(job['skills'][:4])}"},
    ]
    return {"candidate": filename, "job": job, "questions": questions, "privacy": "Resume text is processed in memory and is not persisted by this demo."}


@app.post("/api/interview/feedback")
async def interview_feedback(
    question: str = Form(...),
    answer: str = Form(...),
    anchor: str = Form(""),
):
    """Return transparent structural practice prompts; this is not a factual answer grader."""
    answer = answer.strip()
    if len(answer) < 10:
        raise HTTPException(status_code=400, detail="Write a little more before asking for feedback.")
    if len(answer) > 8000:
        raise HTTPException(status_code=413, detail="Keep each practice answer under 8,000 characters.")
    words = re.findall(r"\b[\w+#.-]+\b", answer)
    sentences = [part for part in re.split(r"[.!?]+", answer) if part.strip()]
    contains_result = bool(re.search(r"\b(result|improved|reduced|increased|delivered|launched|learned|achieved|so that|which meant)\b|\d+\s*%", answer, re.I))
    contains_action = bool(re.search(r"\b(I|we)\s+(built|created|designed|tested|analyzed|fixed|led|implemented|worked|used|improved|learned|decided|wrote|developed)\b", answer, re.I))
    anchor_terms = [word for word in re.findall(r"[a-z][a-z0-9+#.-]*", anchor.lower()) if len(word) > 3]
    grounded = any(term in answer.lower() for term in anchor_terms[:10]) if anchor_terms else False
    notes = []
    notes.append("Your answer has a useful amount of detail." if len(words) >= 35 else "Add a little more detail: aim for a short situation, your action, and the outcome.")
    notes.append("You describe a concrete action you took." if contains_action else "Make your personal contribution clear. Use 'I' to distinguish your work from the team's.")
    notes.append("You mention an outcome or result." if contains_result else "Close with the result, what changed, or what you learned. Use a real measure if you have one.")
    notes.append("You connected your response to the resume or role context." if grounded else "Tie the answer to a specific project, skill, or example from your resume when relevant.")
    return {
        "question": question,
        "word_count": len(words),
        "structure": {"action_present": contains_action, "outcome_present": contains_result, "context_linked": grounded, "sentence_count": len(sentences)},
        "practice_notes": notes,
        "framework": "Try Situation → Task → Action → Result (STAR). Keep the example accurate and use only outcomes you can support.",
        "scope_note": "These notes check answer structure and specificity. They do not judge technical correctness or predict interview success.",
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")
