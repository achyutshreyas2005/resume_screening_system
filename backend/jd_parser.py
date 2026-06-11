"""
jd_parser.py
------------
Dedicated Job Description parser.

Extracts clean, relevant text from JD files for better matching.
Handles PDF, DOCX, TXT.

Strategy:
1. Extract all text
2. Find important sections
3. Remove company boilerplate
4. Return focused JD text for matching
"""

import re
import os

from resume_parser import (
    extract_skills,
    clean_text,
    extract_text
)

# ──────────────────────────────────────────────────────────────────────────────
# Boilerplate phrases to remove
# ──────────────────────────────────────────────────────────────────────────────
BOILERPLATE_PATTERNS = [
    r'copyright.*?\d{4}',
    r'all rights reserved',
    r'stay connected',
    r'follow us',
    r'click the link',
    r'learn more',
    r'beyond possible',
    r'we are growing',
    r'great place to work',
    r'certified',
    r'partner of the year',
    r'forrester wave',
    r'series [a-z] funding',
    r'inc\.\s*5000',
    r'compensation.*?lpa',
    r'ctc will be',
    r'inr\s*[\d.]+\s*lpa',
    r'page \d+ of \d+',
    r'\d+\s*/\s*\d+',
    r'©.*?\d{4}',
    r'www\.[^\s]+',
    r'http[s]?://[^\s]+',
]

# ──────────────────────────────────────────────────────────────────────────────
# Important sections
# ──────────────────────────────────────────────────────────────────────────────
IMPORTANT_SECTIONS = [
    "roles",
    "responsibilities",
    "required",
    "requirements",
    "qualification",
    "skills",
    "experience",
    "about the role",
    "what you'll do",
    "what we're looking for",
    "job description",
    "key responsibilities",
    "must have",
    "good to have",
    "technical skills",
    "interest areas",
    "profile summary",
    "job summary",
    "position overview",
    "duties",
]

# ──────────────────────────────────────────────────────────────────────────────
# Sections to skip
# ──────────────────────────────────────────────────────────────────────────────
SKIP_SECTIONS = [
    "about us",
    "about the company",
    "why join",
    "our culture",
    "benefits",
    "perks",
    "compensation",
    "salary",
    "stay connected",
    "recognition",
    "awards",
    "certified",
    "copyright",
    "locations",
    "our location",
    "follow us",
    "contact",
    "references",
    "equal opportunity",
    "diversity",
    "disclaimer",
]


# ──────────────────────────────────────────────────────────────────────────────
# Remove boilerplate
# ──────────────────────────────────────────────────────────────────────────────
def remove_boilerplate(text):
    """
    Remove branding, footer text, legal noise.
    """

    text_lower = text.lower()

    for pattern in BOILERPLATE_PATTERNS:
        text_lower = re.sub(pattern, '', text_lower)

    lines = text_lower.split('\n')

    # Remove tiny junk lines
    lines = [
        l.strip()
        for l in lines
        if len(l.strip()) > 15
    ]

    return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Extract important JD sections
# ──────────────────────────────────────────────────────────────────────────────
def extract_important_sections(text):
    """
    Extract only useful JD sections.
    """

    lines = text.lower().split('\n')

    result = []

    current_section_important = False
    current_section_skip = False

    for line in lines:

        line = line.strip()

        if not line:
            continue

        is_important = any(
            s in line
            for s in IMPORTANT_SECTIONS
        )

        is_skip = any(
            s in line
            for s in SKIP_SECTIONS
        )

        # Start important section
        if is_important:

            current_section_important = True
            current_section_skip = False

            result.append(line)

        # Skip section
        elif is_skip:

            current_section_important = False
            current_section_skip = True

        # Append section content
        elif current_section_important and not current_section_skip:

            result.append(line)

    return '\n'.join(result)


# ──────────────────────────────────────────────────────────────────────────────
# Extract JD keywords
# ──────────────────────────────────────────────────────────────────────────────
def extract_jd_keywords(text):
    """
    Extract keywords from JD.
    """

    NOISE_WORDS = {
        "the", "and", "for", "with", "our", "you", "are", "will",
        "have", "this", "that", "from", "your", "we", "be", "to",
        "of", "in", "a", "an", "is", "it", "as", "at", "by", "on",
        "or", "if", "us", "can", "all", "any", "but", "not", "was",
        "has", "been", "they", "their", "which", "who", "how", "what",
        "when", "where", "while", "about", "also", "both", "each",
        "more", "most", "other", "some", "such", "than", "then",
        "there", "these", "those", "through", "during", "strong",
        "good", "great", "high", "new", "key", "well", "work",
        "team", "role", "job", "candidate", "looking", "seeking",
        "required", "preferred", "must", "minimum", "years",
        "including", "etc", "like", "using", "use", "based",
        "related", "across", "within", "provide", "support",
        "ensure", "develop", "build", "create", "design",
        "implement", "maintain", "improve", "drive", "please",
        "apply", "position", "company", "opportunity", "join",
        "help", "need", "want", "make", "take", "given", "per",
        "get", "able", "should", "would", "could", "may", "might"
    }

    words = text.lower().split()

    keywords = [
        w for w in words
        if len(w) > 3
        and w not in NOISE_WORDS
        and not w.isdigit()
    ]

    # Remove duplicates
    seen = set()
    unique = []

    for word in keywords:

        if word not in seen:

            seen.add(word)
            unique.append(word)

    return unique[:100]


# ──────────────────────────────────────────────────────────────────────────────
# Main JD parser
# ──────────────────────────────────────────────────────────────────────────────
def parse_jd(file_path):
    """
    Parse JD file and return structured data.
    """

    if not os.path.exists(file_path):

        return {
            "error": f"File not found: {file_path}"
        }

    # ── Extract text ─────────────────────────────────────────────────────────
    raw_text = extract_text(file_path)

    if not raw_text or len(raw_text.strip()) < 50:

        return {
            "error": (
                "Could not extract text from JD — "
                "may be image-based or corrupted"
            )
        }

    # ── Remove boilerplate ───────────────────────────────────────────────────
    cleaned = remove_boilerplate(raw_text)

    # ── Extract focused sections ─────────────────────────────────────────────
    focused = extract_important_sections(raw_text)

    # ── Fallback if focused extraction weak ─────────────────────────────────
    if len(focused.strip()) < 100:

        print(
            "Warning: section extraction weak, "
            "using full JD text"
        )

        focused = cleaned

    # ── Final clean ──────────────────────────────────────────────────────────
    cleaned_text = clean_text(cleaned)

    focused_text = clean_text(focused)

    # ── Extract skills from focused JD ──────────────────────────────────────
    skills = extract_skills(
        focused_text or cleaned_text
    )

    # ── Extract keywords ────────────────────────────────────────────────────
    keywords = extract_jd_keywords(
        focused_text or cleaned_text
    )

    print(
        f"JD parsed: {len(cleaned_text)} chars, "
        f"{len(keywords)} keywords"
    )

    print(f"Top keywords: {keywords[:10]}")

    return {
        "raw_text": raw_text,
        "clean_text": cleaned_text,
        "focused_text": focused_text or cleaned_text,
        "skills": skills,
        "keywords": keywords,
        "word_count": len(cleaned_text.split())
    }