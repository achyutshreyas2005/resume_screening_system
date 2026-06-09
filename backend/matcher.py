"""
matcher.py
----------
Production-grade resume matching pipeline.

Weights:
  Skills Match          → 30%
  Experience Relevance  → 25%
  Projects/Achievements → 20%
  Semantic Similarity   → 10%
  Education             →  5%
  Certifications        →  5%
  Resume Quality        →  3%
  Extra Signals         →  2%
  Total                 100%

Status thresholds:
  Shortlisted → score >= 60%
  In Review   → score >= 40%
  Rejected    → score <  40%
"""

import re
from sentence_transformers import SentenceTransformer, CrossEncoder, util

# ── Load models ────────────────────────────────────────────────────────────────
print("Loading SBERT model...")
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
print("SBERT ready!")

cross_encoder = None
try:
    print("Loading Cross-Encoder model...")
    cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    print("Cross-Encoder ready!")
except Exception as e:
    print(f"Cross-Encoder not loaded: {e} — skipping reranking")


# ── Text cleaner ───────────────────────────────────────────────────────────────
def clean_for_matching(text):
    """Normalize text before SBERT encoding."""
    text = re.sub(r'([a-z])([A-Z])',   r'\1 \2', text)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r',([a-z])',          r', \1',  text)
    text = re.sub(r'\band([A-Za-z])',   r'and \1', text)
    text = re.sub(r'\busing([A-Z])',    r'using \1', text)
    text = re.sub(r'\bwith([A-Z])',     r'with \1', text)
    text = re.sub(r'\s+',               ' ',      text)
    return text.lower().strip()


# ── SBERT semantic similarity ──────────────────────────────────────────────────
def compute_sbert_scores(jd_text, resume_texts):
    """Encode JD and resumes into SBERT embeddings and compute cosine similarity."""
    jd_emb      = sbert_model.encode(jd_text,        convert_to_tensor=True)
    resume_embs = sbert_model.encode(resume_texts,   convert_to_tensor=True)
    scores      = util.cos_sim(jd_emb, resume_embs)[0]
    return [float(s) for s in scores]


# ── Factor 1: Skills Match (30%) ──────────────────────────────────────────────
def compute_skills_score(resume, jd_skills):
    """Percentage of JD skills found in resume."""
    if not jd_skills:
        return 0.5
    resume_lower = resume.get("full_text", "").lower()
    matched      = sum(1 for s in jd_skills if s in resume_lower)
    return float(matched / len(jd_skills))


# ── Factor 2: Experience Relevance (25%) ──────────────────────────────────────
def compute_experience_score(resume, jd_text):
    """Score based on work experience relevance to JD."""
    experience = resume.get("experience", "").lower()
    full_text  = resume.get("full_text",  "").lower()
    jd_lower   = jd_text.lower()

    # No experience section
    if not experience or experience == "not specified":
        exp_signals = ["intern", "worked", "employment", "company", "organization"]
        if not any(s in full_text for s in exp_signals):
            return 0.1
        return 0.3

    score = 0.4

    # Relevant job titles
    relevant_titles = [
        "engineer", "developer", "analyst", "manager", "consultant",
        "researcher", "designer", "architect", "scientist", "specialist",
        "intern", "associate", "executive", "officer", "lead", "head",
        "director", "coordinator", "technician", "advisor"
    ]
    if any(t in experience for t in relevant_titles):
        score += 0.2

    # JD keyword overlap with experience
    jd_words  = set(jd_lower.split())
    exp_words = set(experience.split())
    overlap   = len(jd_words & exp_words)
    score    += min(overlap / max(len(jd_words), 1) * 8, 0.3)

    # Years of experience bonus
    years = re.findall(r'(\d+)\s*(?:year|yr)', experience)
    if years:
        score += min(max(int(y) for y in years) * 0.02, 0.1)

    return float(min(score, 1.0))


