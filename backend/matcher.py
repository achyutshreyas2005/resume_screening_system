"""
matcher.py
----------
General-purpose resume matching pipeline.
Works for ANY domain — tech, MBA, finance, healthcare, etc.

Weights:
  Semantic Similarity (SBERT) → 40%  ← main ranking signal
  Skills Match                → 25%  ← JD skills found in resume  
  Projects & Achievements     → 15%  ← hands-on work
  Experience Relevance        → 10%  ← relevant work history
  Education                   →  5%  ← degree level
  Certifications               →  3%  ← online courses/certs
  Resume Quality               →  2%  ← completeness

Status:
  Shortlisted → >= 60%
  In Review   → >= 40%
  Rejected    → <  40%
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
    text = re.sub(r'([a-z])([A-Z])',      r'\1 \2',   text)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2',   text)
    text = re.sub(r',([a-z])',             r', \1',    text)
    text = re.sub(r'\band([A-Za-z])',      r'and \1',  text)
    text = re.sub(r'\s+',                  ' ',        text)
    return text.lower().strip()


# ── Factor 1: Semantic Similarity (40%) ───────────────────────────────────────
def compute_sbert_scores(jd_text, resume_texts):
    """
    Core ranking signal.
    SBERT understands meaning — if JD says 'data engineering'
    and resume says 'ETL pipelines', it knows they match.
    Works for any domain without any hardcoded rules.
    """
    jd_emb      = sbert_model.encode(jd_text,      convert_to_tensor=True)
    resume_embs = sbert_model.encode(resume_texts, convert_to_tensor=True)
    scores      = util.cos_sim(jd_emb, resume_embs)[0]
    return [float(s) for s in scores]


# ── Factor 2: Skills Match (25%) ──────────────────────────────────────────────
def compute_skills_score(resume, jd_skills):
    """
    Percentage of JD skills found in resume.
    jd_skills comes from universal skills list matched against JD text.
    If no skills extracted from JD, falls back to SBERT score.
    """
    if not jd_skills:
        return 0.5
    resume_lower = resume.get("full_text", "").lower()
    matched      = sum(1 for s in jd_skills if s in resume_lower)
    return float(matched / len(jd_skills))


# ── Factor 3: Projects & Achievements (15%) ───────────────────────────────────
def compute_projects_score(resume):
    """
    Domain-agnostic project scoring.
    Rewards hands-on work, quantified results, and achievements.
    Works for tech projects, MBA case studies, research papers, etc.
    """
    full_text = resume.get("full_text", "").lower()
    score     = 0.0

    # Action verbs — universal signal of doing real work
    action_verbs = [
        "developed", "built", "created", "designed", "implemented",
        "deployed", "trained", "automated", "integrated", "optimized",
        "launched", "published", "contributed", "achieved", "improved",
        "reduced", "increased", "delivered", "led", "managed",
        "analyzed", "researched", "evaluated", "executed", "established"
    ]
    verb_count = sum(1 for v in action_verbs if v in full_text)
    score     += min(verb_count * 0.04, 0.4)

    # Quantified achievements — numbers show real impact
    metrics = re.findall(r'\d+\s*%|\d+\s*x\b|\d+\+|\$[\d,]+', full_text)
    score  += min(len(metrics) * 0.06, 0.3)

    # Competition / recognition signals
    achievement_keywords = [
        "award", "winner", "finalist", "runner", "prize",
        "medal", "scholarship", "honor", "merit", "rank",
        "hackathon", "competition", "recognition", "certified"
    ]
    if any(k in full_text for k in achievement_keywords):
        score += 0.15

    # Has a projects section
    if resume.get("projects") and len(resume.get("projects", "")) > 50:
        score += 0.15

    return float(min(score, 1.0))


# ── Factor 4: Experience Relevance (10%) ──────────────────────────────────────
def compute_experience_score(resume, jd_text):
    """
    General experience scoring — rewards overlap between
    experience text and JD text using word intersection.
    No domain-specific hardcoding.
    """
    experience = resume.get("experience", "").lower()
    full_text  = resume.get("full_text",  "").lower()
    jd_lower   = jd_text.lower()

    # No experience found anywhere
    if not experience or experience == "not specified":
        exp_signals = ["intern", "worked", "employment", "experience", "company"]
        if not any(s in full_text for s in exp_signals):
            return 0.1
        return 0.3

    # Base score for having experience
    score = 0.3

    # Measure JD-experience word overlap
    # Use longer words only to avoid noise
    jd_words  = set(w for w in jd_lower.split() if len(w) > 4)
    exp_words = set(w for w in experience.split() if len(w) > 4)
    if jd_words:
        overlap = len(jd_words & exp_words)
        score  += min(overlap / len(jd_words) * 8, 0.5)

    # Bonus for internship (freshers)
    if any(w in experience for w in ["intern", "internship"]):
        score += 0.1

    # Bonus for full-time experience
    if any(w in experience for w in ["engineer", "analyst", "developer",
                                      "manager", "consultant", "researcher"]):
        score += 0.1

    return float(min(score, 1.0))


# ── Factor 5: Education (5%) ──────────────────────────────────────────────────
def compute_education_score(resume):
    """Score based on degree level — domain agnostic."""
    text = (
        resume.get("education",  "") + " " +
        resume.get("full_text",  "")
    ).lower()

    if any(w in text for w in ["phd", "ph.d", "doctorate"]):
        return 1.0
    elif any(w in text for w in ["m.tech", "mtech", "m.sc", "msc",
                                   "mba", "master", "m.e", "pg"]):
        return 0.9
    elif any(w in text for w in ["b.tech", "btech", "b.sc", "bsc",
                                   "bachelor", "b.e", "be", "b.com"]):
        return 0.8
    elif any(w in text for w in ["diploma", "polytechnic"]):
        return 0.6
    elif any(w in text for w in ["university", "college", "institute"]):
        return 0.5
    return 0.3


# ── Factor 6: Certifications (3%) ─────────────────────────────────────────────
def compute_certifications_score(resume):
    """Score based on certifications — rewards continuous learning."""
    full_text     = resume.get("full_text", "").lower()
    cert_keywords = [
        "certified", "certification", "certificate", "nptel",
        "coursera", "udemy", "edx", "linkedin learning",
        "google", "aws certified", "microsoft certified",
        "oracle", "comptia", "cisco", "hackerrank",
        "kaggle", "geeksforgeeks", "internshala"
    ]
    count = sum(1 for kw in cert_keywords if kw in full_text)
    return float(min(count * 0.25, 1.0))


# ── Factor 7: Resume Quality (2%) ─────────────────────────────────────────────
def compute_resume_quality_score(resume):
    """Score based on resume completeness."""
    score = 0.0
    if resume.get("email"):                            score += 0.25
    if resume.get("phone"):                            score += 0.20
    if resume.get("education"):                        score += 0.20
    if resume.get("projects"):                         score += 0.20
    if len(resume.get("full_text", "")) > 300:         score += 0.15
    return float(min(score, 1.0))


# ── Final weighted score ───────────────────────────────────────────────────────
def compute_weighted_score(resume, jd_text, sbert_score, jd_skills):
    """
    Combine all factors. SBERT carries the most weight (40%)
    so domain-specific ranking is handled automatically.
    """
    final = (
        float(sbert_score)                        * 0.40 +
        compute_skills_score(resume, jd_skills)   * 0.25 +
        compute_projects_score(resume)            * 0.15 +
        compute_experience_score(resume, jd_text) * 0.10 +
        compute_education_score(resume)           * 0.05 +
        compute_certifications_score(resume)      * 0.03 +
        compute_resume_quality_score(resume)      * 0.02
    )
    return round(float(final) * 100, 2)


# ── Cross-Encoder re-ranking ───────────────────────────────────────────────────
def rerank_with_cross_encoder(jd_text, resumes, top_n=10):
    """Re-rank top N candidates using Cross-Encoder."""
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
        # 70% weighted score + 30% cross-encoder
        resume["match_score"] = round(
            float(resume["match_score"]) * 0.70 +
            float(ce_score)             * 0.30, 2
        )

    return sorted(top, key=lambda x: x["match_score"], reverse=True) + rest


# ── AI Explanation ─────────────────────────────────────────────────────────────
def generate_explanation(resume, jd_skills, score):
    """Generate a human-readable explanation of the match result."""
    name      = resume.get("name",      "This candidate")
    full_text = resume.get("full_text", "").lower()
    found     = [s for s in jd_skills if s in full_text]
    missing   = [s for s in jd_skills if s not in full_text]
    parts     = []

    # Overall verdict
    if score >= 60:
        parts.append(
            f"{name} is a strong match with {score}% overall score."
        )
    elif score >= 40:
        parts.append(
            f"{name} is a moderate match with {score}% overall score."
        )
    else:
        parts.append(
            f"{name} is a partial match with {score}% overall score."
        )

    # Skills
    if found:
        parts.append(f"Matched skills: {', '.join(found[:6])}.")
    if missing:
        parts.append(f"Missing skills: {', '.join(missing[:4])}.")

    # Experience
    experience = resume.get("experience", "")
    if experience and experience != "Not specified":
        parts.append("Has relevant work or internship experience.")
    else:
        parts.append("No work experience — evaluated on projects and skills.")

    # Projects
    if resume.get("projects"):
        parts.append("Has hands-on project experience.")

    # Certifications
    cert_keywords = ["nptel", "coursera", "udemy", "certified", "certificate"]
    if any(k in full_text for k in cert_keywords):
        parts.append("Has relevant certifications or online courses.")

    # Extra signals
    if "github" in full_text:
        parts.append("Has GitHub profile.")
    if any(w in full_text for w in ["hackathon", "winner", "award", "medal"]):
        parts.append("Has competition or hackathon achievements.")

    # Education
    education = resume.get("education", "")
    if education and education != "Not specified":
        parts.append(f"Education: {education[:80]}.")

    # Recommendation
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
    Full matching pipeline — works for any domain.
    1. SBERT semantic similarity (main signal)
    2. Weighted scoring (7 factors)
    3. Cross-Encoder re-ranking
    4. AI explanation
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
