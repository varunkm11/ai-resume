from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

MODEL_NAME = "all-MiniLM-L6-v2"

# Weighted score: semantic fit + explicit skill coverage + experience/education signals.
SEMANTIC_WEIGHT = 0.55
SKILL_WEIGHT = 0.35
PROFILE_WEIGHT = 0.10
