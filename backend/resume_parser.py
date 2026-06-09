"""
parser.py
---------
Extracts structured information from resume PDFs.
Works for ANY domain — tech, MBA, finance, healthcare, etc.
Skills are extracted dynamically from JD and matched against resumes.
"""

import pdfplumber
import spacy
import re
import os
import docx

nlp = spacy.load("en_core_web_sm")

BLACKLIST_NAMES = [
    "dart", "java", "python", "swift", "go", "rust",
    "ruby", "c", "c++", "c#", "sql", "html", "css", "r"
]

STOPWORDS = {
    "the", "and", "for", "with", "our", "you", "are", "will", "have",
    "this", "that", "from", "your", "we", "be", "to", "of", "in", "a",
    "an", "is", "it", "as", "at", "by", "on", "or", "if", "us", "can",
    "all", "any", "but", "not", "was", "has", "been", "they", "their",
    "which", "who", "how", "what", "when", "where", "while", "about",
    "also", "both", "each", "more", "most", "other", "some", "such",
    "than", "then", "there", "these", "those", "through", "during",
    "strong", "good", "great", "high", "new", "key", "well", "experience",
    "ability", "skills", "knowledge", "work", "team", "role", "job",
    "candidate", "looking", "seeking", "required", "preferred", "must",
    "minimum", "years", "including", "etc", "like", "using", "use",
    "based", "related", "relevant", "across", "within", "between",
    "provide", "support", "ensure", "manage", "develop", "build",
    "create", "design", "implement", "maintain", "improve", "drive",
    "please", "apply", "position", "company", "opportunity", "join",
    "help", "need", "want", "make", "take", "given", "per", "get"
}


def extract_text(file_path):
    """
    Extract text from PDF, DOCX, or TXT files.
    Auto-detects format from file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # ── PDF ───────────────────────────────────────────────────────────────────
    if ext == ".pdf":
        full_text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
        except Exception as e:
            print(f"  PDF read error: {e}")
        return full_text.strip()

    # ── DOCX (Word) ───────────────────────────────────────────────────────────
    elif ext == ".docx":
        full_text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text += para.text + "\n"

            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            full_text += cell.text + "\n"

        except Exception as e:
            print(f"  DOCX read error: {e}")

        return full_text.strip()

    # ── TXT ───────────────────────────────────────────────────────────────────
    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()

        except Exception as e:
            print(f"  TXT read error: {e}")
            return ""

    # ── Unsupported ───────────────────────────────────────────────────────────
    else:
        print(f"  Unsupported file type: {ext}")
        return ""


def clean_text(text):
    """Fix squished words, remove junk characters, normalize whitespace."""
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r',([a-z])', r', \1', text)
    text = re.sub(r'\band([A-Za-z])', r'and \1', text)
    text = re.sub(r'\bthe([A-Z])', r'the \1', text)
    text = re.sub(r'\bof([A-Z])', r'of \1', text)
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s@.\-+,/]', ' ', text)
    return text.strip()


def extract_skills_from_text(text):
    """
    Dynamically extract skills and keywords from any text.
    Works for ANY domain — tech, MBA, healthcare, finance, etc.
    No hardcoded list needed.
    """

    doc = nlp(text.lower())
    skills = set()

    # Extract noun chunks
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        words = phrase.split()

        if 1 <= len(words) <= 3:
            if not all(w in STOPWORDS for w in words):
                if len(phrase) > 2:
                    skills.add(phrase)

    # Extract important nouns
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and token.text not in STOPWORDS:
            if len(token.text) > 2:
                skills.add(token.text)

    return list(skills)


def match_skills(resume_text, jd_skills):
    """
    Match JD skills against resume text.
    Returns found skills and missing skills.
    """

    resume_lower = resume_text.lower()
    found = []
    missing = []

    for skill in jd_skills:
        if skill.lower() in resume_lower:
            found.append(skill)
        else:
            missing.append(skill)

    return found, missing


def extract_contact_info(raw_text, cleaned_text):
    """Extract name, email, and phone number from resume text."""

    doc = nlp(raw_text)
    name = ""

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    if not name or name.lower() in BLACKLIST_NAMES:
        name = raw_text.strip().split('\n')[0].strip()

    email = re.findall(r'[\w.\-]+@[\w.\-]+\.\w+', cleaned_text)
    phone = re.findall(r'[\+\d][\d\s\-]{8,15}\d', cleaned_text)

    return {
        "name": name,
        "email": email[0] if email else "",
        "phone": phone[0].strip() if phone else ""
    }


def extract_sections(raw_text):
    """Detect and extract Education, Experience, and Projects sections."""

    sections = {
        "experience": "",
        "education": "",
        "projects": ""
    }

    current = None

    for line in raw_text.split('\n'):

        l = line.lower().strip()

        if any(w in l for w in ["experience", "work history", "employment", "internship"]):
            current = "experience"

        elif any(w in l for w in ["education", "qualification", "academic"]):
            current = "education"

        elif any(w in l for w in ["project", "projects"]):
            current = "projects"

        elif current:
            line = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)
            line = re.sub(r'\(cid:\d+\)', '', line)
            sections[current] += line.strip() + " "

    for key in sections:
        sections[key] = sections[key].strip()[:400]

    return sections


def parse_resume(file_path):
    """
    Main function — takes any file path (PDF/DOCX/TXT),
    returns a structured dictionary.
    """

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    # ── Extract text based on file type ───────────────────────────────────────
    raw = extract_text(file_path)

    if not raw:
        return {"error": "No text extracted — file may be corrupted or image-based"}

    cleaned = clean_text(raw)
    contact = extract_contact_info(raw, cleaned)

    # FIXED HERE
    skills = extract_skills_from_text(cleaned)

    sections = extract_sections(raw)

    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "skills": skills,
        "experience": sections["experience"],
        "education": sections["education"],
        "projects": sections["projects"],
        "full_text": cleaned
    }