# ── Factor 3: Projects & Achievements (20%) ───────────────────────────────────
def compute_projects_score(resume, jd_text):
    """Score based on project quality, relevance, and achievements."""
    projects  = resume.get("projects",  "").lower()
    full_text = resume.get("full_text", "").lower()
    jd_lower  = jd_text.lower()

    score = 0.0

    # Action verbs — shows hands-on work
    action_verbs = [
        "developed", "built", "created", "designed", "implemented",
        "deployed", "trained", "automated", "integrated", "optimized",
        "architected", "engineered", "launched", "published", "contributed",
        "achieved", "improved", "reduced", "increased", "delivered"
    ]
    verb_count = sum(1 for v in action_verbs if v in full_text)
    score     += min(verb_count * 0.05, 0.3)

    # Quantified achievements — %, x, +
    metrics = re.findall(r'\d+\s*%|\d+\s*x\b|\d+\+', full_text)
    score  += min(len(metrics) * 0.05, 0.2)

    # Project relevance to JD
    if projects:
        jd_words   = set(jd_lower.split())
        proj_words = set(projects.split())
        overlap    = len(jd_words & proj_words)
        score     += min(overlap / max(len(jd_words), 1) * 6, 0.3)

    # Competition / hackathon achievements
    competition_keywords = [
        "hackathon", "competition", "winner", "finalist", "runner",
        "award", "prize", "medal", "rank", "top", "best"
    ]
    if any(k in full_text for k in competition_keywords):
        score += 0.1

    return float(min(score, 1.0))


# ── Factor 4: Education (5%) ──────────────────────────────────────────────────
def compute_education_score(resume):
    """Score based on degree level."""
    text = (resume.get("education", "") + " " + resume.get("full_text", "")).lower()

    if any(w in text for w in ["phd", "doctorate", "ph.d"]):
        return 1.0
    elif any(w in text for w in ["m.tech", "mtech", "m.sc", "msc", "mba", "master", "m.e"]):
        return 0.9
    elif any(w in text for w in ["b.tech", "btech", "b.sc", "bsc", "bachelor", "b.e", "be"]):
        return 0.8
    elif any(w in text for w in ["diploma", "polytechnic"]):
        return 0.6
    elif any(w in text for w in ["university", "college", "institute"]):
        return 0.5
    return 0.3


# ── Factor 5: Certifications (5%) ─────────────────────────────────────────────
def compute_certifications_score(resume):
    """Score based on certifications and online courses."""
    full_text     = resume.get("full_text", "").lower()
    cert_keywords = [
        "certified", "certification", "certificate", "nptel", "coursera",
        "udemy", "edx", "linkedin learning", "google", "aws certified",
        "microsoft certified", "oracle", "comptia", "cisco",
        "hackerrank", "kaggle", "geeksforgeeks", "internshala"
    ]
    count = sum(1 for kw in cert_keywords if kw in full_text)
    return float(min(count * 0.25, 1.0))


# ── Factor 6: Resume Quality (3%) ─────────────────────────────────────────────
def compute_resume_quality_score(resume):
    """Score based on resume completeness and structure."""
    score = 0.0
    if resume.get("email"):                        score += 0.20
    if resume.get("phone"):                        score += 0.15
    if resume.get("education"):                    score += 0.15
    if resume.get("projects"):                     score += 0.15
    if resume.get("experience"):                   score += 0.15
    if len(resume.get("skills", [])) >= 5:         score += 0.10
    if len(resume.get("full_text", "")) > 500:     score += 0.10
    return float(min(score, 1.0))


# ── Factor 7: Extra Signals (2%) ──────────────────────────────────────────────
def compute_extra_signals_score(resume):
    """Score based on GitHub, LinkedIn, leadership, publications."""
    full_text = resume.get("full_text", "").lower()
    score     = 0.0

    if "github"      in full_text:                 score += 0.25
    if "linkedin"    in full_text:                 score += 0.15
    if "open source" in full_text:                 score += 0.20
    if any(w in full_text for w in [
        "captain", "president", "head", "lead",
        "founder", "convener", "organizer", "coordinator"
    ]):                                             score += 0.20
    if any(w in full_text for w in [
        "publication", "published", "paper",
        "research", "journal", "conference"
    ]):                                             score += 0.20

    return float(min(score, 1.0))


# ── Weighted score ─────────────────────────────────────────────────────────────
def compute_weighted_score(resume, jd_text, sbert_score, jd_skills):
    """Combine all 8 factors into one final score (0–100)."""
    final = (
        compute_skills_score(resume, jd_skills)      * 0.30 +
        compute_experience_score(resume, jd_text)    * 0.25 +
        compute_projects_score(resume, jd_text)      * 0.20 +
        float(sbert_score)                           * 0.10 +
        compute_education_score(resume)              * 0.05 +
        compute_certifications_score(resume)         * 0.05 +
        compute_resume_quality_score(resume)         * 0.03 +
        compute_extra_signals_score(resume)          * 0.02
    )
    return round(float(final) * 100, 2)


