import re

# A practical starter taxonomy. Extend this file for a specific company's roles.
SKILL_ALIASES = {
    "python": ["python", "python3"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "git": ["git", "github", "gitlab"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "nlp": ["natural language processing", "nlp"],
    "computer vision": ["computer vision", "opencv"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch", "torch"],
    "transformers": ["transformers", "hugging face", "huggingface"],
    "bert": ["bert"],
    "llm": ["large language model", "llm", "llms"],
    "generative ai": ["generative ai", "genai", "gen ai"],
    "rag": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "data analysis": ["data analysis", "data analytics"],
    "statistics": ["statistics", "statistical analysis"],
    "rest api": ["rest api", "restful api", "rest apis"],
    "postman": ["postman"],
    "solidity": ["solidity"],
    "blockchain": ["blockchain", "web3"],
    "c": ["c programming", " c "],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "excel": ["excel", "microsoft excel"],
    "communication": ["communication", "communication skills"],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_skills(text: str) -> list[str]:
    t = normalize(text)
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            # Word boundaries where possible; aliases with symbols use a safe substring check.
            if alias.strip() in {"c++", "c"}:
                pattern = re.escape(alias.strip())
                if re.search(rf"(?<!\w){pattern}(?!\w)", t):
                    found.append(canonical)
                    break
            elif re.search(rf"(?<!\w){re.escape(alias.lower())}(?!\w)", t):
                found.append(canonical)
                break
    return sorted(set(found))


def skill_coverage(candidate_skills: list[str], required_skills: list[str]):
    c = set(candidate_skills)
    r = set(required_skills)
    matched = sorted(c & r)
    missing = sorted(r - c)
    score = (len(matched) / len(r) * 100) if r else 100.0
    return matched, missing, round(score, 1)
