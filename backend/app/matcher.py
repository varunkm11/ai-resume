from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .config import MODEL_NAME, SEMANTIC_WEIGHT, SKILL_WEIGHT, PROFILE_WEIGHT
from .skills import extract_skills, skill_coverage


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)


def semantic_score(resume_text: str, job_text: str) -> float:
    model = get_model()
    embeddings = model.encode([resume_text, job_text], normalize_embeddings=True)
    sim = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return round(max(0.0, min(1.0, sim)) * 100, 1)


def profile_score(resume_text: str) -> float:
    t = resume_text.lower()
    score = 0
    # Lightweight, explainable signals; deliberately not used for protected traits.
    if any(x in t for x in ["b.tech", "btech", "b.e.", "bachelor", "master", "m.tech", "mtech"]):
        score += 50
    if any(x in t for x in ["experience", "internship", "work experience", "employment"]):
        score += 50
    return float(score)


def analyze_match(resume_text: str, job_title: str, job_description: str, required_skills: list[str]) -> dict:
    candidate_skills = extract_skills(resume_text)
    matched, missing, skill_score = skill_coverage(candidate_skills, required_skills)

    job_text = f"{job_title}\n{job_description}\nRequired skills: {', '.join(required_skills)}"
    sem = semantic_score(resume_text, job_text)
    prof = profile_score(resume_text)

    final = (
        SEMANTIC_WEIGHT * sem
        + SKILL_WEIGHT * skill_score
        + PROFILE_WEIGHT * prof
    )
    final = round(final, 1)

    if final >= 80:
        decision = "Strong match"
    elif final >= 65:
        decision = "Good match"
    elif final >= 50:
        decision = "Partial match"
    else:
        decision = "Low match"

    explanation = []
    if matched:
        explanation.append(f"Matched {len(matched)} of {len(required_skills)} required skills.")
    if missing:
        explanation.append("Main gaps: " + ", ".join(missing[:6]) + ".")
    explanation.append(f"Semantic resume-to-job similarity is {sem:.1f}%.")
    explanation.append("Score is advisory; a human recruiter should make the final decision.")

    return {
        "score": final,
        "decision": decision,
        "semantic_score": sem,
        "skill_score": skill_score,
        "profile_score": prof,
        "candidate_skills": candidate_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": explanation,
    }