# ── Cross-Encoder re-ranking ───────────────────────────────────────────────────
def rerank_with_cross_encoder(jd_text, resumes, top_n=10):
    """Re-rank top N candidates using Cross-Encoder for higher accuracy."""
    if cross_encoder is None or len(resumes) <= 2:
        return resumes

    top  = resumes[:min(top_n, len(resumes))]
    rest = resumes[min(top_n, len(resumes)):]

    pairs  = [[jd_text, r.get("full_text", "")] for r in top]
    scores = [float(s) for s in cross_encoder.predict(pairs)]

    min_s = min(scores)
    max_s = max(scores)
    rng   = max_s - min_s if max_s != min_s else 1

    for i, resume in enumerate(top):
        ce_score = (scores[i] - min_s) / rng * 100
        resume["match_score"] = round(
            float(resume["match_score"]) * 0.75 + float(ce_score) * 0.25, 2
        )

    return sorted(top, key=lambda x: x["match_score"], reverse=True) + rest


# ── AI Explanation ─────────────────────────────────────────────────────────────
def generate_explanation(resume, jd_skills, score):
    """Generate a human-readable explanation of the match result."""
    name      = resume.get("name", "This candidate")
    full_text = resume.get("full_text", "").lower()
    found     = [s for s in jd_skills if s in full_text]
    missing   = [s for s in jd_skills if s not in full_text]
    parts     = []

    # Overall verdict
    if score >= 60:
        parts.append(f"{name} is a strong match with {score}% overall score.")
    elif score >= 40:
        parts.append(f"{name} is a moderate match with {score}% overall score.")
    else:
        parts.append(f"{name} is a partial match with {score}% overall score.")

    if found:
        parts.append(f"Matched skills: {', '.join(found[:6])}.")
    if missing:
        parts.append(f"Missing skills: {', '.join(missing[:4])}.")

    experience = resume.get("experience", "")
    if experience and experience != "Not specified":
        parts.append("Has relevant work/internship experience.")
    else:
        parts.append("No work experience — evaluated on projects and skills.")

    if resume.get("projects"):
        parts.append("Has demonstrated hands-on project experience.")

    cert_keywords = ["nptel", "coursera", "udemy", "certified", "certificate"]
    if any(k in full_text for k in cert_keywords):
        parts.append("Has relevant certifications or online courses.")

    if "github" in full_text:
        parts.append("Has GitHub profile — shows coding activity.")
    if any(w in full_text for w in ["hackathon", "winner", "award", "medal"]):
        parts.append("Has hackathon or competition achievements.")

    education = resume.get("education", "")
    if education and education != "Not specified":
        parts.append(f"Education: {education[:80]}.")

    if score >= 60:
        parts.append("Recommendation: Strong candidate — proceed to interview.")
    elif score >= 40:
        parts.append("Recommendation: Moderate fit — review manually.")
    else:
        parts.append("Recommendation: Weak match — consider other candidates.")

    return " ".join(parts)


# ── Main pipeline ──────────────────────────────────────────────────────────────
def match_resumes(job_description, resumes, jd_skills=None):
    """
    Full 8-factor matching pipeline:
    1. Clean texts
    2. SBERT semantic similarity
    3. Weighted scoring (8 factors)
    4. Cross-Encoder re-ranking
    5. AI explanation generation
    """
    if not resumes:
        return []

    jd_clean     = clean_for_matching(job_description)
    resume_texts = [clean_for_matching(r.get("full_text", "")) for r in resumes]

    print("Computing SBERT embeddings...")
    sbert_scores = compute_sbert_scores(jd_clean, resume_texts)

    print("Computing weighted scores...")
    for i, resume in enumerate(resumes):
        resume["match_score"] = compute_weighted_score(
            resume, job_description, sbert_scores[i], jd_skills or []
        )

    resumes = sorted(resumes, key=lambda x: x["match_score"], reverse=True)

    print("Re-ranking with Cross-Encoder...")
    resumes = rerank_with_cross_encoder(job_description, resumes)

    print("Generating AI explanations...")
    for resume in resumes:
        resume["explanation"] = generate_explanation(
            resume, jd_skills or [], float(resume["match_score"])
        )

    return resumes