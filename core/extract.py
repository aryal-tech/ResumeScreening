import re
from pypdf import PdfReader
from io import BytesIO

def extract_text(file_bytes):
    """Extract text from PDF file bytes."""
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def extract_exact_section(text, section_name):
    """Extract exact section content by heading using regex."""
    pattern = rf"(?i){re.escape(section_name)}\s*(.*?)(?=\n[A-Z][^\n]*\n|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return section_name + '\n' + match.group(1).strip()
    return ""

def boost_resume_sections(text):
    """Boost skills and experience sections for similarity scoring."""
    skills = extract_exact_section(text, "skills")
    experience = extract_exact_section(text, "experience")
    boosted_text = text + " " + (skills * 2) + " " + (experience * 2)
    return boosted_text

def extract_email(text):
    """Extract the first email address found in the text."""
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ""

def extract_linkedin(text):
    """
    Extract a LinkedIn URL if present.
    Accepts forms like:
      - https://www.linkedin.com/in/username
      - linkedin.com/in/username
    """
    pattern = r"(https?://(?:www\.)?linkedin\.com/[^\s]+|(?:www\.)?linkedin\.com/[^\s]+)"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(1) if m else ""

def extract_phone(text):
    """
    Extract a plausible phone number (first match).
    Strategy: find sequences with 10+ digits, allowing spaces, dashes, parentheses, plus sign.
    """
    # Normalize some unicode dashes
    t = text.replace("–", "-").replace("—", "-")
    # Broad match; we'll post-filter for at least 10 digits total
    pattern = r"(\+?\d[\d\s().-]{7,}\d)"
    for m in re.finditer(pattern, t):
        candidate = m.group(1)
        digits = re.sub(r"\D", "", candidate)
        if len(digits) >= 10:
            return candidate.strip()
    return ""
