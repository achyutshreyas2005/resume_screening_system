"""
main.py
-------
FastAPI backend for the Resume Screening System.

Endpoints:
  POST /register            → create HR account
  POST /login               → login, returns JWT token
  GET  /me                  → get logged in user info
  GET  /                    → health check
  GET  /candidates          → get last screened candidates
  POST /parse               → parse a single resume file
  POST /screen-with-jd-file → upload JD + resumes, returns ranked candidates

Supports: PDF, DOCX, TXT
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from resume_parser import parse_resume, extract_skills, clean_text, match_skills, extract_text
from matcher import match_resumes
from auth import hash_password, verify_password, create_token, decode_token
from database import get_user, create_user
from jd_parser import parse_jd
import shutil
import os

app = FastAPI(title="Resume Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme      = OAuth2PasswordBearer(tokenUrl="login")
last_results       = []
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ── Pydantic models ────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:     str
    email:    str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


# ── Helpers ────────────────────────────────────────────────────────────────────
def is_allowed_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def format_candidate(candidate, rank, jd_skills):
    score = float(candidate.get("match_score", 0))

    if score >= 60:
        status = "Shortlisted"
    elif score >= 40:
        status = "In Review"
    else:
        status = "Rejected"

    found, missing = match_skills(candidate.get("full_text", ""), jd_skills)

    return {
        "id":            rank,
        "rank":          rank,
        "name":          candidate.get("name", ""),
        "email":         candidate.get("email", ""),
        "phone":         candidate.get("phone", ""),
        "score":         round(score, 2),
        "skills":        found,
        "missingSkills": missing[:8],
        "experience":    candidate.get("experience", "") or "Not specified",
        "education":     candidate.get("education", "") or "Not specified",
        "projects":      candidate.get("projects", "") or "Not specified",
        "status":        status,
        "summary":       candidate.get("explanation", ""),
        "filename":      candidate.get("filename", ""),
        "role":          "",
        "company":       "",
    }


# ── Route 1: Health check ──────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Resume Screener API is running ✅"}


# ── Route 2: Register ──────────────────────────────────────────────────────────
@app.post("/register")
def register(req: RegisterRequest):
    if get_user(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(req.password)
    user   = create_user(req.name, req.email, hashed)
    token  = create_token({"sub": req.email})
    return {
        "token": token,
        "user":  {"name": user["name"], "email": user["email"], "role": user["role"]}
    }


# ── Route 3: Login ─────────────────────────────────────────────────────────────
@app.post("/login")
def login(req: LoginRequest):
    user = get_user(req.email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token({"sub": req.email})
    return {
        "token": token,
        "user":  {"name": user["name"], "email": user["email"], "role": user["role"]}
    }


# ── Route 4: Current user ──────────────────────────────────────────────────────
@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "name":  current_user["name"],
        "email": current_user["email"],
        "role":  current_user["role"]
    }


# ── Route 5: Get candidates ────────────────────────────────────────────────────
@app.get("/candidates")
def get_candidates(current_user: dict = Depends(get_current_user)):
    return last_results


# ── Route 6: Parse single resume ──────────────────────────────────────────────
@app.post("/parse")
async def parse(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, DOCX, TXT")

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        result = parse_resume(temp_path)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ── Route 7: Screen resumes against JD ────────────────────────────────────────
@app.post("/screen-with-jd-file")
async def screen_with_jd_file(
    jd_file: UploadFile = File(...),
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    global last_results

    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one resume")

    if not is_allowed_file(jd_file.filename):
        raise HTTPException(status_code=400, detail="JD must be PDF, DOCX, or TXT")

    resumes    = []
    temp_files = []

    try:
        # ── Save and parse JD ──────────────────────────────────────────────────
        jd_temp = f"temp_jd_{jd_file.filename}"
        temp_files.append(jd_temp)

        with open(jd_temp, "wb") as f:
            shutil.copyfileobj(jd_file.file, f)

        jd_result = parse_jd(jd_temp)

        if "error" in jd_result:
            raise HTTPException(status_code=400, detail=jd_result["error"])

        job_description = jd_result["focused_text"]
        jd_skills       = extract_skills(job_description)

        print(f"JD preview: {job_description[:200]}")
        print(f"JD skills: {jd_skills}")

        # ── Parse each resume ──────────────────────────────────────────────────
        for file in files:
            if not is_allowed_file(file.filename):
                print(f"  Skipping {file.filename} — unsupported format")
                continue

            temp_path = f"temp_{file.filename}"
            temp_files.append(temp_path)

            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            result = parse_resume(temp_path)

            if "error" in result:
                print(f"  Skipping {file.filename}: {result['error']}")
                continue

            result["filename"] = file.filename
            resumes.append(result)

    finally:
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not resumes:
        raise HTTPException(status_code=400, detail="No valid resumes could be parsed")

    # ── Match + rank ───────────────────────────────────────────────────────────
    ranked    = match_resumes(job_description, resumes, jd_skills=jd_skills)
    formatted = [format_candidate(c, i + 1, jd_skills) for i, c in enumerate(ranked)]

    last_results = formatted

    return {
        "job_description_preview": job_description[:300],
        "jd_skills":               jd_skills,
        "ranked_candidates":       formatted
    }